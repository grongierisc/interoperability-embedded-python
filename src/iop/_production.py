from __future__ import annotations

import json
import os
import importlib
from contextlib import contextmanager
from dataclasses import dataclass, field
from dataclasses import is_dataclass
from functools import wraps
from typing import Any, Optional

from pydantic import BaseModel

from ._settings import Category, Setting, controls
from ._director_protocol import DirectorProtocol as _DirectorProtocol


def _bool_text(value: bool | str) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    normalized = str(value).lower().strip()
    if normalized in ("1", "yes", "on"):
        return "true"
    if normalized in ("0", "no", "off"):
        return "false"
    return normalized


def _text_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return _bool_text(value)
    return str(value)


def _auto_proxy_class_name(component_class: type) -> str:
    return (
        f"Python.{component_class.__module__}.{component_class.__name__}".replace(
            "_", ""
        )
    )


def _adapter_type_from_component_class(component_class: Optional[type]) -> str:
    if component_class is None:
        return ""
    for method_name in ("get_adapter_type", "getAdapterType"):
        method = getattr(component_class, method_name, None)
        if not callable(method):
            continue
        value = method()
        if value:
            return str(value)
    return ""


def _adapter_type_from_class_name(class_name: Optional[str]) -> str:
    if not class_name or not class_name.startswith("Python."):
        return ""
    python_name = class_name.removeprefix("Python.")
    module_name, separator, class_attr = python_name.rpartition(".")
    if not separator:
        return ""
    try:
        module = importlib.import_module(module_name)
        component_class = getattr(module, class_attr)
    except Exception:
        return ""
    if not isinstance(component_class, type):
        return ""
    return _adapter_type_from_component_class(component_class)


class TargetSetting(Setting):
    """Production target setting descriptor created by target()."""

    def __init__(self, logical_name: str = "", **kwargs: Any):
        kwargs.setdefault("iris_type", "Ens.DataType.ConfigName")
        kwargs.setdefault("category", Category.BASIC)
        kwargs.setdefault("control", controls.production_item())
        super().__init__("", **kwargs)
        self.logical_name = logical_name


def target(logical_name: str = "", **kwargs: Any) -> TargetSetting:
    """Declare an outbound target port on a component class."""
    return TargetSetting(logical_name, **kwargs)


@dataclass
class Port:
    """Bound reference to a component target setting inside a Production."""

    production: "Production"
    component: "ComponentRef"
    name: str
    logical_name: str = ""

    @property
    def item_name(self) -> str:
        return self.component.name

    @property
    def path(self) -> str:
        return f"{self.item_name}.{self.name}"

    def resolve(self) -> str:
        return self.production.resolve_port(self)

    def __str__(self) -> str:
        return self.path


@dataclass(frozen=True)
class GraphNode:
    name: str
    class_name: str
    kind: str = "component"
    enabled: bool | str = True
    category: str = ""
    adapter_class_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "class_name": self.class_name,
            "kind": self.kind,
            "enabled": self.enabled,
            "category": self.category,
        }
        if self.adapter_class_name:
            data["adapter_class_name"] = self.adapter_class_name
        return data


@dataclass(frozen=True)
class GraphEdge:
    """Possible communication route between two production items.

    An IRIS production topology can be modeled as a directed multigraph of
    possible communication routes. A graph edge is not an execution dependency
    and does not imply DAG semantics.
    """

    source_item: str
    target: str
    source_port: str = ""
    logical_name: str = ""
    origin: str = "authored"
    interaction: str = "request"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        origin = self.origin or "authored"
        if origin not in {"authored", "runtime", "inferred"}:
            raise ValueError(f"Unsupported GraphEdge origin: {origin!r}")
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "interaction", self.interaction or "unknown")
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @property
    def runtime(self) -> bool:
        return self.origin == "runtime"

    @property
    def inferred(self) -> bool:
        return self.origin == "inferred"

    @property
    def source(self) -> str:
        if self.source_port:
            return f"{self.source_item}.{self.source_port}"
        return self.source_item

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source": self.source,
            "source_item": self.source_item,
            "source_port": self.source_port,
            "logical_name": self.logical_name,
            "target": self.target,
            "origin": self.origin,
            "interaction": self.interaction,
        }
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        if self.runtime:
            data["runtime"] = True
        if self.inferred:
            data["inferred"] = True
        return data


@dataclass(frozen=True)
class ProductionGraph:
    production_name: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "production": self.production_name,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
        }
        if self.warnings:
            data["warnings"] = list(self.warnings)
        return data

    def to_text(self) -> str:
        outgoing: dict[str, list[GraphEdge]] = {node.name: [] for node in self.nodes}
        node_names = set(outgoing)
        for edge in self.edges:
            outgoing.setdefault(edge.source_item, []).append(edge)

        lines = [self.production_name]
        for node in self.nodes:
            label = f" [{node.class_name}]" if node.class_name else ""
            lines.append(f"  {node.name}{label}")
            for edge in sorted(
                outgoing.get(node.name, ()),
                key=lambda item: (item.source_port, item.target),
            ):
                source_port = edge.source_port or "(runtime)"
                suffix = "" if edge.target in node_names else " (unresolved)"
                labels = []
                if edge.origin != "authored":
                    labels.append(edge.origin)
                if edge.interaction not in ("", "request"):
                    labels.append(edge.interaction)
                label = f" [{', '.join(labels)}]" if labels else ""
                lines.append(f"    {source_port} -> {edge.target}{suffix}{label}")
        if self.warnings:
            lines.append("  warnings:")
            lines.extend(f"    {warning}" for warning in self.warnings)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_text()


@dataclass(frozen=True)
class ProductionDiffEntry:
    """One deterministic desired-vs-current production difference."""

    action: str
    kind: str
    path: str
    before: Any = None
    after: Any = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "action": self.action,
            "kind": self.kind,
            "path": self.path,
        }
        if self.before is not None:
            data["before"] = self.before
        if self.after is not None:
            data["after"] = self.after
        if self.detail:
            data["detail"] = self.detail
        return data

    def to_text(self) -> str:
        line = f"{self.action} {self.kind} {self.path}"
        if self.detail:
            return f"{line}: {self.detail}"
        if self.action == "change":
            return f"{line}: {_diff_value_text(self.before)} -> {_diff_value_text(self.after)}"
        if self.action == "add":
            return f"{line}: {_diff_value_text(self.after)}"
        if self.action == "remove":
            return f"{line}: {_diff_value_text(self.before)}"
        return line


@dataclass(frozen=True)
class ProductionDiff:
    """Directional diff from current runtime/imported state to desired Python state."""

    production_name: str
    changes: tuple[ProductionDiffEntry, ...]
    warnings: tuple[str, ...] = ()

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "production": self.production_name,
            "has_changes": self.has_changes,
            "changes": [change.to_dict() for change in self.changes],
        }
        if self.warnings:
            data["warnings"] = list(self.warnings)
        return data

    def to_text(self) -> str:
        lines = [f"Production diff: {self.production_name}"]
        if self.changes:
            lines.extend(f"  {change.to_text()}" for change in self.changes)
        else:
            lines.append("  no changes")
        if self.warnings:
            lines.append("  warnings:")
            lines.extend(f"    {warning}" for warning in self.warnings)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_text()


