from __future__ import annotations

from collections.abc import Iterable
from typing import Any, ClassVar, Protocol, cast

from .component import ComponentRef
from .declarations import (
    Route,
    _ProductionItemDeclaration,
    normalize_route_target_setting_for_match,
)
from .types import TargetSettingRef


class _ComponentFactory(Protocol):
    def __call__(
        self,
        name_or_cls: str | type,
        cls: type | None = None,
        **kwargs: Any,
    ) -> ComponentRef: ...


class _DeclarativeProductionHost(Protocol):
    def component(
        self,
        name_or_cls: str | type,
        cls: type | None = None,
        **kwargs: Any,
    ) -> ComponentRef: ...

    def service(
        self,
        name_or_cls: str | type,
        cls: type | None = None,
        **kwargs: Any,
    ) -> ComponentRef: ...

    def process(
        self,
        name_or_cls: str | type,
        cls: type | None = None,
        **kwargs: Any,
    ) -> ComponentRef: ...

    def operation(
        self,
        name_or_cls: str | type,
        cls: type | None = None,
        **kwargs: Any,
    ) -> ComponentRef: ...

    def item(self, name: str) -> ComponentRef: ...

    def connect(
        self,
        source: TargetSettingRef,
        target_component: ComponentRef | str | None = None,
        *,
        mode: str = "replace",
    ) -> None: ...


class _DeclarativeProductionMixin:
    components: ClassVar[Iterable[_ProductionItemDeclaration] | None] = ()
    services: ClassVar[Iterable[_ProductionItemDeclaration] | None] = ()
    processes: ClassVar[Iterable[_ProductionItemDeclaration] | None] = ()
    operations: ClassVar[Iterable[_ProductionItemDeclaration] | None] = ()

    def _hydrate_declared_items(self) -> None:
        declarations: list[_ProductionItemDeclaration] = []
        for attr_name, expected_kind in (
            ("components", "component"),
            ("services", "service"),
            ("processes", "process"),
            ("operations", "operation"),
        ):
            for declaration in self._declared_items(attr_name):
                if declaration.kind != expected_kind:
                    raise TypeError(
                        f"{attr_name} must contain {expected_kind.title()}Item "
                        f"declarations"
                    )
                self._raise_declared_route_conflicts(declaration)
                self._add_declared_item(declaration)
                declarations.append(declaration)

        for declaration in declarations:
            self._connect_declared_routes(declaration)

    def _declared_items(self, attr_name: str) -> tuple[_ProductionItemDeclaration, ...]:
        values: object = getattr(type(self), attr_name, ())
        if values is None:
            return ()
        if isinstance(values, _ProductionItemDeclaration):
            return (values,)
        try:
            declarations = tuple(cast(Iterable[object], values))
        except TypeError as exc:
            raise TypeError(f"{attr_name} must be an iterable of item declarations") from exc
        items: list[_ProductionItemDeclaration] = []
        for declaration in declarations:
            if not isinstance(declaration, _ProductionItemDeclaration):
                raise TypeError(f"{attr_name} must contain production item declarations")
            items.append(declaration)
        return tuple(items)

    def _raise_declared_route_conflicts(
        self,
        declaration: _ProductionItemDeclaration,
    ) -> None:
        host_target_settings = {
            normalize_route_target_setting_for_match(name)
            for name in declaration.host_setting_values
        }
        route_target_settings = {
            route.target_setting_name for route in declaration.route_values
        }
        conflicts = sorted(host_target_settings & route_target_settings)
        if not conflicts:
            return
        names = ", ".join(repr(name) for name in conflicts)
        raise ValueError(
            f"{declaration.kind.title()} item {declaration.name!r} declares route "
            "target setting(s) in Host settings: "
            f"{names}. Declare route target settings with Route only."
        )

    def _add_declared_item(self, declaration: _ProductionItemDeclaration) -> None:
        kwargs: dict[str, Any] = {
            "enabled": declaration.enabled,
            "pool_size": declaration.pool_size,
            "category": declaration.category,
            "foreground": declaration.foreground,
            "comment": declaration.comment,
            "log_trace_events": declaration.log_trace_events,
            "schedule": declaration.schedule,
            "settings": declaration.host_setting_values,
            "adapter_settings": declaration.adapter_setting_values,
        }
        if declaration.adapter_class is not None:
            kwargs["adapter_class"] = declaration.adapter_class
        if declaration.adapter_class_name is not None:
            kwargs["adapter_class_name"] = declaration.adapter_class_name

        host = cast(_DeclarativeProductionHost, self)
        methods: dict[str, _ComponentFactory] = {
            "component": host.component,
            "service": host.service,
            "process": host.process,
            "operation": host.operation,
        }
        method = methods[declaration.kind]

        component = declaration.component
        if isinstance(component, type):
            if declaration.class_name is not None:
                kwargs["class_name"] = declaration.class_name
            ref = method(declaration.name, component, **kwargs)
            ref.other_settings = declaration.other_setting_values
            return

        class_name = declaration.class_name
        if component is not None:
            component_class_name = str(component)
            if class_name is not None and class_name != component_class_name:
                raise ValueError(
                    f"{declaration.kind.title()} item {declaration.name!r} "
                    "declares conflicting component and class_name values"
                )
            class_name = component_class_name

        if class_name is None:
            raise ValueError(
                f"{declaration.kind.title()} item {declaration.name!r} requires "
                "a component class or class_name"
            )
        kwargs["class_name"] = class_name
        ref = method(declaration.name, **kwargs)
        ref.other_settings = declaration.other_setting_values

    def _connect_declared_routes(self, declaration: _ProductionItemDeclaration) -> None:
        host = cast(_DeclarativeProductionHost, self)
        source = host.item(declaration.name)
        for route in declaration.route_values:
            self._raise_if_route_target_setting_owner_mismatch(source, route)
            target_setting_ref = source.target_setting(route.target_setting_name)
            targets = route.target_names
            host.connect(target_setting_ref, targets[0])
            for target in targets[1:]:
                host.connect(
                    target_setting_ref,
                    target,
                    mode="add",
                )

    def _raise_if_route_target_setting_owner_mismatch(
        self,
        source: ComponentRef,
        route: Route,
    ) -> None:
        owner = route.target_setting_owner
        if (
            owner is None
            or source.component_class is None
            or issubclass(source.component_class, owner)
        ):
            return
        raise ValueError(
            f"Route target setting {route.target_setting_name!r} belongs to "
            f"{owner.__module__}.{owner.__qualname__}, not "
            f"{source.component_class.__module__}."
            f"{source.component_class.__qualname__}"
        )
