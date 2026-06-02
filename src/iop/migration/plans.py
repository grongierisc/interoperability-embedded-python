from __future__ import annotations

import inspect
import os
from typing import Any


def format_migration_success(filename: str, namespace: str | None = None) -> str:
    suffix = f" in namespace {namespace}" if namespace else ""
    return f"Migration succeeded{suffix}: {filename}"


def format_migration_plan(plan: dict[str, Any]) -> str:
    """Format a migration plan for CLI and migration output."""
    lines = [f"Migration plan: {plan['settings']}"]
    if plan.get("mode"):
        lines.append(f"Mode: {plan['mode']}")
    if plan.get("namespace"):
        lines.append(f"Namespace: {plan['namespace']}")
    lines.append("")
    lines.extend(format_plan_section("CLASSES", plan["classes"]))
    lines.extend(format_plan_section("SCHEMAS", plan["schemas"]))
    lines.extend(format_plan_section("PRODUCTIONS", plan["productions"]))
    return "\n".join(lines)


def format_plan_section(title: str, entries: list[str]) -> list[str]:
    lines = [f"{title}:"]
    if entries:
        lines.extend(f"  {entry}" for entry in entries)
    else:
        lines.append("  none")
    lines.append("")
    return lines


class MigrationPlanner:
    """Build migration plan payloads using the existing registration helpers."""

    def __init__(self, utils):
        self._utils = utils

    def build(
        self,
        settings,
        path,
        filename=None,
        mode: str | None = None,
        namespace: str | None = None,
    ) -> dict[str, Any]:
        """Build and validate a migration plan from a settings module."""
        if not path:
            path = self._settings_path(settings)

        plan: dict[str, Any] = {
            "settings": filename or inspect.getfile(settings),
            "mode": mode,
            "namespace": namespace,
            "classes": [],
            "schemas": [],
            "productions": [],
        }

        self._add_class_entries(plan, getattr(settings, "CLASSES", {}), path)
        self._add_schema_entries(plan, getattr(settings, "SCHEMAS", None))
        self._add_production_entries(plan, getattr(settings, "PRODUCTIONS", None))
        return plan

    @staticmethod
    def _settings_path(settings) -> str:
        return os.path.dirname(inspect.getfile(settings))

    def _add_class_entries(
        self, plan: dict[str, Any], classes: dict[str, Any], path: str
    ) -> None:
        if not isinstance(classes, dict):
            raise ValueError("CLASSES must be a dictionary.")
        for key, value in classes.items():
            kind, target = self._utils._classify_class_setting(value, path)
            if kind == "message_schema":
                schema_hint = value.__name__ if inspect.isclass(value) else target
                raise ValueError(
                    f"{target} is a Message/PydanticMessage and cannot be registered "
                    f"in CLASSES. Use SCHEMAS = [{schema_hint}] if you "
                    "need DTL support. Otherwise, no migration is required for this "
                    "message."
                )
            if kind == "persistent_message":
                plan["classes"].append(f"{key} -> {target} (PersistentMessage)")
            else:
                plan["classes"].append(f"{key} -> {target} (component)")

    def _add_schema_entries(
        self, plan: dict[str, Any], schemas: list[type] | None
    ) -> None:
        if schemas is None:
            return
        if not isinstance(schemas, list):
            raise ValueError("SCHEMAS must be a list of message classes.")
        for cls in schemas:
            self._utils._validate_dtl_schema_class(cls, "SCHEMAS")
            plan["schemas"].append(self._utils._python_classname(cls))

    def _add_production_entries(
        self, plan: dict[str, Any], productions: list[Any] | None
    ) -> None:
        if productions is None:
            return
        if not isinstance(productions, list):
            raise ValueError("PRODUCTIONS must be a list.")
        auto_class_entries = set()
        for production in productions:
            if self._utils._is_production_object(production):
                plan["productions"].append(production.name)
                self._add_production_component_entries(
                    plan, production, auto_class_entries
                )
                continue
            if not isinstance(production, dict) or not production:
                raise ValueError("Each PRODUCTION entry must be a non-empty dict.")
            plan["productions"].append(next(iter(production.keys())))

    def _add_production_component_entries(
        self,
        plan: dict[str, Any],
        production,
        auto_class_entries: set[tuple[str, str]],
    ) -> None:
        for registration in getattr(production, "message_registrations", lambda: ())():
            self._add_auto_class_entry(
                plan,
                auto_class_entries,
                registration.iris_classname,
                registration.message_class,
                kind="PersistentMessage",
            )
        for item in production.component_registrations():
            target = item.class_name or item.name
            cls = item.component_class
            self._add_auto_class_entry(plan, auto_class_entries, target, cls)
        for item in getattr(production, "adapter_registrations", lambda: ())():
            self._add_auto_class_entry(
                plan, auto_class_entries, item.adapter_class_name, item.adapter_class
            )

    def _add_auto_class_entry(
        self,
        plan: dict[str, Any],
        auto_class_entries: set[tuple[str, str]],
        target: str,
        cls: type,
        *,
        kind: str = "component",
    ) -> None:
        entry_key = (target, self._utils._python_classname(cls))
        if entry_key in auto_class_entries:
            return
        auto_class_entries.add(entry_key)
        plan["classes"].append(f"{target} -> {entry_key[1]} ({kind})")