@dataclass
class ComponentRef:
    """Reference to a component item declared inside a Production."""

    production: "Production"
    name: str
    component_class: Optional[type] = None
    class_name: Optional[str] = None
    adapter_class: Optional[type] = None
    adapter_class_name: str = ""
    kind: str = "component"
    category: str = ""
    pool_size: int | str = 1
    enabled: bool | str = True
    foreground: bool | str = False
    comment: str = ""
    log_trace_events: bool | str = False
    schedule: str = ""
    host_settings: dict[str, Any] = field(default_factory=dict)
    adapter_settings: dict[str, Any] = field(default_factory=dict)
    other_settings: list[dict[str, Any]] = field(default_factory=list)
    port_names: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        if self.class_name is None:
            if self.component_class is None:
                raise ValueError("component_class or class_name is required")
            self.class_name = _auto_proxy_class_name(self.component_class)
        if self.adapter_class is not None and not self.adapter_class_name:
            self.adapter_class_name = _auto_proxy_class_name(self.adapter_class)
        if not self.adapter_class_name:
            self.adapter_class_name = _adapter_type_from_component_class(
                self.component_class
            )
        if not self.adapter_class_name:
            self.adapter_class_name = _adapter_type_from_class_name(self.class_name)

    def __getattr__(self, name: str) -> Port:
        if self.component_class is not None:
            descriptor = getattr(self.component_class, name, None)
            if isinstance(descriptor, TargetSetting):
                return Port(
                    production=self.production,
                    component=self,
                    name=name,
                    logical_name=descriptor.logical_name,
                )
        if name in self.port_names:
            return self.port(name)
        raise AttributeError(name)

    def port(self, name: str, logical_name: str = "") -> Port:
        self.port_names.add(name)
        return Port(
            production=self.production,
            component=self,
            name=name,
            logical_name=logical_name,
        )

    def set_host_setting(self, name: str, value: Any) -> None:
        self.host_settings[name] = value

    def inspect(self, *, refresh: bool = True) -> dict[str, Any]:
        return self.production.inspect_component(self, refresh=refresh)

    def start(self) -> None:
        self.production.start_component(self)

    def stop(self) -> None:
        self.production.stop_component(self)

    def restart(self) -> None:
        self.production.restart_component(self)

    def test(
        self,
        message: Any = None,
        *,
        classname: Optional[str] = None,
        body: str | dict | None = None,
    ) -> Any:
        return self.production.test_component(
            self,
            message=message,
            classname=classname,
            body=body,
        )

    def to_dict(self) -> dict[str, Any]:
        item: dict[str, Any] = {
            "@Name": self.name,
            "@Category": self.category,
            "@ClassName": self.class_name,
            "@PoolSize": _text_value(self.pool_size),
            "@Enabled": _bool_text(self.enabled),
            "@Foreground": _bool_text(self.foreground),
            "@Comment": self.comment,
            "@LogTraceEvents": _bool_text(self.log_trace_events),
            "@Schedule": self.schedule,
        }

        settings = []
        settings.extend(_settings_to_iris("Host", self.host_settings))
        settings.extend(_settings_to_iris("Adapter", self.adapter_settings))
        settings.extend(dict(setting) for setting in self.other_settings)
        if settings:
            item["Setting"] = settings

        return item


def _settings_to_iris(target_name: str, values: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "@Target": target_name,
            "@Name": name,
            "#text": _text_value(value),
        }
        for name, value in values.items()
    ]


def _apply_settings_update(target: dict[str, Any], updates: Any) -> None:
    """Merge *updates* into *target*, treating ``None`` values as removals."""
    for key, value in (updates or {}).items():
        if value is None:
            target.pop(key, None)
        else:
            target[key] = value


