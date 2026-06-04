from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol

from .common import SETTING_NAME_ALIASES
from .types import TargetSetting


class _NamedRouteTarget(Protocol):
    @property
    def name(self) -> str: ...


@dataclass(frozen=True)
class Route:
    """Declarative route from a target setting to one or more targets."""

    target_setting: str | TargetSetting
    targets: str | _NamedRouteTarget | Iterable[str | _NamedRouteTarget]

    @property
    def target_setting_name(self) -> str:
        return normalize_route_target_setting(self.target_setting)

    @property
    def target_setting_owner(self) -> type | None:
        if isinstance(self.target_setting, TargetSetting):
            return self.target_setting.owner
        return None

    @property
    def target_names(self) -> tuple[str, ...]:
        if _is_route_target(self.targets):
            targets = (self.targets,)
        else:
            try:
                targets = tuple(self.targets)
            except TypeError as exc:
                raise TypeError(
                    f"Route {self.target_setting_name!r} targets must be an item name, "
                    "a production item declaration, or an iterable of either"
                ) from exc
        if not targets:
            raise ValueError(
                f"Route {self.target_setting_name!r} requires at least one target"
            )
        return tuple(
            _route_target_name(target, self.target_setting_name)
            for target in targets
        )


@dataclass(frozen=True)
class _ProductionItemDeclaration:
    name: str
    component: type | str | None = None
    class_name: str | None = None
    adapter_class: type | str | None = None
    adapter_class_name: str | None = None
    enabled: bool | str = True
    pool_size: int | str = 1
    category: str = ""
    foreground: bool | str = False
    comment: str = ""
    log_trace_events: bool | str = False
    schedule: str = ""
    settings: Mapping[str, Any] | None = None
    host_settings: Mapping[str, Any] | None = None
    adapter_settings: Mapping[str, Any] | None = None
    other_settings: Iterable[Mapping[str, Any]] | None = None
    routes: Route | Iterable[Route] | None = field(default_factory=tuple)

    kind: ClassVar[str] = "component"

    @property
    def host_setting_values(self) -> dict[str, Any]:
        settings = _mapping(self.settings, "settings", self.name)
        host_settings = _mapping(self.host_settings, "host_settings", self.name)
        duplicates = sorted(settings.keys() & host_settings.keys())
        if duplicates:
            names = ", ".join(repr(name) for name in duplicates)
            raise ValueError(
                f"{self.kind.title()} item {self.name!r} declares duplicate "
                f"Host setting keys: {names}"
            )
        merged = dict(settings)
        merged.update(host_settings)
        return merged

    @property
    def adapter_setting_values(self) -> dict[str, Any]:
        return _mapping(self.adapter_settings, "adapter_settings", self.name)

    @property
    def other_setting_values(self) -> list[dict[str, Any]]:
        return [dict(setting) for setting in self.other_settings or ()]

    @property
    def route_values(self) -> tuple[Route, ...]:
        if self.routes is None:
            return ()
        if isinstance(self.routes, Route):
            return (self.routes,)
        routes = tuple(self.routes)
        for route in routes:
            if not isinstance(route, Route):
                raise TypeError(
                    f"{self.kind.title()} item {self.name!r} routes must be Route "
                    f"instances"
                )
        return routes


@dataclass(frozen=True)
class ServiceItem(_ProductionItemDeclaration):
    kind: ClassVar[str] = "service"


@dataclass(frozen=True)
class ComponentItem(_ProductionItemDeclaration):
    kind: ClassVar[str] = "component"


@dataclass(frozen=True)
class ProcessItem(_ProductionItemDeclaration):
    kind: ClassVar[str] = "process"


@dataclass(frozen=True)
class OperationItem(_ProductionItemDeclaration):
    kind: ClassVar[str] = "operation"


def normalize_route_target_setting(name: str | TargetSetting) -> str:
    """Normalize known Pythonic route aliases without changing other settings."""

    if isinstance(name, TargetSetting):
        if not name.name:
            raise ValueError(
                "Route target setting must be declared on a component class"
            )
        return name.name
    target_setting_name = str(name)
    return SETTING_NAME_ALIASES.get(target_setting_name, target_setting_name)


def normalize_route_target_setting_for_match(name: str | TargetSetting) -> str:
    return normalize_route_target_setting(name)


def _is_route_target(value: Any) -> bool:
    return isinstance(value, str) or isinstance(value, _ProductionItemDeclaration)


def _route_target_name(value: Any, target_setting_name: str) -> str:
    if isinstance(value, str):
        if value:
            return value
    elif isinstance(value, _ProductionItemDeclaration):
        if value.name:
            return value.name

    raise TypeError(
        f"Route {target_setting_name!r} targets must be item names or production item "
        "declarations"
    )


def _mapping(
    values: Mapping[str, Any] | None,
    field_name: str,
    item_name: str,
) -> dict[str, Any]:
    try:
        return dict(values or {})
    except (TypeError, ValueError) as exc:
        raise TypeError(
            f"Production item {item_name!r} {field_name} must be a mapping"
        ) from exc


__all__ = [
    "ComponentItem",
    "OperationItem",
    "ProcessItem",
    "Route",
    "ServiceItem",
]
