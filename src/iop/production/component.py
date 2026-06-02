from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .common import (
    _adapter_type_from_class_name,
    _adapter_type_from_component_class,
    _apply_settings_update,
    _auto_proxy_class_name,
    _bool_text,
    _settings_to_iris,
    _text_value,
)
from .types import Port, TargetSetting


@dataclass
class ComponentRef:
    """Reference to a component item declared inside a Production."""

    production: Any
    name: str
    component_class: type | None = None
    class_name: str | None = None
    adapter_class: type | None = None
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
        if not logical_name and self.component_class is not None:
            descriptor = getattr(self.component_class, name, None)
            if isinstance(descriptor, TargetSetting):
                logical_name = descriptor.logical_name
        self.port_names.add(name)
        return Port(
            production=self.production,
            component=self,
            name=name,
            logical_name=logical_name,
        )

    def set_host_setting(self, name: str, value: Any) -> None:
        self.host_settings[name] = value

    def pool(self, size: int | str) -> ComponentRef:
        self.pool_size = size
        return self

    def enable(self, enabled: bool | str = True) -> ComponentRef:
        self.enabled = enabled
        return self

    def disable(self) -> ComponentRef:
        return self.enable(False)

    def run_foreground(self, enabled: bool | str = True) -> ComponentRef:
        self.foreground = enabled
        return self

    def trace(self, enabled: bool | str = True) -> ComponentRef:
        self.log_trace_events = enabled
        return self

    def schedule_on(self, schedule: str) -> ComponentRef:
        self.schedule = schedule
        return self

    def comment_as(self, text: str) -> ComponentRef:
        self.comment = text
        return self

    def category_as(self, category: str) -> ComponentRef:
        self.category = category
        return self

    def host_setting(self, name: str, value: Any) -> ComponentRef:
        _apply_settings_update(self.host_settings, {name: value})
        return self

    def host_settings_update(self, values: dict[str, Any]) -> ComponentRef:
        _apply_settings_update(self.host_settings, values)
        return self

    def setting(self, name: str, value: Any) -> ComponentRef:
        return self.host_setting(name, value)

    def settings_update(self, values: dict[str, Any]) -> ComponentRef:
        return self.host_settings_update(values)

    def adapter_setting(self, name: str, value: Any) -> ComponentRef:
        _apply_settings_update(self.adapter_settings, {name: value})
        return self

    def adapter_settings_update(self, values: dict[str, Any]) -> ComponentRef:
        _apply_settings_update(self.adapter_settings, values)
        return self

    def other_setting(
        self,
        target: str,
        name: str,
        value: Any,
    ) -> ComponentRef:
        if target == "Host":
            return self.host_setting(name, value)
        if target == "Adapter":
            return self.adapter_setting(name, value)

        self.other_settings = [
            setting
            for setting in self.other_settings
            if not (
                setting.get("@Target") == target
                and setting.get("@Name") == name
            )
        ]
        if value is not None:
            self.other_settings.append(
                {
                    "@Target": target,
                    "@Name": name,
                    "#text": _text_value(value),
                }
            )
        return self

    def connect(
        self,
        port_name: str | Port,
        target_component: ComponentRef | str,
    ) -> ComponentRef:
        port = self._coerce_port(port_name)
        self.production.connect(port, target_component)
        return self

    def connect_add(
        self,
        port_name: str | Port,
        target_component: ComponentRef | str,
    ) -> ComponentRef:
        port = self._coerce_port(port_name)
        self.production.connect_add(port, target_component)
        return self

    def _coerce_port(self, port_name: str | Port) -> Port:
        if isinstance(port_name, Port):
            if port_name.production is not self.production:
                raise ValueError("source port belongs to a different Production")
            if port_name.component is not self:
                raise ValueError("source port belongs to a different component")
            return port_name
        return self.port(str(port_name))

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
        classname: str | None = None,
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