class Production:
    """Python authoring DSL for IRIS interoperability production topology.

    Python Production is the source of truth for Python-authored topology.
    IRIS remains the runtime source of truth. Imported graphs are operational
    reconstructions until metadata persistence makes round-trip fidelity possible.
    """

    def __init__(
        self,
        name: str,
        *,
        testing_enabled: bool | str = False,
        log_general_trace_events: bool | str = False,
        actor_pool_size: int | str = 2,
        description: str = "",
        namespace: Optional[str] = None,
        director: Optional["_DirectorProtocol"] = None,
    ):
        self.name = name
        self.testing_enabled = testing_enabled
        self.log_general_trace_events = log_general_trace_events
        self.actor_pool_size = actor_pool_size
        self.description = description
        self.namespace = namespace
        self._director = director
        self._items: list[ComponentRef] = []
        self._items_by_name: dict[str, ComponentRef] = {}
        self._connections: dict[tuple[str, str], list[str]] = {}
        self._edges: list[GraphEdge] = []
        self._graph_warnings: list[str] = []
        self._queue_info: dict[str, dict[str, Any]] = {}

    @classmethod
    def from_iris(
        cls,
        name: str,
        *,
        namespace: Optional[str] = None,
        director: Any = None,
    ) -> "Production":
        seed = cls(name, namespace=namespace, director=director)
        runtime_director = _ProductionRuntime(seed).director
        exported = runtime_director.export_production(name)
        connections = None
        try:
            connections = runtime_director.export_production_connections(name)
        except AttributeError:
            connections = None
        except Exception as exc:
            connections = {"warnings": [f"Could not export runtime connections: {exc}"]}
        if connections is not None and not isinstance(connections, (dict, list)):
            connections = None

        return cls.from_dict(
            exported,
            connections=connections,
            namespace=namespace,
            director=director,
        )

    @classmethod
    def from_dict(
        cls,
        data: dict[str, Any],
        *,
        connections: Any = None,
        queue_info: Any = None,
        namespace: Optional[str] = None,
        director: Any = None,
    ) -> "Production":
        production_name, production_data = _production_payload(data)
        production = cls(
            production_name,
            testing_enabled=production_data.get("@TestingEnabled", False),
            log_general_trace_events=production_data.get(
                "@LogGeneralTraceEvents", False
            ),
            actor_pool_size=production_data.get("ActorPoolSize", 2),
            description=production_data.get("Description", ""),
            namespace=namespace,
            director=director,
        )

        for item_data in _as_list(production_data.get("Item", [])):
            if not isinstance(item_data, dict):
                continue
            host_settings, adapter_settings, other_settings = _split_settings(
                item_data.get("Setting", [])
            )
            ref = ComponentRef(
                production=production,
                name=item_data.get("@Name", ""),
                class_name=item_data.get("@ClassName", ""),
                adapter_class_name=(
                    item_data.get("@AdapterClassName")
                    or item_data.get("@Adapter")
                    or ""
                ),
                kind="component",
                category=item_data.get("@Category", ""),
                pool_size=item_data.get("@PoolSize", 1),
                enabled=item_data.get("@Enabled", True),
                foreground=item_data.get("@Foreground", False),
                comment=item_data.get("@Comment", ""),
                log_trace_events=item_data.get("@LogTraceEvents", False),
                schedule=item_data.get("@Schedule", ""),
                host_settings=host_settings,
                adapter_settings=adapter_settings,
                other_settings=other_settings,
            )
            production._add_item(ref)

        queue_map, queue_warnings = _normalize_queue_info(queue_info)
        production._graph_warnings.extend(queue_warnings)
        for item_name, info in queue_map.items():
            if item_name not in production._items_by_name:
                production._graph_warnings.append(
                    f"Queue info item does not exist: {item_name}"
                )
                continue
            normalized = dict(info)
            production._queue_info[item_name] = normalized

        runtime_item_metadata = _normalize_runtime_item_metadata(connections)
        for item_name, metadata in runtime_item_metadata.items():
            ref = production._items_by_name.get(item_name)
            if ref is None:
                continue
            adapter_class_name = metadata.get("adapter_class_name", "")
            if adapter_class_name and not ref.adapter_class_name:
                ref.adapter_class_name = adapter_class_name

        connection_map, runtime_sources, warnings = _normalize_connections(
            connections
        )
        production._graph_warnings.extend(warnings)
        runtime_sources_with_targets = {
            source_item
            for source_item, targets in connection_map.items()
            if targets
        }

        for source_item, targets in connection_map.items():
            if source_item not in production._items_by_name:
                production._graph_warnings.append(
                    f"Runtime connection source does not exist: {source_item}"
                )
                continue
            ref = production._items_by_name[source_item]
            for target in targets:
                target_name = target.get("target", "")
                if not target_name:
                    continue
                source_port = target.get("source_port", "") or _matching_host_setting(
                    ref, target_name
                )
                if source_port:
                    ref.port_names.add(source_port)
                if target_name not in production._items_by_name:
                    if _is_internal_runtime_target(target_name):
                        continue
                    production._graph_warnings.append(
                        f"Runtime connection target does not exist: "
                        f"{source_item} -> {target_name}"
                    )
                production._register_connection(
                    source_item,
                    source_port,
                    target_name,
                    origin="runtime",
                    interaction=target.get("interaction", "request"),
                    metadata=target.get("metadata", {}),
                    validate_target=False,
                )

        for ref in production._items:
            if ref.name in runtime_sources_with_targets:
                continue
            for setting_name, value in ref.host_settings.items():
                for target_name in _setting_targets(value):
                    if target_name not in production._items_by_name:
                        continue
                    ref.port_names.add(setting_name)
                    metadata = {"source": "Host setting fallback"}
                    if ref.name in runtime_sources:
                        metadata["reason"] = (
                            "runtime discovery returned no targets"
                        )
                    production._register_connection(
                        ref.name,
                        setting_name,
                        target_name,
                        origin="inferred",
                        metadata=metadata,
                        validate_target=False,
                    )

        return production

    @property
    def items(self) -> tuple[ComponentRef, ...]:
        return tuple(self._items)

    @property
    def edges(self) -> tuple["GraphEdge", ...]:
        return tuple(self._edges)

    def item(self, name: str) -> ComponentRef:
        try:
            return self._items_by_name[name]
        except KeyError as exc:
            raise ValueError(f"Production item does not exist: {name}") from exc

    def component_ref(self, component: ComponentRef | Port | str) -> ComponentRef:
        component_name = self._runtime_component_name(component)
        return self.item(component_name)

    def get_component(self, component: ComponentRef | Port | str) -> ComponentRef:
        return self.component_ref(component)

    def component(
        self,
        name_or_cls: str | type,
        cls: Optional[type] = None,
        *,
        class_name: Optional[str] = None,
        adapter_class: Optional[type | str] = None,
        adapter_class_name: Optional[str] = None,
        kind: str = "component",
        enabled: bool | str = True,
        pool_size: int | str = 1,
        category: str = "",
        foreground: bool | str = False,
        comment: str = "",
        log_trace_events: bool | str = False,
        schedule: str = "",
        settings: Optional[dict[str, Any]] = None,
        adapter_settings: Optional[dict[str, Any]] = None,
    ) -> ComponentRef:
        item_name: str
        component_class: Optional[type]

        if isinstance(name_or_cls, type) and cls is None:
            component_class = name_or_cls
            item_name = component_class.__name__
        else:
            item_name = str(name_or_cls)
            component_class = cls

        if item_name in self._items_by_name:
            raise ValueError(f"Production item already exists: {item_name}")

        adapter_class_ref: Optional[type] = None
        resolved_adapter_class_name = adapter_class_name or ""
        if adapter_class is not None:
            if isinstance(adapter_class, type):
                adapter_class_ref = adapter_class
                resolved_adapter_class_name = (
                    resolved_adapter_class_name
                    or _auto_proxy_class_name(adapter_class)
                )
            else:
                resolved_adapter_class_name = (
                    resolved_adapter_class_name
                    or str(adapter_class)
                )

        ref = ComponentRef(
            production=self,
            name=item_name,
            component_class=component_class,
            class_name=class_name,
            adapter_class=adapter_class_ref,
            adapter_class_name=resolved_adapter_class_name,
            kind=kind,
            category=category,
            pool_size=pool_size,
            enabled=enabled,
            foreground=foreground,
            comment=comment,
            log_trace_events=log_trace_events,
            schedule=schedule,
            host_settings=dict(settings or {}),
            adapter_settings=dict(adapter_settings or {}),
        )
        self._add_item(ref)
        return ref

    def add_component(self, *args: Any, **kwargs: Any) -> ComponentRef:
        return self.component(*args, **kwargs)

    def update_component(
        self,
        item: ComponentRef | str,
        **kwargs: Any,
    ) -> ComponentRef:
        ref = self._component_ref(item)
        scalar_fields = {
            "kind",
            "category",
            "pool_size",
            "enabled",
            "foreground",
            "comment",
            "log_trace_events",
            "schedule",
        }
        for field_name in scalar_fields:
            if field_name in kwargs:
                setattr(ref, field_name, kwargs.pop(field_name))

        if "component_class" in kwargs:
            ref.component_class = kwargs.pop("component_class")
            if "class_name" not in kwargs and ref.component_class is not None:
                ref.class_name = _auto_proxy_class_name(ref.component_class)
        if "class_name" in kwargs:
            ref.class_name = kwargs.pop("class_name")
        if ref.class_name is None and ref.component_class is None:
            raise ValueError("component_class or class_name is required")
        if "adapter_class" in kwargs:
            adapter_class = kwargs.pop("adapter_class")
            if adapter_class is None:
                ref.adapter_class = None
            elif isinstance(adapter_class, type):
                ref.adapter_class = adapter_class
                if "adapter_class_name" not in kwargs:
                    ref.adapter_class_name = _auto_proxy_class_name(adapter_class)
            else:
                ref.adapter_class = None
                if "adapter_class_name" not in kwargs:
                    ref.adapter_class_name = str(adapter_class)
        if "adapter_class_name" in kwargs:
            ref.adapter_class_name = str(kwargs.pop("adapter_class_name") or "")
        if not ref.adapter_class_name:
            ref.adapter_class_name = _adapter_type_from_component_class(
                ref.component_class
            )

        if "settings" in kwargs:
            _apply_settings_update(ref.host_settings, kwargs.pop("settings"))
        if "host_settings" in kwargs:
            _apply_settings_update(ref.host_settings, kwargs.pop("host_settings"))
        if "adapter_settings" in kwargs:
            _apply_settings_update(ref.adapter_settings, kwargs.pop("adapter_settings"))
        if "other_settings" in kwargs:
            ref.other_settings = [dict(value) for value in kwargs.pop("other_settings")]
        if "ports" in kwargs:
            ref.port_names.update(str(value) for value in kwargs.pop("ports"))

        if kwargs:
            names = ", ".join(sorted(kwargs))
            raise ValueError(f"Unsupported component update fields: {names}")
        return ref

    def delete_component(self, item: ComponentRef | str) -> None:
        ref = self._component_ref(item)
        self._items = [existing for existing in self._items if existing is not ref]
        self._items_by_name.pop(ref.name, None)

        for edge in list(self._edges):
            if edge.target != ref.name:
                continue
            source_item = edge.source_item
            source_port = edge.source_port
            source_ref = self._items_by_name.get(source_item)
            if source_ref is not None and source_port:
                if source_ref.host_settings.get(source_port) == ref.name:
                    source_ref.host_settings.pop(source_port, None)

        self._connections = {
            key: targets
            for key, targets in (
                (key, [target for target in targets if target != ref.name])
                for key, targets in self._connections.items()
                if key[0] != ref.name
            )
            if targets
        }
        self._edges = [
            edge
            for edge in self._edges
            if edge.source_item != ref.name and edge.target != ref.name
        ]

    def disconnect(self, source: Port | str) -> None:
        if isinstance(source, Port):
            if source.production is not self:
                raise ValueError("source port belongs to a different Production")
            item_name = source.item_name
            port_name = source.name
        else:
            item_name, separator, port_name = str(source).rpartition(".")
            if not separator:
                raise ValueError("source must be a Port or an Item.Port string")

        key = (item_name, port_name)
        if key not in self._connections:
            raise ValueError(f"Production port is not connected: {item_name}.{port_name}")
        self._connections.pop(key, None)
        ref = self.item(item_name)
        ref.host_settings.pop(port_name, None)
        self._edges = [
            edge
            for edge in self._edges
            if not (
                edge.source_item == item_name
                and edge.source_port == port_name
            )
        ]

    def service(self, name_or_cls: str | type, cls: Optional[type] = None, **kwargs):
        return self.component(name_or_cls, cls, kind="service", **kwargs)

    def process(self, name_or_cls: str | type, cls: Optional[type] = None, **kwargs):
        return self.component(name_or_cls, cls, kind="process", **kwargs)

    def operation(self, name_or_cls: str | type, cls: Optional[type] = None, **kwargs):
        return self.component(name_or_cls, cls, kind="operation", **kwargs)

    def connect(self, source: Port, target_component: ComponentRef | str) -> None:
        if not isinstance(source, Port):
            raise TypeError("source must be a Port returned from a ComponentRef")
        if source.production is not self:
            raise ValueError("source port belongs to a different Production")

        target_name = self._component_name(target_component)
        source.component.set_host_setting(source.name, target_name)
        source.component.port_names.add(source.name)
        self._register_connection(
            source.item_name,
            source.name,
            target_name,
            logical_name=source.logical_name,
            replace_port=True,
        )

    def connect_add(self, source: Port, target_component: ComponentRef | str) -> None:
        """Append a fan-out target to a source port without replacing existing targets.

        The IRIS host setting value becomes a comma-separated list of target names.
        Use instead of ``connect()`` when a single port should route to multiple
        components.
        """
        if not isinstance(source, Port):
            raise TypeError("source must be a Port returned from a ComponentRef")
        if source.production is not self:
            raise ValueError("source port belongs to a different Production")
        target_name = self._component_name(target_component)
        existing = source.component.host_settings.get(source.name, "")
        existing_targets = [t.strip() for t in existing.split(",") if t.strip()]
        if target_name not in existing_targets:
            source.component.host_settings[source.name] = ",".join(
                existing_targets + [target_name]
            )
        source.component.port_names.add(source.name)
        self._register_connection(
            source.item_name,
            source.name,
            target_name,
            logical_name=source.logical_name,
            replace_port=False,
        )

    def resolve_port(self, port: Port) -> str:
        if port.production is not self:
            raise ValueError("port belongs to a different Production")
        return self._resolve_connection_target(port.item_name, port.name, port.path)

    def _resolve_connection_target(
        self,
        item_name: str,
        port_name: str,
        path: str,
    ) -> str:
        key = (item_name, port_name)
        targets = self._connections.get(key)
        if not targets:
            raise ValueError(f"Production port is not connected: {path}")
        if len(targets) > 1:
            target_list = ", ".join(repr(target) for target in targets)
            raise ValueError(
                f"Production port is ambiguous: {path} resolves to "
                f"multiple targets ({target_list})"
            )
        return targets[0]

    def resolve_target(self, target_or_port: str | Port | ComponentRef) -> str:
        if isinstance(target_or_port, Port):
            return self.resolve_port(target_or_port)
        if isinstance(target_or_port, ComponentRef):
            return self._component_name(target_or_port)

        target_name = str(target_or_port)
        if target_name in self._items_by_name:
            return target_name

        if "." in target_name:
            item_name, _, port_name = target_name.rpartition(".")
            if item_name not in self._items_by_name:
                raise ValueError(f"Production item does not exist: {item_name}")
            key = (item_name, port_name)
            if key not in self._connections:
                raise ValueError(f"Production port is not connected: {target_name}")
            return self._resolve_connection_target(item_name, port_name, target_name)

        raise ValueError(f"Production item does not exist: {target_name}")

    def to_dict(self) -> dict[str, Any]:
        production: dict[str, Any] = {
            "@Name": self.name,
            "@TestingEnabled": _bool_text(self.testing_enabled),
            "@LogGeneralTraceEvents": _bool_text(self.log_general_trace_events),
            "Description": self.description,
            "ActorPoolSize": _text_value(self.actor_pool_size),
        }
        if self._items:
            production["Item"] = [item.to_dict() for item in self._items]
        return {self.name: production}

    def to_xml(self) -> str:
        from ._utils import _Utils

        return _Utils.dict_to_xml({"Production": self.to_dict()[self.name]})

    def graph(self) -> ProductionGraph:
        nodes = tuple(
            GraphNode(
                name=item.name,
                class_name=item.class_name or "",
                kind=item.kind,
                enabled=item.enabled,
                category=item.category,
                adapter_class_name=item.adapter_class_name,
            )
            for item in self._items
        )
        edges = tuple(self._edges)
        return ProductionGraph(
            production_name=self.name,
            nodes=nodes,
            edges=edges,
            warnings=tuple(self._graph_warnings),
        )

    def diff(
        self,
        other: Production | dict[str, Any] | None = None,
    ) -> ProductionDiff:
        """Compare deployable IRIS shape against current/imported state.

        With no *other* argument, IRIS is queried through ``from_iris()`` and the
        returned diff describes what would change to make that runtime
        reconstruction match this Python object.
        """
        return self.diff_deployable(other)

    def diff_deployable(
        self,
        other: Production | dict[str, Any] | None = None,
    ) -> ProductionDiff:
        """Compare settings, items, and deployable routes.

        Edge import metadata such as ``origin`` is ignored so an authored Python
        route and an equivalent IRIS setting-inferred route do not produce a
        false deployment change.
        """
        current = self._diff_current(other)
        return _diff_productions(desired=self, current=current)

    def graph_diff(
        self,
        other: Production | dict[str, Any] | None = None,
    ) -> ProductionDiff:
        """Compare graph topology including edge origin and route metadata."""
        current = self._diff_current(other)
        return _diff_productions(
            desired=self,
            current=current,
            include_graph_metadata=True,
        )

    def component_registrations(self) -> tuple[ComponentRef, ...]:
        return tuple(
            item for item in self._items if item.component_class is not None
        )

    def adapter_registrations(self) -> tuple[ComponentRef, ...]:
        return tuple(
            item for item in self._items if item.adapter_class is not None
        )

    def start(self, detach: bool = True) -> None:
        runtime = _ProductionRuntime(self)
        director = runtime.director
        if detach:
            director.start_production(self.name)
        else:
            director.start_production_with_log(self.name)

    def stop(self) -> None:
        director = _ProductionRuntime(self).director
        self._require_current_production(director, "stop")
        director.stop_production()

    def restart(self) -> None:
        director = _ProductionRuntime(self).director
        self._require_current_production(director, "restart")
        director.restart_production()

    def kill(self) -> None:
        director = _ProductionRuntime(self).director
        self._require_current_production(director, "kill")
        director.shutdown_production()

    def status(self) -> dict:
        return _ProductionRuntime(self).director.status_production()

    def queue(self, *, refresh: bool = True) -> dict[str, dict[str, Any]]:
        if not refresh:
            return {name: dict(value) for name, value in self._queue_info.items()}
        info = _ProductionRuntime(self).director.export_production_queue_info(self.name)
        queue_map, _queue_warnings = _normalize_queue_info(info)
        self._queue_info = queue_map
        return {name: dict(value) for name, value in queue_map.items()}

    def queue_info(self, *, refresh: bool = True) -> dict[str, dict[str, Any]]:
        return self.queue(refresh=refresh)

    def update(self) -> None:
        director = _ProductionRuntime(self).director
        self._require_current_production(director, "update")
        director.update_production()

    def inspect_component(
        self,
        component: ComponentRef | Port | str,
        *,
        refresh: bool = True,
    ) -> dict[str, Any]:
        """Return design-time and runtime details for a production component."""
        component_name = self._runtime_component_name(component)
        ref = self.item(component_name)
        graph = self.graph()
        outgoing = [
            edge.to_dict()
            for edge in graph.edges
            if edge.source_item == component_name
        ]
        incoming = [
            edge.to_dict()
            for edge in graph.edges
            if edge.target == component_name
        ]
        info: dict[str, Any] = {
            "production": self.name,
            "name": ref.name,
            "class_name": ref.class_name or "",
            "adapter_class_name": ref.adapter_class_name,
            "kind": ref.kind,
            "category": ref.category,
            "enabled": ref.enabled,
            "pool_size": ref.pool_size,
            "foreground": ref.foreground,
            "comment": ref.comment,
            "log_trace_events": ref.log_trace_events,
            "schedule": ref.schedule,
            "settings": {
                "Host": dict(ref.host_settings),
                "Adapter": dict(ref.adapter_settings),
                "Other": [dict(setting) for setting in ref.other_settings],
            },
            "ports": sorted(ref.port_names),
            "outgoing": outgoing,
            "incoming": incoming,
        }

        if refresh:
            runtime_info = self._component_runtime_info(component_name)
            if runtime_info:
                info["runtime"] = runtime_info
        elif component_name in self._queue_info:
            info["runtime"] = {"queue": dict(self._queue_info[component_name])}
        return info

    def start_component(self, component: ComponentRef | Port | str) -> None:
        component_name = self._runtime_component_name(component)
        director = _ProductionRuntime(self).director
        self._require_current_runtime(
            director,
            f"start component {component_name!r} in production {self.name!r}",
        )
        director.start_component(component_name)

    def stop_component(self, component: ComponentRef | Port | str) -> None:
        component_name = self._runtime_component_name(component)
        director = _ProductionRuntime(self).director
        self._require_current_runtime(
            director,
            f"stop component {component_name!r} in production {self.name!r}",
        )
        director.stop_component(component_name)

    def restart_component(self, component: ComponentRef | Port | str) -> None:
        component_name = self._runtime_component_name(component)
        director = _ProductionRuntime(self).director
        self._require_current_runtime(
            director,
            f"restart component {component_name!r} in production {self.name!r}",
        )
        director.restart_component(component_name)

    def export(self) -> dict:
        return _ProductionRuntime(self).director.export_production(self.name)

    def set_default(self) -> None:
        _ProductionRuntime(self).director.set_default_production(self.name)

    def sync(self, *, root_path: Optional[str] = None, update: bool = True) -> None:
        if _has_remote_director(self):
            raise NotImplementedError(
                "Production.sync() can only register directly with local IRIS. "
                "Use `iop --migrate <settings_file>` for remote migrations."
            )
        from ._utils import _Utils

        with _temporary_env("IRISNAMESPACE", self.namespace):
            _Utils.set_productions_settings([self], root_path)
            if update:
                from ._local import _LocalDirector

                _LocalDirector().update_production()

    def apply(self, *, root_path: Optional[str] = None, update: bool = True) -> None:
        self.sync(root_path=root_path, update=update)

    def log(self, top: Optional[int] = None) -> None:
        director = _ProductionRuntime(self).director
        if top is None:
            director.log_production()
        else:
            director.log_production_top(top)

    def test_component(
        self,
        target_or_port: str | Port | ComponentRef,
        message: Any = None,
        classname: Optional[str] = None,
        body: str | dict | None = None,
    ) -> Any:
        runtime = _ProductionRuntime(self)
        director = runtime.director
        target_name = self.resolve_target(target_or_port)

        self._raise_if_existing_production_not_running(director)

        if classname is None and body is None and message is not None:
            classname, body = _message_to_classname_body(message)
            if classname is not None:
                message = None
        return director.test_component(
            target_name,
            message=message,
            classname=classname,
            body=body,
        )

    def test(
        self,
        target_or_port: str | Port | ComponentRef,
        message: Any = None,
        classname: Optional[str] = None,
        body: str | dict | None = None,
    ) -> Any:
        return self.test_component(
            target_or_port,
            message=message,
            classname=classname,
            body=body,
        )

    def _raise_if_existing_production_not_running(self, director: Any) -> None:
        production_name, state = self._read_status(director, "test")
        state_lower = str(state).lower()
        if production_name == self.name and str(state).lower() == "running":
            return

        if (
            production_name
            and production_name != self.name
            and state_lower == "running"
        ):
            raise RuntimeError(
                f"Production {self.name!r} exists but is not running "
                f"(currently running production is {production_name!r}). "
                f"{self._switch_running_production_message(production_name)} "
                "Do that before calling `prod.test(...)`."
            )
        if production_name and production_name != self.name:
            detail = f"current default production is {production_name!r}"
        elif state:
            detail = f"current status is {state!r}"
        else:
            detail = "runtime status did not report a running production"
        raise RuntimeError(
            f"Production {self.name!r} exists but is not running ({detail}). "
            f"Start it with `iop --start {self.name} --detach` or "
            "`prod.start()` before calling `prod.test(...)`."
        )

    def _require_current_production(self, director: Any, action: str) -> None:
        self._require_current_runtime(
            director,
            f"{action} production {self.name!r}",
        )

    def _require_current_runtime(self, director: Any, action: str) -> None:
        production_name, state = self._read_status(director, action)
        if production_name == self.name:
            return

        if production_name:
            detail = f"current/default production is {production_name!r}"
        elif state:
            detail = f"current status is {state!r}"
        else:
            detail = "runtime status did not report a current/default production"
        raise RuntimeError(
            f"Cannot {action}: {detail}. "
            f"Select {self.name!r} with `prod.set_default()` or start it with "
            "`prod.start()` before using this lifecycle method."
        )

    def _read_status(self, director: Any, action: str) -> tuple[str, str]:
        try:
            status = director.status_production()
        except Exception as exc:
            raise RuntimeError(
                f"Cannot {action}: could not verify production status ({exc})."
            ) from exc
        if not isinstance(status, dict):
            raise RuntimeError(
                f"Cannot {action}: production status response is invalid "
                f"({status!r})."
            )
        production_name = status.get("Production") or status.get("production") or ""
        state = status.get("Status") or status.get("status") or ""
        return str(production_name), str(state)

    def _switch_running_production_message(self, current_production: str) -> str:
        return (
            f"IRIS can run only one production at a time. Stop {current_production!r} "
            f"first with `iop --stop`, then start {self.name!r} with "
            f"`iop --start {self.name} --detach`; or call `prod.stop()` and "
            "`prod.start()` explicitly."
        )

    def _component_runtime_info(self, component_name: str) -> dict[str, Any]:
        director = _ProductionRuntime(self).director
        runtime: dict[str, Any] = {}
        warnings: list[str] = []

        try:
            status = director.status_production()
        except Exception as exc:
            warnings.append(f"Could not fetch production status: {exc}")
        else:
            if isinstance(status, dict):
                production_name = (
                    status.get("Production")
                    or status.get("production")
                    or ""
                )
                state = status.get("Status") or status.get("status") or ""
                runtime["production_status"] = dict(status)
                runtime["current_production"] = str(production_name)
                runtime["status"] = str(state)
                runtime["is_current_production"] = production_name == self.name
                runtime["is_running"] = (
                    production_name == self.name
                    and str(state).lower() == "running"
                )
            else:
                warnings.append(
                    f"Production status response is invalid: {status!r}"
                )

        try:
            queue_info = director.export_production_queue_info(self.name)
        except Exception as exc:
            warnings.append(f"Could not fetch queue info: {exc}")
        else:
            queue_map, queue_warnings = _normalize_queue_info(queue_info)
            warnings.extend(queue_warnings)
            self._queue_info = queue_map
            if component_name in queue_map:
                runtime["queue"] = dict(queue_map[component_name])

        if warnings:
            runtime["warnings"] = warnings
        return runtime

    def _component_name(self, target_component: ComponentRef | str) -> str:
        if isinstance(target_component, ComponentRef):
            if target_component.production is not self:
                raise ValueError("target component belongs to a different Production")
            return target_component.name
        target_name = str(target_component)
        if target_name not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {target_name}")
        return target_name

    def _runtime_component_name(self, component: ComponentRef | Port | str) -> str:
        if isinstance(component, Port):
            component_name = self.resolve_port(component)
        elif isinstance(component, ComponentRef):
            component_name = self._component_name(component)
        else:
            component_name = self.resolve_target(str(component))
        if component_name not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {component_name}")
        return component_name

    def _component_ref(self, item: ComponentRef | str) -> ComponentRef:
        if isinstance(item, ComponentRef):
            if item.production is not self:
                raise ValueError("component belongs to a different Production")
            return item
        return self.item(str(item))

    def _add_item(self, ref: ComponentRef) -> None:
        if not ref.name:
            raise ValueError("Production item name is required")
        if ref.name in self._items_by_name:
            raise ValueError(f"Production item already exists: {ref.name}")
        if ref.component_class is not None:
            for existing in self._items:
                if (
                    existing.component_class is not None
                    and existing.component_class is not ref.component_class
                    and existing.class_name == ref.class_name
                ):
                    raise ValueError(
                        f"Python classes {existing.component_class.__qualname__!r} and "
                        f"{ref.component_class.__qualname__!r} produce the same IRIS "
                        f"proxy class name {ref.class_name!r}. Rename one of the "
                        "Python classes or supply an explicit class_name= to resolve "
                        "the collision."
                    )
        self._items.append(ref)
        self._items_by_name[ref.name] = ref

    def _diff_current(
        self,
        other: Production | dict[str, Any] | None,
    ) -> Production:
        if other is None:
            return self.from_iris(
                self.name,
                namespace=self.namespace,
                director=self._director,
            )
        if isinstance(other, Production):
            return other
        if isinstance(other, dict):
            return self.from_dict(
                other,
                namespace=self.namespace,
                director=self._director,
            )
        raise TypeError("other must be a Production, production dictionary, or None")

    def _register_connection(
        self,
        source_item: str,
        source_port: str,
        target_name: str,
        *,
        logical_name: str = "",
        origin: str = "authored",
        interaction: str = "request",
        metadata: Optional[dict[str, Any]] = None,
        replace_port: bool = False,
        validate_target: bool = True,
    ) -> None:
        if source_item not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {source_item}")
        if validate_target and target_name not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {target_name}")
        if source_port:
            key = (source_item, source_port)
            if replace_port:
                self._connections[key] = [target_name]
            else:
                self._connections.setdefault(key, [])
                if target_name not in self._connections[key]:
                    self._connections[key].append(target_name)

        edge = GraphEdge(
            source_item=source_item,
            source_port=source_port,
            logical_name=logical_name,
            target=target_name,
            origin=origin,
            interaction=interaction,
            metadata=dict(metadata or {}),
        )

        if replace_port and source_port:
            self._edges = [
                existing
                for existing in self._edges
                if not (
                    existing.source_item == source_item
                    and existing.source_port == source_port
                )
            ]

        edge_key = _edge_identity(edge)
        self._edges = [
            existing
            for existing in self._edges
            if _edge_identity(existing) != edge_key
        ]
        self._edges.append(edge)


