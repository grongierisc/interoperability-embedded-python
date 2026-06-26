from __future__ import annotations

import warnings
from dataclasses import dataclass
from typing import Any

from .common import (
    PRODUCTION_SETTING_FIELDS_BY_IRIS,
    PRODUCTION_SETTING_NAMES,
    SETTING_NAME_ALIASES,
    _normalize_settings_mapping,
)
from .import_ import _as_list, _production_payload, _split_settings
from .types import TargetSetting

_PRODUCTION_PUBLIC_FIELDS = {
    "name",
    "testing_enabled",
    "log_general_trace_events",
    "actor_pool_size",
    "description",
    "shutdown_timeout",
    "update_timeout",
    "alert_notification_manager",
    "alert_notification_operation",
    "alert_notification_recipients",
    "alert_action_window",
    "namespace",
}

_PRODUCTION_DICT_KEYS = {
    "@Name",
    "@TestingEnabled",
    "@LogGeneralTraceEvents",
    "Description",
    "ActorPoolSize",
    "Setting",
    "Item",
}

_PRODUCTION_SETTING_NAME_ALIASES = {
    **PRODUCTION_SETTING_NAMES,
    **{iris_name: iris_name for iris_name in PRODUCTION_SETTING_FIELDS_BY_IRIS},
}


@dataclass(frozen=True)
class ProductionValidationIssue:
    kind: str
    path: str
    message: str
    suggestion: str = ""

    def to_dict(self) -> dict[str, str]:
        data = {
            "kind": self.kind,
            "path": self.path,
            "message": self.message,
        }
        if self.suggestion:
            data["suggestion"] = self.suggestion
        return data

    def to_text(self) -> str:
        text = f"{self.kind} {self.path}: {self.message}"
        if self.suggestion:
            return f"{text} {self.suggestion}"
        return text


@dataclass(frozen=True)
class ProductionValidationReport:
    production_name: str
    issues: tuple[ProductionValidationIssue, ...] = ()

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "production": self.production_name,
            "has_issues": self.has_issues,
            "issues": [issue.to_dict() for issue in self.issues],
        }

    def to_text(self) -> str:
        lines = [f"Production validation: {self.production_name}"]
        if not self.issues:
            lines.append("  no issues")
        else:
            lines.extend(f"  {issue.to_text()}" for issue in self.issues)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_text()


class ProductionValidationWarning(UserWarning):
    pass


class ProductionValidationError(ValueError):
    def __init__(self, report: ProductionValidationReport):
        self.report = report
        super().__init__(report.to_text())


def validate_production(
    production: Any,
    *,
    strict: bool = False,
    warn: bool = True,
) -> ProductionValidationReport:
    report = _build_production_object_report(production)
    return _finalize_report(report, strict=strict, warn=warn)


def validate_production_entry(
    production: Any,
    *,
    strict: bool = False,
    warn: bool = True,
) -> ProductionValidationReport:
    if _is_production_object(production):
        report = _build_production_object_report(production)
    else:
        report = _build_production_dict_report(production)
    return _finalize_report(report, strict=strict, warn=warn)


def _finalize_report(
    report: ProductionValidationReport,
    *,
    strict: bool,
    warn: bool,
) -> ProductionValidationReport:
    if not report.has_issues:
        return report
    if strict:
        raise ProductionValidationError(report)
    if warn:
        for issue in report.issues:
            warnings.warn(issue.to_text(), ProductionValidationWarning, stacklevel=3)
    return report


def _build_production_object_report(production: Any) -> ProductionValidationReport:
    production_name = str(getattr(production, "name", "Production"))
    issues: list[ProductionValidationIssue] = []
    issues.extend(_unknown_public_attrs(production))

    for item in getattr(production, "items", ()):
        issues.extend(_validate_component_ref(item))

    issues.extend(_validate_target_setting_values(production))

    return ProductionValidationReport(production_name, tuple(issues))


def _unknown_public_attrs(production: Any) -> list[ProductionValidationIssue]:
    issues = []
    for attr in sorted(getattr(production, "__dict__", {})):
        if attr.startswith("_") or attr in _PRODUCTION_PUBLIC_FIELDS:
            continue
        issues.append(
            ProductionValidationIssue(
                kind="production",
                path=f"production.{attr}",
                message=(
                    "Unknown public Production attribute. Only documented "
                    "Production fields are serialized."
                ),
            )
        )
    return issues


