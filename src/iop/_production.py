from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from dataclasses import is_dataclass
from typing import Any, Optional

from pydantic import BaseModel

from ._settings import Category, Setting, controls


def _bool_text(value: bool | str) -> str:
    if isinstance(value, str):
        return value.lower()
    return "true" if value else "false"


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
        return self.resolve()


@dataclass(frozen=True)
class GraphNode:
    name: str
    class_name: str
    kind: str = "component"
    enabled: bool | str = True
    category: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "class_name": self.class_name,
            "kind": self.kind,
            "enabled": self.enabled,
            "category": self.category,
        }


@dataclass(frozen=True)
class GraphEdge:
    source_item: str
    target: str
    source_port: str = ""
    logical_name: str = ""
    runtime: bool = False
    inferred: bool = False

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
        }
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
                lines.append(f"    {source_port} -> {edge.target}{suffix}")
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
        director: Any = None,
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
        self._connections: dict[tuple[str, str], str] = {}
        self._edges: list[dict[str, Any]] = []
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

        connection_map, _runtime_sources, warnings = _normalize_connections(connections)
        production._graph_warnings.extend(warnings)
        runtime_sources_with_known_targets: set[str] = set()

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
                else:
                    runtime_sources_with_known_targets.add(source_item)
                production._register_connection(
                    source_item,
                    source_port,
                    target_name,
                    runtime=True,
                    validate_target=False,
                )

        for ref in production._items:
            if ref.name in runtime_sources_with_known_targets:
                continue
            for setting_name, value in ref.host_settings.items():
                for target_name in _setting_targets(value):
                    if target_name not in production._items_by_name:
                        continue
                    ref.port_names.add(setting_name)
                    production._register_connection(
                        ref.name,
                        setting_name,
                        target_name,
                        inferred=True,
                        validate_target=False,
                    )

        return production

    @property
    def items(self) -> tuple[ComponentRef, ...]:
        return tuple(self._items)

    @property
    def edges(self) -> tuple[dict[str, Any], ...]:
        return tuple(dict(edge) for edge in self._edges)

    def item(self, name: str) -> ComponentRef:
        try:
            return self._items_by_name[name]
        except KeyError as exc:
            raise ValueError(f"Production item does not exist: {name}") from exc

    def component(
        self,
        name_or_cls: str | type,
        cls: Optional[type] = None,
        *,
        class_name: Optional[str] = None,
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

        ref = ComponentRef(
            production=self,
            name=item_name,
            component_class=component_class,
            class_name=class_name,
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

        if "settings" in kwargs:
            ref.host_settings.update(dict(kwargs.pop("settings") or {}))
        if "host_settings" in kwargs:
            ref.host_settings.update(dict(kwargs.pop("host_settings") or {}))
        if "adapter_settings" in kwargs:
            ref.adapter_settings.update(dict(kwargs.pop("adapter_settings") or {}))
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
            if edge.get("target") != ref.name:
                continue
            source_item = edge.get("source_item", "")
            source_port = edge.get("source_port", "")
            source_ref = self._items_by_name.get(source_item)
            if source_ref is not None and source_port:
                if source_ref.host_settings.get(source_port) == ref.name:
                    source_ref.host_settings.pop(source_port, None)

        self._connections = {
            key: target
            for key, target in self._connections.items()
            if key[0] != ref.name and target != ref.name
        }
        self._edges = [
            edge
            for edge in self._edges
            if edge.get("source_item") != ref.name and edge.get("target") != ref.name
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
                edge.get("source_item") == item_name
                and edge.get("source_port") == port_name
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
        )

    def resolve_port(self, port: Port) -> str:
        if port.production is not self:
            raise ValueError("port belongs to a different Production")
        key = (port.item_name, port.name)
        if key not in self._connections:
            raise ValueError(f"Production port is not connected: {port.path}")
        return self._connections[key]

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
            return self._connections[key]

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
            )
            for item in self._items
        )
        edges = tuple(
            GraphEdge(
                source_item=edge.get("source_item", ""),
                source_port=edge.get("source_port", ""),
                logical_name=edge.get("logical_name", ""),
                target=edge.get("target", ""),
                runtime=bool(edge.get("runtime", False)),
                inferred=bool(edge.get("inferred", False)),
            )
            for edge in self._edges
        )
        return ProductionGraph(
            production_name=self.name,
            nodes=nodes,
            edges=edges,
            warnings=tuple(self._graph_warnings),
        )

    def component_registrations(self) -> tuple[ComponentRef, ...]:
        return tuple(
            item for item in self._items if item.component_class is not None
        )

    def start(self, detach: bool = True) -> None:
        runtime = _ProductionRuntime(self)
        director = runtime.director
        if detach:
            director.start_production(self.name)
        else:
            director.start_production_with_log(self.name)

    def stop(self) -> None:
        _ProductionRuntime(self).director.stop_production()

    def restart(self) -> None:
        _ProductionRuntime(self).director.restart_production()

    def kill(self) -> None:
        _ProductionRuntime(self).director.shutdown_production()

    def status(self) -> dict:
        return _ProductionRuntime(self).director.status_production()

    def queue(self, *, refresh: bool = True) -> dict[str, dict[str, Any]]:
        if not refresh:
            return {name: dict(value) for name, value in self._queue_info.items()}
        info = _ProductionRuntime(self).director.export_production_queue_info(self.name)
        queue_map, warnings = _normalize_queue_info(info)
        self._graph_warnings.extend(warnings)
        self._queue_info = queue_map
        return {name: dict(value) for name, value in queue_map.items()}

    def queue_info(self, *, refresh: bool = True) -> dict[str, dict[str, Any]]:
        return self.queue(refresh=refresh)

    def update(self) -> None:
        _ProductionRuntime(self).director.update_production()

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

        _Utils.set_productions_settings([self], root_path)
        if update:
            from ._local import _LocalDirector

            if self.namespace:
                os.environ["IRISNAMESPACE"] = self.namespace
            _LocalDirector().update_production()

    def apply(self, *, root_path: Optional[str] = None, update: bool = True) -> None:
        self.sync(root_path=root_path, update=update)

    def log(self, top: Optional[int] = None) -> None:
        director = _ProductionRuntime(self).director
        if top is None:
            director.log_production()
        else:
            director.log_production_top(top)

    def test(
        self,
        target_or_port: str | Port | ComponentRef,
        message: Any = None,
        classname: Optional[str] = None,
        body: str | dict | None = None,
    ) -> Any:
        runtime = _ProductionRuntime(self)
        director = runtime.director
        try:
            target_name = self.resolve_target(target_or_port)
        except ValueError:
            if isinstance(target_or_port, str) and "." in target_or_port:
                target_name = self._resolve_target_from_export(director, target_or_port)
            else:
                raise

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

    def _resolve_target_from_export(self, director: Any, target_path: str) -> str:
        item_name, _, port_name = target_path.rpartition(".")
        exported = director.export_production(self.name)
        production_data = exported.get(self.name) if isinstance(exported, dict) else None
        if production_data is None and isinstance(exported, dict) and len(exported) == 1:
            production_data = next(iter(exported.values()))
        if not isinstance(production_data, dict):
            raise ValueError(f"Production does not exist or cannot be exported: {self.name}")

        item = _find_named_entry(production_data.get("Item", []), item_name)
        if item is None:
            raise ValueError(
                f"Production item does not exist in {self.name}: {item_name}"
            )

        setting = _find_setting(item.get("Setting", []), port_name)
        if setting is None:
            raise ValueError(
                f"Production port is not connected in {self.name}: {target_path}"
            )
        target_name = setting.get("#text", "")
        if not target_name:
            raise ValueError(
                f"Production port is not connected in {self.name}: {target_path}"
            )
        return target_name

    def _raise_if_existing_production_not_running(self, director: Any) -> None:
        try:
            status = director.status_production()
        except Exception:
            return
        if not isinstance(status, dict):
            return

        production_name = status.get("Production") or status.get("production") or ""
        state = status.get("Status") or status.get("status") or ""
        state_lower = str(state).lower()
        if production_name == self.name and str(state).lower() == "running":
            return

        try:
            productions = director.list_productions()
        except Exception:
            productions = {}
        if isinstance(productions, dict) and self.name in productions:
            if production_name and production_name != self.name and state_lower == "running":
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
                detail = "it is not the running production"
            raise RuntimeError(
                f"Production {self.name!r} exists but is not running ({detail}). "
                f"Start it with `iop --start {self.name} --detach` or "
                "`prod.start()` before calling `prod.test(...)`."
            )

    def _switch_running_production_message(self, current_production: str) -> str:
        return (
            f"IRIS can run only one production at a time. Stop {current_production!r} "
            f"first with `iop --stop`, then start {self.name!r} with "
            f"`iop --start {self.name} --detach`; or call `prod.stop()` and "
            "`prod.start()` explicitly."
        )

    def _component_name(self, target_component: ComponentRef | str) -> str:
        if isinstance(target_component, ComponentRef):
            if target_component.production is not self:
                raise ValueError("target component belongs to a different Production")
            return target_component.name
        target_name = str(target_component)
        if target_name not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {target_name}")
        return target_name

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
        self._items.append(ref)
        self._items_by_name[ref.name] = ref

    def _register_connection(
        self,
        source_item: str,
        source_port: str,
        target_name: str,
        *,
        logical_name: str = "",
        runtime: bool = False,
        inferred: bool = False,
        validate_target: bool = True,
    ) -> None:
        if source_item not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {source_item}")
        if validate_target and target_name not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {target_name}")
        if source_port:
            self._connections[(source_item, source_port)] = target_name

        source = f"{source_item}.{source_port}" if source_port else source_item
        edge: dict[str, Any] = {
            "source": source,
            "source_item": source_item,
            "source_port": source_port,
            "logical_name": logical_name,
            "target": target_name,
        }
        if runtime:
            edge["runtime"] = True
        if inferred:
            edge["inferred"] = True

        self._edges = [
            existing
            for existing in self._edges
            if not (
                existing.get("source_item") == source_item
                and existing.get("source_port") == source_port
                and (source_port or existing.get("target") == target_name)
            )
        ]
        self._edges.append(edge)


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