def _edge_identity(edge: GraphEdge) -> tuple[Any, ...]:
    return (
        edge.source_item,
        edge.source_port,
        edge.target,
        edge.origin,
        edge.interaction,
        edge.logical_name,
        tuple(
            sorted(
                (str(key), _canonical_value(value))
                for key, value in edge.metadata.items()
            )
        ),
    )


def _diff_productions(
    desired: Production,
    current: Production,
    *,
    include_graph_metadata: bool = False,
) -> ProductionDiff:
    changes: list[ProductionDiffEntry] = []
    warnings = _diff_warnings(desired, current)

    if current.name != desired.name:
        changes.append(
            ProductionDiffEntry(
                action="change",
                kind="production",
                path="production.name",
                before=current.name,
                after=desired.name,
            )
        )

    _diff_mapping_values(
        changes,
        kind="production",
        base_path="production",
        before=_production_signature(current),
        after=_production_signature(desired),
    )
    _diff_items(changes, desired=desired, current=current)
    _diff_connections(
        changes,
        desired=desired,
        current=current,
        include_graph_metadata=include_graph_metadata,
    )

    return ProductionDiff(
        production_name=desired.name,
        changes=tuple(changes),
        warnings=tuple(warnings),
    )


def _diff_warnings(desired: Production, current: Production) -> list[str]:
    warnings = []
    warnings.extend(f"desired: {warning}" for warning in desired.graph().warnings)
    warnings.extend(f"current: {warning}" for warning in current.graph().warnings)
    return warnings


