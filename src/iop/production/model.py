from __future__ import annotations

from typing import Any

from ..runtime.protocol import DirectorProtocol as _DirectorProtocol
from . import actions as _actions
from .common import (
    PRODUCTION_SETTING_FIELDS,
    _adapter_type_from_component_class,
    _apply_settings_update,
    _auto_proxy_class_name,
    _normalize_settings_mapping,
)
from .component import ComponentRef
from .declarative import _DeclarativeProductionMixin
from .diff import _diff_productions
from .inspection import component_runtime_info, inspect_component
from .planning import (
    ProductionApplyResult,
    ProductionChangePlan,
    ProductionVerifyResult,
    build_change_plan,
)
from .reconstruction import production_from_dict
from .rendering import (
    production_graph,
    production_to_class,
    production_to_dict,
    production_to_python,
    production_to_xml,
)
from .runtime import _ProductionRuntime
from .types import (
    GraphEdge,
    PersistentMessageRegistration,
    ProductionDiff,
    ProductionGraph,
    TargetSetting,
    TargetSettingRef,
    _edge_identity,
)

_MISSING = object()


class Production(_DeclarativeProductionMixin):
    """Purpose:
        Python authoring DSL for IRIS interoperability production topology.

    Use when:
        A project should declare services, processes, operations, settings, and
        graph connections in Python.

    Lifecycle:
        A settings.py module exports PRODUCTIONS = [prod]. Migration renders the
        graph to IRIS; IRIS remains the runtime source of truth.

    Best practices:
        Declare topology with service(), process(), operation(), target(), and
        connect(). Keep the Production object import-safe.

    Common mistakes:
        Do not execute migration or runtime side effects at module import time.
        Do not use raw CLASSES entries for graph components.

    Minimal example:
        prod = Production("Demo.Production")
        svc = prod.service("Demo.Service", MyService)
        op = prod.operation("Demo.Operation", MyOperation)
        prod.connect(svc.Output, op)
        PRODUCTIONS = [prod]

    Related:
        docs/cookbooks/hello-world-production.md,
        docs/production-graph.md
    """

    def __init__(
        self,
        name: str | object = _MISSING,
        *,
        testing_enabled: bool | str | object = _MISSING,
        log_general_trace_events: bool | str | object = _MISSING,
        actor_pool_size: int | str | object = _MISSING,
        description: str | object = _MISSING,
        shutdown_timeout: int | str | object = _MISSING,
        update_timeout: int | str | object = _MISSING,
        alert_notification_manager: str | object = _MISSING,
        alert_notification_operation: str | object = _MISSING,
        alert_notification_recipients: str | object = _MISSING,
        alert_action_window: int | str | object = _MISSING,
        namespace: str | None | object = _MISSING,
        director: _DirectorProtocol | None | object = _MISSING,
    ):
        self._initialize(
            name,
            testing_enabled=testing_enabled,
            log_general_trace_events=log_general_trace_events,
            actor_pool_size=actor_pool_size,
            description=description,
            shutdown_timeout=shutdown_timeout,
            update_timeout=update_timeout,
            alert_notification_manager=alert_notification_manager,
            alert_notification_operation=alert_notification_operation,
            alert_notification_recipients=alert_notification_recipients,
            alert_action_window=alert_action_window,
            namespace=namespace,
            director=director,
            hydrate_declarations=True,
        )

    @classmethod
    def _new_unhydrated(
        cls,
        name: str | object = _MISSING,
        *,
        testing_enabled: bool | str | object = _MISSING,
        log_general_trace_events: bool | str | object = _MISSING,
        actor_pool_size: int | str | object = _MISSING,
        description: str | object = _MISSING,
        shutdown_timeout: int | str | object = _MISSING,
        update_timeout: int | str | object = _MISSING,
        alert_notification_manager: str | object = _MISSING,
        alert_notification_operation: str | object = _MISSING,
        alert_notification_recipients: str | object = _MISSING,
        alert_action_window: int | str | object = _MISSING,
        namespace: str | None | object = _MISSING,
        director: _DirectorProtocol | None | object = _MISSING,
    ) -> Production:
        production = object.__new__(cls)
        Production._initialize(
            production,
            name,
            testing_enabled=testing_enabled,
            log_general_trace_events=log_general_trace_events,
            actor_pool_size=actor_pool_size,
            description=description,
            shutdown_timeout=shutdown_timeout,
            update_timeout=update_timeout,
            alert_notification_manager=alert_notification_manager,
            alert_notification_operation=alert_notification_operation,
            alert_notification_recipients=alert_notification_recipients,
            alert_action_window=alert_action_window,
            namespace=namespace,
            director=director,
            hydrate_declarations=False,
        )
        return production

    def _initialize(
        self,
        name: str | object = _MISSING,
        *,
        testing_enabled: bool | str | object = _MISSING,
        log_general_trace_events: bool | str | object = _MISSING,
        actor_pool_size: int | str | object = _MISSING,
        description: str | object = _MISSING,
        shutdown_timeout: int | str | object = _MISSING,
        update_timeout: int | str | object = _MISSING,
        alert_notification_manager: str | object = _MISSING,
        alert_notification_operation: str | object = _MISSING,
        alert_notification_recipients: str | object = _MISSING,
        alert_action_window: int | str | object = _MISSING,
        namespace: str | None | object = _MISSING,
        director: _DirectorProtocol | None | object = _MISSING,
        hydrate_declarations: bool,
    ) -> None:
        self.name = self._resolve_production_name(name)
        self.testing_enabled = self._production_default(
            "testing_enabled", testing_enabled, False
        )
        self.log_general_trace_events = self._production_default(
            "log_general_trace_events", log_general_trace_events, False
        )
        self.actor_pool_size = self._production_default(
            "actor_pool_size", actor_pool_size, 2
        )
        self.description = self._production_default("description", description, "")
        self.shutdown_timeout = self._production_default(
            "shutdown_timeout",
            shutdown_timeout,
            PRODUCTION_SETTING_FIELDS["shutdown_timeout"][1],
        )
        self.update_timeout = self._production_default(
            "update_timeout",
            update_timeout,
            PRODUCTION_SETTING_FIELDS["update_timeout"][1],
        )
        self.alert_notification_manager = self._production_default(
            "alert_notification_manager",
            alert_notification_manager,
            PRODUCTION_SETTING_FIELDS["alert_notification_manager"][1],
        )
        self.alert_notification_operation = self._production_default(
            "alert_notification_operation",
            alert_notification_operation,
            PRODUCTION_SETTING_FIELDS["alert_notification_operation"][1],
        )
        self.alert_notification_recipients = self._production_default(
            "alert_notification_recipients",
            alert_notification_recipients,
            PRODUCTION_SETTING_FIELDS["alert_notification_recipients"][1],
        )
        self.alert_action_window = self._production_default(
            "alert_action_window",
            alert_action_window,
            PRODUCTION_SETTING_FIELDS["alert_action_window"][1],
        )
        self.namespace = self._production_default("namespace", namespace, None)
        self._director = self._production_default("director", director, None)
        self._items: list[ComponentRef] = []
        self._items_by_name: dict[str, ComponentRef] = {}
        self._connections: dict[tuple[str, str], list[str]] = {}
        self._edges: list[GraphEdge] = []
        self._graph_warnings: list[str] = []
        self._queue_info: dict[str, dict[str, Any]] = {}
        self._messages: list[PersistentMessageRegistration] = []
        if hydrate_declarations:
            self._hydrate_declared_items()

    def _resolve_production_name(self, name: str | object) -> str:
        if name is not _MISSING:
            return str(name)
        class_name = getattr(type(self), "name", _MISSING)
        if class_name is not _MISSING:
            return str(class_name)
        return f"{type(self).__module__}.{type(self).__name__}"

    def _production_default(
        self,
        field_name: str,
        explicit: Any,
        default: Any,
    ) -> Any:
        if explicit is not _MISSING:
            return explicit
        class_value = getattr(type(self), field_name, _MISSING)
        if class_value is not _MISSING:
            return class_value
        return default

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

    def timeouts(
        self,
        *,
        shutdown: int | str | None = None,
        update: int | str | None = None,
    ) -> Production:
        if shutdown is not None:
            self.shutdown_timeout = shutdown
        if update is not None:
            self.update_timeout = update
        return self

    def alerting(
        self,
        *,
        manager: str | None = None,
        operation: str | None = None,
        recipients: str | None = None,
        action_window: int | str | None = None,
    ) -> Production:
        if manager is not None:
            self.alert_notification_manager = manager
        if operation is not None:
            self.alert_notification_operation = operation
        if recipients is not None:
            self.alert_notification_recipients = recipients
        if action_window is not None:
            self.alert_action_window = action_window
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
        seed = cls._new_unhydrated(
            name,
            namespace=namespace,
            director=director,
        )
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
        return production_from_dict(
            cls,
            data,
            connections=connections,
            queue_info=queue_info,
            namespace=namespace,
            director=director,
        )

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

    def component_ref(
        self,
        component: ComponentRef | TargetSettingRef | str,
    ) -> ComponentRef:
        component_name = self._runtime_component_name(component)
        return self.item(component_name)

    def get_component(
        self,
        component: ComponentRef | TargetSettingRef | str,
    ) -> ComponentRef:
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
            host_settings=_normalize_settings_mapping(settings),
            adapter_settings=_normalize_settings_mapping(adapter_settings),
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
        if "target_settings" in kwargs:
            ref.target_setting_names.update(
                str(value) for value in kwargs.pop("target_settings")
            )

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
            source_target_setting = edge.source_target_setting
            source_ref = self._items_by_name.get(source_item)
            if source_ref is not None and source_target_setting:
                if source_ref.host_settings.get(source_target_setting) == ref.name:
                    source_ref.host_settings.pop(source_target_setting, None)

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

    def disconnect(self, source: TargetSettingRef | str) -> None:
        if isinstance(source, TargetSettingRef):
            if source.production is not self:
                raise ValueError(
                    "source target setting belongs to a different Production"
                )
            item_name = source.item_name
            target_setting_name = source.name
        else:
            item_name, separator, target_setting_name = str(source).rpartition(".")
            if not separator:
                raise ValueError(
                    "source must be a TargetSettingRef or an "
                    "Item.TargetSetting string"
                )

        key = (item_name, target_setting_name)
        if key not in self._connections:
            raise ValueError(
                "Production target setting is not connected: "
                f"{item_name}.{target_setting_name}"
            )
        self._connections.pop(key, None)
        ref = self.item(item_name)
        ref.host_settings.pop(target_setting_name, None)
        self._edges = [
            edge
            for edge in self._edges
            if not (
                edge.source_item == item_name
                and edge.source_target_setting == target_setting_name
            )
        ]

    def service(
        self,
        name_or_cls: str | type,
        cls: type | None = None,
        **kwargs: Any,
    ) -> ComponentRef:
        """Add a BusinessService item to the production graph.

        See docs/cookbooks/hello-world-production.md and
        docs/cookbooks/hl7v2-native-input.md.
        """
        return self.component(name_or_cls, cls, kind="service", **kwargs)

    def process(
        self,
        name_or_cls: str | type,
        cls: type | None = None,
        **kwargs: Any,
    ) -> ComponentRef:
        """Add a BusinessProcess item to the production graph.

        See docs/cookbooks/add-business-process.md.
        """
        return self.component(name_or_cls, cls, kind="process", **kwargs)

    def operation(
        self,
        name_or_cls: str | type,
        cls: type | None = None,
        **kwargs: Any,
    ) -> ComponentRef:
        """Add a BusinessOperation item to the production graph.

        See docs/cookbooks/add-business-operation.md.
        """
        return self.component(name_or_cls, cls, kind="operation", **kwargs)

    def message(
        self,
        iris_classname: str,
        msg_cls: type,
        *,
        sync_schema: bool = True,
    ) -> Production:
        from ..messages.persistent import (
            get_python_classname,
            is_persistent_message_class,
        )

        iris_classname = str(iris_classname or "").strip()
        if not iris_classname:
            raise ValueError("PersistentMessage IRIS classname is required")
        if not is_persistent_message_class(msg_cls):
            raise TypeError("msg_cls must be a concrete PersistentMessage subclass")

        python_classname = get_python_classname(msg_cls)
        for registration in self._messages:
            registered_python_classname = get_python_classname(
                registration.message_class
            )
            if registration.iris_classname == iris_classname:
                if registered_python_classname != python_classname:
                    raise ValueError(
                        "PersistentMessage IRIS classname already registered: "
                        f"{iris_classname}"
                    )
                if registration.sync_schema != bool(sync_schema):
                    raise ValueError(
                        "PersistentMessage registration has conflicting sync_schema "
                        f"for {iris_classname}"
                    )
                return self
            if registered_python_classname == python_classname:
                raise ValueError(
                    "PersistentMessage class already registered with IRIS classname "
                    f"{registration.iris_classname}"
                )

        self._messages.append(
            PersistentMessageRegistration(
                iris_classname=iris_classname,
                message_class=msg_cls,
                sync_schema=bool(sync_schema),
            )
        )
        return self

    def connect(
        self,
        source: TargetSettingRef,
        target_component: ComponentRef | str | None = None,
        *,
        mode: str = "replace",
    ) -> None:
        if not isinstance(source, TargetSettingRef):
            if isinstance(source, TargetSetting):
                raise TypeError(
                    "source must be bound to a production item. Use "
                    "component.connect(ComponentClass.Target, target_component) "
                    "or prod.connect(component.Target, target_component)."
                )
            raise TypeError(
                "source must be a TargetSettingRef returned from a ComponentRef"
            )
        if source.production is not self:
            raise ValueError("source target setting belongs to a different Production")

        mode = _connection_mode(mode)
        if mode == "remove":
            self._remove_connection(source, target_component)
            return
        if target_component is None:
            raise ValueError("target_component is required unless mode='remove'")

        target_name = self._component_name(target_component)
        if mode == "replace":
            source.component.set_host_setting(source.name, target_name)
        else:
            existing = source.component.host_settings.get(source.name, "")
            existing_targets = [t.strip() for t in existing.split(",") if t.strip()]
            if target_name not in existing_targets:
                source.component.host_settings[source.name] = ",".join(
                    existing_targets + [target_name]
                )
        source.component.target_setting_names.add(source.name)
        self._register_connection(
            source.item_name,
            source.name,
            target_name,
            replace_target_setting=mode == "replace",
        )

    def _remove_connection(
        self,
        source: TargetSettingRef,
        target_component: ComponentRef | str | None,
    ) -> None:
        if target_component is None:
            self.disconnect(source)
            return

        target_name = self._component_name(target_component)
        key = (source.item_name, source.name)
        targets = self._connections.get(key, [])
        edge_exists = any(
            edge.source_item == source.item_name
            and edge.source_target_setting == source.name
            and edge.target == target_name
            for edge in self._edges
        )
        if target_name not in targets and not edge_exists:
            raise ValueError(
                "Production target setting is not connected: "
                f"{source.path} -> {target_name}"
            )

        remaining_targets = [target for target in targets if target != target_name]
        if remaining_targets:
            self._connections[key] = remaining_targets
            source.component.host_settings[source.name] = ",".join(remaining_targets)
        else:
            self._connections.pop(key, None)
            source.component.host_settings.pop(source.name, None)

        self._edges = [
            edge
            for edge in self._edges
            if not (
                edge.source_item == source.item_name
                and edge.source_target_setting == source.name
                and edge.target == target_name
            )
        ]

    def resolve_target_setting_ref(self, target_setting_ref: TargetSettingRef) -> str:
        if target_setting_ref.production is not self:
            raise ValueError(
                "target setting ref belongs to a different Production"
            )
        return self._resolve_connection_target(
            target_setting_ref.item_name,
            target_setting_ref.name,
            target_setting_ref.path,
        )

    def _resolve_connection_target(
        self,
        item_name: str,
        target_setting_name: str,
        path: str,
    ) -> str:
        key = (item_name, target_setting_name)
        targets = self._connections.get(key)
        if not targets:
            raise ValueError(f"Production target setting is not connected: {path}")
        if len(targets) > 1:
            target_list = ", ".join(repr(target) for target in targets)
            raise ValueError(
                f"Production target setting is ambiguous: {path} resolves to "
                f"multiple targets ({target_list})"
            )
        return targets[0]

    def resolve_target(
        self,
        target_or_ref: str | TargetSettingRef | ComponentRef,
    ) -> str:
        if isinstance(target_or_ref, TargetSettingRef):
            return self.resolve_target_setting_ref(target_or_ref)
        if isinstance(target_or_ref, ComponentRef):
            return self._component_name(target_or_ref)

        target_name = str(target_or_ref)
        if target_name in self._items_by_name:
            return target_name

        if "." in target_name:
            item_name, _, target_setting_name = target_name.rpartition(".")
            if item_name not in self._items_by_name:
                raise ValueError(f"Production item does not exist: {item_name}")
            key = (item_name, target_setting_name)
            if key not in self._connections:
                raise ValueError(
                    f"Production target setting is not connected: {target_name}"
                )
            return self._resolve_connection_target(
                item_name,
                target_setting_name,
                target_name,
            )

        raise ValueError(f"Production item does not exist: {target_name}")

    def to_dict(self) -> dict[str, Any]:
        return production_to_dict(self)

    def to_xml(self) -> str:
        return production_to_xml(self)

    def to_python(self) -> str:
        return production_to_python(self)

    def to_class(self) -> str:
        return production_to_class(self)

    def to_mermaid(self, *, direction: str = "LR") -> str:
        return self.graph().to_mermaid(direction=direction)

    def graph(self) -> ProductionGraph:
        return production_graph(self)

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

    def plan(
        self,
        other: Production | dict[str, Any] | None = None,
    ) -> ProductionChangePlan:
        """Build a conservative granular change plan against current/imported state."""
        current = self._diff_current(other)
        return build_change_plan(self, current)

    def component_registrations(self) -> tuple[ComponentRef, ...]:
        return tuple(
            item for item in self._items if item.component_class is not None
        )

    def adapter_registrations(self) -> tuple[ComponentRef, ...]:
        return tuple(
            item for item in self._items if item.adapter_class is not None
        )

    def message_registrations(self) -> tuple[PersistentMessageRegistration, ...]:
        return tuple(self._messages)

    def validate(self, *, strict: bool = False):
        from .validation import validate_production

        return validate_production(self, strict=strict, warn=not strict)

    def start(self, detach: bool = True) -> None:
        _actions.start(self, detach=detach)

    def stop(self) -> None:
        _actions.stop(self)

    def restart(self) -> None:
        _actions.restart(self)

    def kill(self) -> None:
        _actions.kill(self)

    def status(self) -> dict:
        return _actions.status(self)

    def queue(self, *, refresh: bool = True) -> dict[str, dict[str, Any]]:
        return _actions.queue(self, refresh=refresh)

    def queue_info(self, *, refresh: bool = True) -> dict[str, dict[str, Any]]:
        return self.queue(refresh=refresh)

    def update(self) -> None:
        _actions.update(self)

    def inspect_component(
        self,
        component: ComponentRef | TargetSettingRef | str,
        *,
        refresh: bool = True,
    ) -> dict[str, Any]:
        return inspect_component(self, component, refresh=refresh)

    def start_component(self, component: ComponentRef | TargetSettingRef | str) -> None:
        _actions.start_component(self, component)

    def stop_component(self, component: ComponentRef | TargetSettingRef | str) -> None:
        _actions.stop_component(self, component)

    def restart_component(
        self,
        component: ComponentRef | TargetSettingRef | str,
    ) -> None:
        _actions.restart_component(self, component)

    def export(self) -> dict:
        return _actions.export(self)

    def set_default(self) -> None:
        _actions.set_default(self)

    def sync(self, *, root_path: str | None = None, update: bool = True) -> None:
        _actions.sync(self, root_path=root_path, update_runtime=update)

    def apply(
        self,
        plan: ProductionChangePlan | None = None,
        *,
        allow_destructive: bool = False,
        backup_dir: str = ".iop/backups",
        root_path: str | None = None,
        update: bool = True,
    ) -> ProductionApplyResult:
        return _actions.apply(
            self,
            plan=plan,
            allow_destructive=allow_destructive,
            backup_dir=backup_dir,
            root_path=root_path,
            update_runtime=update,
        )

    def verify(self, plan: ProductionChangePlan) -> ProductionVerifyResult:
        return _actions.verify(self, plan)

    @staticmethod
    def rollback_backup(
        backup_path: str,
        *,
        director: _DirectorProtocol | None = None,
        namespace: str | None = None,
        allow_destructive: bool = False,
        update: bool = True,
    ) -> ProductionVerifyResult:
        return _actions.rollback_backup(
            backup_path,
            director=director,
            namespace=namespace,
            allow_destructive=allow_destructive,
            update_runtime=update,
        )

    def log(self, top: int | None = None) -> None:
        _actions.log(self, top)

    def test_component(
        self,
        target_or_ref: str | TargetSettingRef | ComponentRef,
        message: Any = None,
        classname: str | None = None,
        body: str | dict | None = None,
    ) -> Any:
        return _actions.test_component(
            self,
            target_or_ref,
            message=message,
            classname=classname,
            body=body,
        )

    def test(
        self,
        target_or_ref: str | TargetSettingRef | ComponentRef,
        message: Any = None,
        classname: str | None = None,
        body: str | dict | None = None,
    ) -> Any:
        return self.test_component(
            target_or_ref,
            message=message,
            classname=classname,
            body=body,
        )

    def _raise_if_existing_production_not_running(self, director: Any) -> None:
        _actions.raise_if_existing_production_not_running(self, director)

    def _require_current_production(self, director: Any, action: str) -> None:
        _actions.require_current_production(self, director, action)

    def _require_current_runtime(self, director: Any, action: str) -> None:
        _actions.require_current_runtime(self, director, action)

    def _read_status(self, director: Any, action: str) -> tuple[str, str]:
        return _actions.read_status(self, director, action)

    def _switch_running_production_message(self, current_production: str) -> str:
        return _actions.switch_running_production_message(self, current_production)

    def _component_runtime_info(self, component_name: str) -> dict[str, Any]:
        return component_runtime_info(self, component_name)

    def _component_name(self, target_component: ComponentRef | str) -> str:
        if isinstance(target_component, ComponentRef):
            if target_component.production is not self:
                raise ValueError("target component belongs to a different Production")
            return target_component.name
        target_name = str(target_component)
        if target_name not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {target_name}")
        return target_name

    def _runtime_component_name(
        self,
        component: ComponentRef | TargetSettingRef | str,
    ) -> str:
        if isinstance(component, TargetSettingRef):
            component_name = self.resolve_target_setting_ref(component)
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
        self._apply_target_defaults()

    def _apply_target_defaults(self) -> None:
        for ref in self._items:
            for setting_name, target_name in self._target_default_routes(ref):
                if setting_name not in ref.host_settings:
                    if setting_name in ref.target_setting_names:
                        continue
                    ref.host_settings[setting_name] = target_name
                ref.target_setting_names.add(setting_name)
                if str(ref.host_settings[setting_name]) != target_name:
                    continue
                if target_name not in self._items_by_name:
                    continue
                self._register_connection(
                    ref.name,
                    setting_name,
                    target_name,
                )

    def _target_default_routes(self, ref: ComponentRef) -> tuple[tuple[str, str], ...]:
        if ref.component_class is None:
            return ()
        routes: list[tuple[str, str]] = []
        for setting_name, descriptor in _target_settings(ref.component_class):
            target_name = _target_default_name(descriptor.default)
            if target_name:
                routes.append((setting_name, target_name))
        return tuple(routes)

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
        source_target_setting: str,
        target_name: str,
        *,
        origin: str = "authored",
        interaction: str = "request",
        metadata: dict[str, Any] | None = None,
        replace_target_setting: bool = False,
        validate_target: bool = True,
    ) -> None:
        if source_item not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {source_item}")
        if validate_target and target_name not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {target_name}")
        if source_target_setting:
            key = (source_item, source_target_setting)
            if replace_target_setting:
                self._connections[key] = [target_name]
            else:
                self._connections.setdefault(key, [])
                if target_name not in self._connections[key]:
                    self._connections[key].append(target_name)

        edge = GraphEdge(
            source_item=source_item,
            source_target_setting=source_target_setting,
            target=target_name,
            origin=origin,
            interaction=interaction,
            metadata=dict(metadata or {}),
        )

        if replace_target_setting and source_target_setting:
            self._edges = [
                existing
                for existing in self._edges
                if not (
                    existing.source_item == source_item
                    and existing.source_target_setting == source_target_setting
                )
            ]

        edge_key = _edge_identity(edge)
        self._edges = [
            existing
            for existing in self._edges
            if _edge_identity(existing) != edge_key
        ]
        self._edges.append(edge)


def _connection_mode(mode: str) -> str:
    normalized = str(mode or "").strip().lower()
    if normalized in {"replace", "set"}:
        return "replace"
    if normalized in {"add", "append"}:
        return "add"
    if normalized in {"remove", "delete", "disconnect"}:
        return "remove"
    raise ValueError(
        "Unsupported connection mode: "
        f"{mode!r}. Expected 'replace', 'add', or 'remove'."
    )


def _target_settings(
    component_class: type,
) -> tuple[tuple[str, TargetSetting], ...]:
    descriptors: dict[str, TargetSetting] = {}
    for base in reversed(component_class.__mro__):
        for name, value in base.__dict__.items():
            if isinstance(value, TargetSetting):
                descriptors[name] = value
    return tuple(descriptors.items())


def _target_default_name(value: Any) -> str:
    if value is None:
        return ""
    name = getattr(value, "name", value)
    return str(name).strip()
