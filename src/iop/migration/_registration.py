from __future__ import annotations

from collections.abc import Callable
from typing import Any

from .manifest import ClassRegistration, MigrationManifest


def execute_class_registration(
    registration: ClassRegistration,
    *,
    persistent_registry: dict[str, tuple[type, bool]] | None,
    register_persistent: Callable[..., None],
    register_component: Callable[..., None],
    register_file: Callable[..., None],
    register_package: Callable[..., None],
    register_folder: Callable[..., None],
) -> None:
    action = registration.action
    if action == "persistent_message":
        assert registration.cls is not None
        register_persistent(
            registration.cls,
            registration.iris_classname,
            sync_schema=registration.sync_schema,
            persistent_registry=persistent_registry,
        )
        return

    assert registration.path is not None
    if action in {"component_class", "component_descriptor"}:
        register_component(
            registration.module,
            registration.classname,
            registration.path,
            1,
            registration.iris_classname,
        )
    elif action in {"module_file", "file"}:
        register_file(
            registration.file,
            registration.path,
            1,
            registration.iris_classname,
        )
    elif action == "package":
        register_package(
            registration.package,
            registration.path,
            1,
            registration.iris_classname,
        )
    elif action == "folder":
        register_folder(registration.path, 1, registration.iris_classname)
    else:
        raise ValueError(f"Invalid migration class action: {action}.")


def execute_manifest(
    manifest: MigrationManifest,
    *,
    persistent_registry: dict[str, tuple[type, bool]] | None,
    execute_class: Callable[..., None],
    validate_production: Callable[[Any], Any],
    register_production: Callable[[str, dict], None],
    register_schema: Callable[[type], None],
) -> None:
    for registration in manifest.class_registrations:
        execute_class(registration, persistent_registry=persistent_registry)

    for production in manifest.production_registrations:
        for registration in production.class_registrations:
            execute_class(registration, persistent_registry=persistent_registry)
        validate_production(production.validation_subject)
        register_production(production.name, production.definition)

    for registration in manifest.schema_registrations:
        register_schema(registration.schema_class)