def _production_signature(production: Production) -> dict[str, Any]:
    return {
        "testing_enabled": _bool_text(production.testing_enabled),
        "log_general_trace_events": _bool_text(production.log_general_trace_events),
        "actor_pool_size": _text_value(production.actor_pool_size),
        "description": production.description,
    }


def _item_signatures(production: Production) -> dict[str, dict[str, Any]]:
    return {item.name: _item_signature(item) for item in production.items}


def _item_signature(item: ComponentRef) -> dict[str, Any]:
    return {
        "class_name": item.class_name or "",
        "category": item.category,
        "pool_size": _text_value(item.pool_size),
        "enabled": _bool_text(item.enabled),
        "foreground": _bool_text(item.foreground),
        "comment": item.comment,
        "log_trace_events": _bool_text(item.log_trace_events),
        "schedule": item.schedule,
        "host_settings": _settings_signature(item.host_settings),
        "adapter_settings": _settings_signature(item.adapter_settings),
        "other_settings": _canonical_value(item.other_settings),
    }


def _settings_signature(settings: dict[str, Any]) -> dict[str, str]:
    return {key: _text_value(settings[key]) for key in sorted(settings)}


def _diff_items(
    changes: list[ProductionDiffEntry],
    *,
    desired: Production,
    current: Production,
) -> None:
    desired_items = _item_signatures(desired)
    current_items = _item_signatures(current)

    for item_name in sorted(current_items.keys() - desired_items.keys()):
        changes.append(
            ProductionDiffEntry(
                action="remove",
                kind="item",
                path=f"items.{item_name}",
                before=current_items[item_name],
            )
        )

    for item_name in sorted(desired_items.keys() - current_items.keys()):
        changes.append(
            ProductionDiffEntry(
                action="add",
                kind="item",
                path=f"items.{item_name}",
                after=desired_items[item_name],
            )
        )

    for item_name in sorted(desired_items.keys() & current_items.keys()):
        _diff_item_fields(
            changes,
            item_name=item_name,
            before=current_items[item_name],
            after=desired_items[item_name],
        )


