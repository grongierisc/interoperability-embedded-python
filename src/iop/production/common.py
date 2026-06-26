from __future__ import annotations

import importlib
from typing import Any

from ..components.settings import Setting

PRODUCTION_SETTING_FIELDS: dict[str, tuple[str, Any]] = {
    "shutdown_timeout": ("ShutdownTimeout", 120),
    "update_timeout": ("UpdateTimeout", 10),
    "alert_notification_manager": ("AlertNotificationManager", ""),
    "alert_notification_operation": ("AlertNotificationOperation", ""),
    "alert_notification_recipients": ("AlertNotificationRecipients", ""),
    "alert_action_window": ("AlertActionWindow", 60),
}

PRODUCTION_SETTING_NAMES: dict[str, str] = {
    field_name: iris_name
    for field_name, (iris_name, _default) in PRODUCTION_SETTING_FIELDS.items()
}

PRODUCTION_SETTING_FIELDS_BY_IRIS: dict[str, str] = {
    iris_name: field_name
    for field_name, (iris_name, _default) in PRODUCTION_SETTING_FIELDS.items()
}

SETTING_NAME_ALIASES = {
    "target_config_name": "TargetConfigName",
    "target_config_names": "TargetConfigNames",
}


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


def _adapter_type_from_component_class(component_class: type | None) -> str:
    if component_class is None:
        return ""
    method = getattr(component_class, "get_adapter_type", None)
    if callable(method):
        value = method()
        if value:
            return str(value)
    return ""


def _adapter_type_from_class_name(class_name: str | None) -> str:
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


def _setting_name(name: Any) -> str:
    if isinstance(name, Setting) and name.name:
        return name.name
    return str(name)


def _normalize_settings_mapping(values: Any) -> dict[str, Any]:
    return {_setting_name(key): value for key, value in dict(values or {}).items()}


def _settings_to_iris(target_name: str, values: dict[str, Any]) -> list[dict[str, str]]:
    return [
        {
            "@Target": target_name,
            "@Name": _setting_name(name),
            "#text": _text_value(value),
        }
        for name, value in values.items()
    ]


def _apply_settings_update(target: dict[str, Any], updates: Any) -> None:
    """Merge *updates* into *target*, treating ``None`` values as removals."""
    for key, value in (updates or {}).items():
        key = _setting_name(key)
        if value is None:
            target.pop(key, None)
        else:
            target[key] = value