def _validate_component_ref(item: Any) -> list[ProductionValidationIssue]:
    issues: list[ProductionValidationIssue] = []
    item_name = str(getattr(item, "name", ""))
    component_class = getattr(item, "component_class", None)
    class_name = str(getattr(item, "class_name", "") or "")

    issues.extend(
        _validate_settings(
            settings=_normalize_settings_mapping(
                getattr(item, "host_settings", {}) or {}
            ),
            path_prefix=f"items.{item_name}.settings.Host",
            local_class=component_class,
            iris_class_name=class_name,
        )
    )

    adapter_settings = _normalize_settings_mapping(
        getattr(item, "adapter_settings", {}) or {}
    )
    if str(getattr(item, "kind", "")) == "process" and adapter_settings:
        issues.append(
            ProductionValidationIssue(
                kind="setting",
                path=f"items.{item_name}.settings.Adapter",
                message="Business process items do not support adapter settings.",
            )
        )

    adapter_class = getattr(item, "adapter_class", None)
    adapter_class_name = str(getattr(item, "adapter_class_name", "") or "")
    issues.extend(
        _validate_settings(
            settings=adapter_settings,
            path_prefix=f"items.{item_name}.settings.Adapter",
            local_class=adapter_class,
            iris_class_name=adapter_class_name,
            host_class_name=class_name,
        )
    )
    return issues


def _build_production_dict_report(data: Any) -> ProductionValidationReport:
    issues: list[ProductionValidationIssue] = []
    try:
        production_name, production_data = _production_payload(data)
    except Exception:
        return ProductionValidationReport("Production", tuple(issues))

    for key in sorted(set(production_data) - _PRODUCTION_DICT_KEYS):
        issues.append(
            ProductionValidationIssue(
                kind="production",
                path=f"production.{key}",
                message="Unknown production dictionary key.",
            )
        )

    issues.extend(_validate_production_settings(production_data.get("Setting")))
    for item in _as_list(production_data.get("Item", [])):
        if isinstance(item, dict):
            issues.extend(_validate_dict_item(item))

    return ProductionValidationReport(str(production_name), tuple(issues))


def _validate_production_settings(settings: Any) -> list[ProductionValidationIssue]:
    issues: list[ProductionValidationIssue] = []
    known_iris_names = set(PRODUCTION_SETTING_FIELDS_BY_IRIS)
    for setting in _as_list(settings):
        if not isinstance(setting, dict):
            continue
        target = setting.get("@Target", "")
        if target not in ("", "Production"):
            continue
        setting_name = str(setting.get("@Name", ""))
        if not setting_name or setting_name in known_iris_names:
            continue
        alias = _PRODUCTION_SETTING_NAME_ALIASES.get(setting_name)
        if alias in known_iris_names:
            issues.append(
                ProductionValidationIssue(
                    kind="production",
                    path=f"production.settings.{setting_name}",
                    message=(
                        "Production setting name is accepted as a known alias for "
                        "validation, but IoP will emit the original name."
                    ),
                    suggestion=f"Use {alias!r}.",
                )
            )
            continue
        issues.append(
            ProductionValidationIssue(
                kind="production",
                path=f"production.settings.{setting_name}",
                message="Unknown production-level setting.",
            )
        )
    return issues


def _validate_dict_item(item: dict[str, Any]) -> list[ProductionValidationIssue]:
    item_name = str(item.get("@Name", ""))
    class_ref = item.get("@ClassName", "")
    local_class = class_ref if isinstance(class_ref, type) else None
    iris_class_name = "" if isinstance(class_ref, type) else str(class_ref or "")
    host_settings, adapter_settings, _other_settings = _split_settings(
        item.get("Setting", [])
    )

    issues = _validate_settings(
        settings=host_settings,
        path_prefix=f"items.{item_name}.settings.Host",
        local_class=local_class,
        iris_class_name=iris_class_name,
    )
    issues.extend(
        _validate_settings(
            settings=adapter_settings,
            path_prefix=f"items.{item_name}.settings.Adapter",
            local_class=None,
            iris_class_name="",
            host_class_name=iris_class_name,
        )
    )
    return issues


def _validate_settings(
    *,
    settings: dict[str, Any],
    path_prefix: str,
    local_class: type | None,
    iris_class_name: str,
    host_class_name: str = "",
) -> list[ProductionValidationIssue]:
    if not settings:
        return []
    if local_class is not None:
        local_names = _local_setting_names(local_class)
        if local_names is not None:
            return _validate_names_with_known_set(
                settings,
                path_prefix=path_prefix,
                known_names=local_names,
            )

    iris_target_class = iris_class_name or _adapter_class_name_from_host(host_class_name)
    if iris_target_class:
        report = _validate_names_with_iris_dictionary(
            settings,
            path_prefix=path_prefix,
            iris_class_name=iris_target_class,
        )
        if report is not None:
            return report
    return []


def _local_setting_names(cls: type) -> set[str] | None:
    getter = getattr(cls, "_get_properties", None)
    if not callable(getter):
        return None
    try:
        properties = getter()
    except Exception:
        return None
    if not isinstance(properties, (list, tuple)):
        return None
    names: set[str] = set()
    for prop in properties:
        if isinstance(prop, (list, tuple)) and prop:
            names.add(str(prop[0]))
    return names