def _diff_item_fields(
    changes: list[ProductionDiffEntry],
    *,
    item_name: str,
    before: dict[str, Any],
    after: dict[str, Any],
) -> None:
    scalar_fields = [
        "class_name",
        "category",
        "pool_size",
        "enabled",
        "foreground",
        "comment",
        "log_trace_events",
        "schedule",
    ]
    _diff_mapping_values(
        changes,
        kind="item",
        base_path=f"items.{item_name}",
        before={field: before[field] for field in scalar_fields},
        after={field: after[field] for field in scalar_fields},
    )
    _diff_mapping_values(
        changes,
        kind="setting",
        base_path=f"items.{item_name}.settings.Host",
        before=before["host_settings"],
        after=after["host_settings"],
    )
    _diff_mapping_values(
        changes,
        kind="setting",
        base_path=f"items.{item_name}.settings.Adapter",
        before=before["adapter_settings"],
        after=after["adapter_settings"],
    )
    if before["other_settings"] != after["other_settings"]:
        changes.append(
            ProductionDiffEntry(
                action="change",
                kind="setting",
                path=f"items.{item_name}.settings.Other",
                before=before["other_settings"],
                after=after["other_settings"],
            )
        )


def _diff_mapping_values(
    changes: list[ProductionDiffEntry],
    *,
    kind: str,
    base_path: str,
    before: dict[str, Any],
    after: dict[str, Any],
) -> None:
    for key in sorted(before.keys() - after.keys()):
        changes.append(
            ProductionDiffEntry(
                action="remove",
                kind=kind,
                path=f"{base_path}.{key}",
                before=before[key],
            )
        )
    for key in sorted(after.keys() - before.keys()):
        changes.append(
            ProductionDiffEntry(
                action="add",
                kind=kind,
                path=f"{base_path}.{key}",
                after=after[key],
            )
        )
    for key in sorted(before.keys() & after.keys()):
        if before[key] != after[key]:
            changes.append(
                ProductionDiffEntry(
                    action="change",
                    kind=kind,
                    path=f"{base_path}.{key}",
                    before=before[key],
                    after=after[key],
                )
            )