def _find_named_entry(entries: Any, name: str) -> Optional[dict[str, Any]]:
    for entry in _as_list(entries):
        if isinstance(entry, dict) and entry.get("@Name") == name:
            return entry
    return None


def _find_setting(settings: Any, name: str) -> Optional[dict[str, Any]]:
    for setting in _as_list(settings):
        if not isinstance(setting, dict):
            continue
        if setting.get("@Name") != name:
            continue
        if setting.get("@Target", "Host") not in ("", "Host"):
            continue
        return setting
    return None


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
) -> tuple[dict[str, list[dict[str, str]]], set[str], list[str]]:
    connection_map: dict[str, list[dict[str, str]]] = {}
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
                if not item_warnings:
                    runtime_sources.add(source)
                for target in _as_list(item.get("connections")):
                    normalized = _normalize_connection_target(target)
                    if normalized is not None:
                        connection_map.setdefault(source, []).append(normalized)
                for edge in _as_list(item.get("edges")):
                    normalized = _normalize_connection_target(edge)
                    if normalized is not None:
                        connection_map.setdefault(source, []).append(normalized)
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


def _normalize_connection_target(value: Any) -> Optional[dict[str, str]]:
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
    return {"target": str(target), "source_port": str(source_port)}


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
            os.environ["IRISNAMESPACE"] = self.production.namespace
        return _LocalDirector()
