from __future__ import annotations

import json
from dataclasses import is_dataclass
from typing import Any

from pydantic import BaseModel

from ..runtime.protocol import DirectorProtocol as _DirectorProtocol
from .common import (
    _adapter_type_from_component_class,
    _apply_settings_update,
    _auto_proxy_class_name,
    _bool_text,
    _text_value,
)
from .component import ComponentRef
from .diff import _diff_productions
from .import_ import (
    _as_list,
    _is_internal_runtime_target,
    _matching_host_setting,
    _normalize_connections,
    _normalize_queue_info,
    _normalize_runtime_item_metadata,
    _production_payload,
    _setting_targets,
    _split_settings,
)
from .runtime import (
    _has_remote_director,
    _ProductionRuntime,
    _temporary_env,
)
from .types import (
    GraphEdge,
    GraphNode,
    Port,
    ProductionDiff,
    ProductionGraph,
    _edge_identity,
)


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
        namespace: str | None = None,
        director: _DirectorProtocol | None = None,
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

    def testing(self, enabled: bool | str = True) -> Production:
        self.testing_enabled = enabled
        return self

    def tracing(self, enabled: bool | str = True) -> Production:
        self.log_general_trace_events = enabled
        return self

    def actor_pool(self, size: int | str) -> Production:
        self.actor_pool_size = size
        return self

    def describe(self, text: str) -> Production:
        self.description = text
        return self

    def in_namespace(self, namespace: str | None) -> Production:
        self.namespace = namespace
        return self

    def with_director(self, director: _DirectorProtocol | None) -> Production:
        self._director = director
        return self

    @classmethod
    def from_iris(
        cls,
        name: str,
        *,
        namespace: str | None = None,
        director: _DirectorProtocol | None = None,
    ) -> Production:
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
        namespace: str | None = None,
        director: Any = None,
    ) -> Production:
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
    def edges(self) -> tuple[GraphEdge, ...]:
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
        cls: type | None = None,
        *,
        class_name: str | None = None,
        adapter_class: type | str | None = None,
        adapter_class_name: str | None = None,
        kind: str = "component",
        enabled: bool | str = True,
        pool_size: int | str = 1,
        category: str = "",
        foreground: bool | str = False,
        comment: str = "",
        log_trace_events: bool | str = False,
        schedule: str = "",
        settings: dict[str, Any] | None = None,
        adapter_settings: dict[str, Any] | None = None,
    ) -> ComponentRef:
        item_name: str
        component_class: type | None

        if isinstance(name_or_cls, type) and cls is None:
            component_class = name_or_cls
            item_name = component_class.__name__
        else:
            item_name = str(name_or_cls)
            component_class = cls

        if item_name in self._items_by_name:
            raise ValueError(f"Production item already exists: {item_name}")

        adapter_class_ref: type | None = None
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

    def service(self, name_or_cls: str | type, cls: type | None = None, **kwargs):
        return self.component(name_or_cls, cls, kind="service", **kwargs)

    def process(self, name_or_cls: str | type, cls: type | None = None, **kwargs):
        return self.component(name_or_cls, cls, kind="process", **kwargs)

    def operation(self, name_or_cls: str | type, cls: type | None = None, **kwargs):
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
        from ..migration.utils import _Utils

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

    def sync(self, *, root_path: str | None = None, update: bool = True) -> None:
        if _has_remote_director(self):
            raise NotImplementedError(
                "Production.sync() can only register directly with local IRIS. "
                "Use `iop --migrate <settings_file>` for remote migrations."
            )
        from ..migration.utils import _Utils

        with _temporary_env("IRISNAMESPACE", self.namespace):
            _Utils.set_productions_settings([self], root_path)
            if update:
                from ..runtime.local import _LocalDirector

                _LocalDirector().update_production()

    def apply(self, *, root_path: str | None = None, update: bool = True) -> None:
        self.sync(root_path=root_path, update=update)

    def log(self, top: int | None = None) -> None:
        director = _ProductionRuntime(self).director
        if top is None:
            director.log_production()
        else:
            director.log_production_top(top)

    def test_component(
        self,
        target_or_port: str | Port | ComponentRef,
        message: Any = None,
        classname: str | None = None,
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
        classname: str | None = None,
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
        metadata: dict[str, Any] | None = None,
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


def _message_to_classname_body(message: Any) -> tuple[str | None, str | dict | None]:
    classname = f"{message.__class__.__module__}.{message.__class__.__name__}"
    if isinstance(message, BaseModel):
        return classname, message.model_dump_json()
    if is_dataclass(message):
        from ..messages.serialization import dataclass_to_dict

        return classname, json.dumps(dataclass_to_dict(message))
    return None, None
