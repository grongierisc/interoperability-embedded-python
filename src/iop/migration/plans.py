from __future__ import annotations

import inspect
import os
from typing import Any

from .manifest import MigrationManifestBuilder


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
    lines.extend(format_plan_section("VALIDATION", plan.get("validation", [])))
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
    """Build migration plan payloads from the normalized migration manifest."""

    def __init__(self, utils):
        self._utils = utils

    def build(
        self,
        settings,
        path,
        filename=None,
        mode: str | None = None,
        namespace: str | None = None,
        strict_production_validation: bool = False,
    ) -> dict[str, Any]:
        """Build and validate a migration plan from a settings module."""
        if not path:
            path = self._settings_path(settings)

        manifest = MigrationManifestBuilder(self._utils).build(
            settings,
            path,
            filename=filename,
            mode=mode,
            namespace=namespace,
            strict_production_validation=strict_production_validation,
        )

        return {
            "settings": manifest.settings,
            "mode": mode,
            "namespace": namespace,
            "classes": manifest.plan_class_entries(),
            "schemas": manifest.plan_schema_entries(),
            "productions": manifest.plan_production_entries(),
            "validation": manifest.plan_validation_entries(),
        }

    @staticmethod
    def _settings_path(settings) -> str:
        return os.path.dirname(inspect.getfile(settings))