def _diff_connections(
    changes: list[ProductionDiffEntry],
    *,
    desired: Production,
    current: Production,
    include_graph_metadata: bool = False,
) -> None:
    desired_connections = _connection_signature(
        desired,
        include_graph_metadata=include_graph_metadata,
    )
    current_connections = _connection_signature(
        current,
        include_graph_metadata=include_graph_metadata,
    )

    for source in sorted(current_connections.keys() - desired_connections.keys()):
        changes.append(
            ProductionDiffEntry(
                action="remove",
                kind="connection",
                path=f"connections.{_connection_source_path(source)}",
                before=current_connections[source],
            )
        )
    for source in sorted(desired_connections.keys() - current_connections.keys()):
        changes.append(
            ProductionDiffEntry(
                action="add",
                kind="connection",
                path=f"connections.{_connection_source_path(source)}",
                after=desired_connections[source],
            )
        )
    for source in sorted(desired_connections.keys() & current_connections.keys()):
        before = current_connections[source]
        after = desired_connections[source]
        if before != after:
            changes.append(
                ProductionDiffEntry(
                    action="change",
                    kind="connection",
                    path=f"connections.{_connection_source_path(source)}",
                    before=before,
                    after=after,
                )
            )


def _connection_signature(
    production: Production,
    *,
    include_graph_metadata: bool = False,
) -> dict[tuple[str, str], list[Any]]:
    if include_graph_metadata:
        detailed_connections: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for edge in production.graph().edges:
            source = (edge.source_item, edge.source_port)
            detailed_connections.setdefault(source, []).append(_edge_diff_value(edge))
        return {
            source: sorted(
                values,
                key=lambda value: json.dumps(value, sort_keys=True),
            )
            for source, values in sorted(detailed_connections.items())
        }

    connections: dict[tuple[str, str], set[str]] = {}
    for edge in production.graph().edges:
        source = (edge.source_item, edge.source_port)
        connections.setdefault(source, set()).add(edge.target)
    return {
        source: list(sorted(targets))
        for source, targets in sorted(connections.items())
    }


def _edge_diff_value(edge: GraphEdge) -> dict[str, Any]:
    data: dict[str, Any] = {
        "target": edge.target,
        "origin": edge.origin,
        "interaction": edge.interaction,
        "logical_name": edge.logical_name,
    }
    if edge.metadata:
        data["metadata"] = _canonical_value(edge.metadata)
    return data


def _connection_source_path(source: tuple[str, str]) -> str:
    source_item, source_port = source
    if source_port:
        return f"{source_item}.{source_port}"
    return source_item


def _canonical_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _canonical_value(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, bool):
        return _bool_text(value)
    if value is None:
        return ""
    return value


def _diff_value_text(value: Any) -> str:
    if isinstance(value, str):
        return repr(value)
    try:
        return json.dumps(value, sort_keys=True)
    except TypeError:
        return repr(value)