def _validate_target_setting_values(production: Any) -> list[ProductionValidationIssue]:
    items = tuple(getattr(production, "items", ()) or ())
    item_names = {str(getattr(item, "name", "")) for item in items}
    issues: list[ProductionValidationIssue] = []
    for item in items:
        item_name = str(getattr(item, "name", ""))
        host_settings = _normalize_settings_mapping(
            getattr(item, "host_settings", {}) or {}
        )
        for setting_name in _target_setting_names(item):
            if setting_name not in host_settings:
                continue
            for target_name in _target_names(host_settings[setting_name]):
                if target_name in item_names:
                    continue
                issues.append(
                    ProductionValidationIssue(
                        kind="route",
                        path=f"items.{item_name}.settings.Host.{setting_name}",
                        message=(
                            f"Target setting references missing production item "
                            f"{target_name!r}."
                        ),
                        suggestion=(
                            f"Add a production item named {target_name!r}, "
                            "or update/remove this target setting."
                        ),
                    )
                )
    return issues


def _target_setting_names(item: Any) -> set[str]:
    names = {str(name) for name in getattr(item, "target_setting_names", set())}
    component_class = getattr(item, "component_class", None)
    if isinstance(component_class, type):
        for base in reversed(component_class.__mro__):
            for name, value in base.__dict__.items():
                if isinstance(value, TargetSetting):
                    names.add(str(name))
    return names


def _target_names(value: Any) -> tuple[str, ...]:
    return tuple(
        target
        for target in (part.strip() for part in str(value or "").split(","))
        if target
    )


def _validate_names_with_known_set(
    settings: dict[str, Any],
    *,
    path_prefix: str,
    known_names: set[str],
) -> list[ProductionValidationIssue]:
    issues: list[ProductionValidationIssue] = []
    for setting_name in sorted(settings):
        if setting_name.startswith("%") or setting_name in known_names:
            continue
        alias = SETTING_NAME_ALIASES.get(setting_name)
        if alias in known_names:
            issues.append(_setting_alias_issue(path_prefix, setting_name, alias))
            continue
        issues.append(_unknown_setting_issue(path_prefix, setting_name))
    return issues


def _validate_names_with_iris_dictionary(
    settings: dict[str, Any],
    *,
    path_prefix: str,
    iris_class_name: str,
) -> list[ProductionValidationIssue] | None:
    iris = _iris_module()
    if iris is None or not _iris_class_exists(iris, iris_class_name):
        return None

    issues: list[ProductionValidationIssue] = []
    for setting_name in sorted(settings):
        if _iris_property_exists(iris, iris_class_name, setting_name):
            continue
        alias = SETTING_NAME_ALIASES.get(setting_name)
        if alias and _iris_property_exists(iris, iris_class_name, alias):
            issues.append(_setting_alias_issue(path_prefix, setting_name, alias))
            continue
        issues.append(_unknown_setting_issue(path_prefix, setting_name))
    return issues


def _adapter_class_name_from_host(host_class_name: str) -> str:
    if not host_class_name:
        return ""
    iris = _iris_module()
    if iris is None:
        return ""
    try:
        parameter = iris._Dictionary.CompiledParameter._OpenId(
            f"{host_class_name}||ADAPTER"
        )
        return str(getattr(parameter, "Default", "") or "")
    except Exception:
        return ""


def _iris_module() -> Any:
    try:
        import iris  # type: ignore
    except Exception:
        return None
    return iris


def _iris_class_exists(iris: Any, class_name: str) -> bool:
    try:
        return bool(iris._Dictionary.CompiledClass._ExistsId(class_name))
    except Exception:
        return False


def _iris_property_exists(iris: Any, class_name: str, property_name: str) -> bool:
    try:
        return bool(
            iris._Dictionary.CompiledProperty._ExistsId(
                f"{class_name}||{property_name}"
            )
        )
    except Exception:
        return False


def _setting_alias_issue(
    path_prefix: str,
    setting_name: str,
    alias: str,
) -> ProductionValidationIssue:
    return ProductionValidationIssue(
        kind="setting",
        path=f"{path_prefix}.{setting_name}",
        message=(
            "Setting name is accepted as a known alias for validation, "
            "but IoP will emit the original name."
        ),
        suggestion=f"Use {alias!r}.",
    )


def _unknown_setting_issue(path_prefix: str, setting_name: str) -> ProductionValidationIssue:
    return ProductionValidationIssue(
        kind="setting",
        path=f"{path_prefix}.{setting_name}",
        message="Unknown setting name.",
    )


def _is_production_object(value: Any) -> bool:
    return (
        hasattr(value, "to_dict")
        and hasattr(value, "component_registrations")
        and hasattr(value, "name")
    )