def _message_to_classname_body(message: Any) -> tuple[Optional[str], str | dict | None]:
    classname = f"{message.__class__.__module__}.{message.__class__.__name__}"
    if isinstance(message, BaseModel):
        return classname, message.model_dump_json()
    if is_dataclass(message):
        from ._serialization import dataclass_to_dict

        return classname, json.dumps(dataclass_to_dict(message))
    return None, None


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _production_payload(data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if not isinstance(data, dict) or not data:
        raise ValueError("Production data must be a non-empty dictionary.")

    if "Production" in data:
        production_data = data["Production"]
        if not isinstance(production_data, dict):
            raise ValueError("Production data must be a dictionary.")
        production_name = production_data.get("@Name") or "Production"
        return production_name, production_data

    production_name = next(iter(data.keys()))
    production_data = data[production_name]
    if not isinstance(production_data, dict):
        raise ValueError("Production data must be a dictionary.")
    production_name = production_data.get("@Name") or production_name
    return production_name, production_data


def _split_settings(
    settings: Any,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    host_settings: dict[str, Any] = {}
    adapter_settings: dict[str, Any] = {}
    other_settings: list[dict[str, Any]] = []

    for setting in _as_list(settings):
        if not isinstance(setting, dict):
            continue
        target = setting.get("@Target", "Host")
        name = setting.get("@Name", "")
        value = setting.get("#text", "")
        if target in ("", "Host"):
            host_settings[name] = value
        elif target == "Adapter":
            adapter_settings[name] = value
        else:
            other_settings.append(dict(setting))
    return host_settings, adapter_settings, other_settings


def _normalize_connections(
    connections: Any,
) -> tuple[dict[str, list[dict[str, Any]]], set[str], list[str]]:
    connection_map: dict[str, list[dict[str, Any]]] = {}
    runtime_sources: set[str] = set()
    warnings: list[str] = []

    if connections is None:
        return connection_map, runtime_sources, warnings

    if isinstance(connections, dict):
        warnings.extend(str(value) for value in _as_list(connections.get("warnings")))
        if "items" in connections:
            for item in _as_list(connections.get("items")):
                if not isinstance(item, dict):
                    continue
                source = (
                    item.get("item")
                    or item.get("name")
                    or item.get("source_item")
                    or ""
                )
                if not source:
                    continue
                item_warnings = [value for value in _as_list(item.get("warnings")) if value]
                warnings.extend(
                    f"{source}: {value}"
                    for value in item_warnings
                )
                discovered = False
                for target in _as_list(item.get("connections")):
                    normalized = _normalize_connection_target(target)
                    if normalized is not None:
                        discovered = True
                        connection_map.setdefault(source, []).append(normalized)
                for edge in _as_list(item.get("edges")):
                    normalized = _normalize_connection_target(edge)
                    if normalized is not None:
                        discovered = True
                        connection_map.setdefault(source, []).append(normalized)
                if not item_warnings or discovered:
                    runtime_sources.add(source)
            return connection_map, runtime_sources, warnings

        for source, targets in connections.items():
            if source in ("production", "warnings"):
                continue
            runtime_sources.add(str(source))
            for target in _as_list(targets):
                normalized = _normalize_connection_target(target)
                if normalized is not None:
                    connection_map.setdefault(str(source), []).append(normalized)
        return connection_map, runtime_sources, warnings

    if isinstance(connections, list):
        for edge in connections:
            if not isinstance(edge, dict):
                continue
            source = edge.get("source_item") or edge.get("item") or ""
            if not source and "." in str(edge.get("source", "")):
                source, _, source_port = str(edge["source"]).rpartition(".")
                edge = {**edge, "source_port": source_port}
            if not source:
                continue
            runtime_sources.add(str(source))
            normalized = _normalize_connection_target(edge)
            if normalized is not None:
                connection_map.setdefault(str(source), []).append(normalized)
        return connection_map, runtime_sources, warnings

    warnings.append(f"Ignoring invalid runtime connections: {connections!r}")
    return connection_map, runtime_sources, warnings


def _normalize_runtime_item_metadata(connections: Any) -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    if not isinstance(connections, dict):
        return metadata
    for item in _as_list(connections.get("items")):
        if not isinstance(item, dict):
            continue
        item_name = (
            item.get("item")
            or item.get("name")
            or item.get("source_item")
            or ""
        )
        if not item_name:
            continue
        adapter_class_name = (
            item.get("adapter_class_name")
            or item.get("adapter")
            or item.get("AdapterClassName")
            or item.get("Adapter")
            or ""
        )
        if adapter_class_name:
            metadata[str(item_name)] = {
                "adapter_class_name": str(adapter_class_name)
            }
    return metadata


def _normalize_connection_target(value: Any) -> Optional[dict[str, Any]]:
    if isinstance(value, str):
        if not value:
            return None
        return {"target": value, "source_port": ""}
    if not isinstance(value, dict):
        return None
    target = value.get("target") or value.get("name") or value.get("to") or ""
    if not target:
        return None
    source_port = value.get("source_port") or value.get("port") or ""
    metadata = dict(value.get("metadata") or {})
    known_keys = {
        "target",
        "name",
        "to",
        "source_port",
        "port",
        "interaction",
        "metadata",
    }
    for key, item in value.items():
        if key not in known_keys and item is not None:
            metadata.setdefault(str(key), item)
    normalized: dict[str, Any] = {
        "target": str(target),
        "source_port": str(source_port),
    }
    if value.get("interaction"):
        normalized["interaction"] = str(value["interaction"])
    if metadata:
        normalized["metadata"] = metadata
    return normalized


def _normalize_queue_info(value: Any) -> tuple[dict[str, dict[str, Any]], list[str]]:
    queue_map: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    if value is None:
        return queue_map, warnings

    if isinstance(value, dict):
        warnings.extend(str(item) for item in _as_list(value.get("warnings")) if item)
        if "items" in value:
            for item in _as_list(value.get("items")):
                normalized = _normalize_queue_item(item)
                if normalized is None:
                    continue
                item_name, info = normalized
                queue_map[item_name] = info
            return queue_map, warnings

        for item_name, info in value.items():
            if item_name in ("production", "warnings"):
                continue
            if isinstance(info, dict):
                queue_map[str(item_name)] = dict(info)
        return queue_map, warnings

    if isinstance(value, list):
        for item in value:
            normalized = _normalize_queue_item(item)
            if normalized is None:
                continue
            item_name, info = normalized
            queue_map[item_name] = info
        return queue_map, warnings

    warnings.append(f"Ignoring invalid queue info: {value!r}")
    return queue_map, warnings


def _normalize_queue_item(value: Any) -> Optional[tuple[str, dict[str, Any]]]:
    if not isinstance(value, dict):
        return None
    item_name = value.get("item") or value.get("name") or value.get("queue_name") or ""
    if not item_name:
        return None
    info = dict(value)
    info.pop("item", None)
    info.setdefault("queue_name", info.pop("name", item_name))
    return str(item_name), info


def _setting_targets(value: Any) -> list[str]:
    text = _text_value(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def _matching_host_setting(component: ComponentRef, target_name: str) -> str:
    for name, value in component.host_settings.items():
        if target_name in _setting_targets(value):
            return name
    return ""


def _is_internal_runtime_target(target_name: str) -> bool:
    return target_name in {"Ens.Alert", "Ens.ScheduleHandler"}


def _has_remote_director(production: Production) -> bool:
    try:
        from ._remote import _RemoteDirector
    except Exception:
        return False

    return isinstance(production._director, _RemoteDirector)


def resolve_target(target_value: Any) -> Any:
    """Resolve Port values to the current IRIS dispatch string."""
    if isinstance(target_value, Port):
        return target_value.resolve()
    return target_value


@contextmanager
def _temporary_env(name: str, value: Optional[str]):
    if not value:
        yield
        return

    missing = object()
    previous = os.environ.get(name, missing)
    os.environ[name] = value
    try:
        yield
    finally:
        if previous is missing:
            os.environ.pop(name, None)
        else:
            os.environ[name] = str(previous)


class _NamespaceDirectorProxy:
    def __init__(self, director: Any, namespace: str):
        self._director = director
        self._namespace = namespace

    @property
    def namespace(self) -> str:
        return self._namespace

    def __getattr__(self, name: str) -> Any:
        attribute = getattr(self._director, name)
        if not callable(attribute):
            return attribute

        @wraps(attribute)
        def call_with_namespace(*args: Any, **kwargs: Any) -> Any:
            with _temporary_env("IRISNAMESPACE", self._namespace):
                return attribute(*args, **kwargs)

        return call_with_namespace


class _ProductionRuntime:
    def __init__(self, production: Production):
        self.production = production

    @property
    def director(self):
        if self.production._director is not None:
            return self.production._director

        from ._local import _LocalDirector
        from ._remote import _RemoteDirector, get_remote_settings

        remote_settings = get_remote_settings()
        if remote_settings:
            if self.production.namespace:
                remote_settings = dict(remote_settings)
                remote_settings["namespace"] = self.production.namespace
            return _RemoteDirector(remote_settings)

        if self.production.namespace:
            return _NamespaceDirectorProxy(
                _LocalDirector(),
                self.production.namespace,
            )
        return _LocalDirector()
