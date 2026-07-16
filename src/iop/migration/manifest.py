from __future__ import annotations

import copy
import inspect
import os
from dataclasses import dataclass, field
from typing import Any

from ..production.validation import (
    ProductionValidationError,
    ProductionValidationReport,
    validate_production_entry,
)


@dataclass(frozen=True)
class ClassRegistration:
    iris_classname: str
    action: str
    target: str
    plan_kind: str = "component"
    source: str = "classes"
    cls: type | None = None
    module: str = ""
    classname: str = ""
    path: str | None = None
    package: str = ""
    file: str = ""
    sync_schema: bool = True

    @property
    def plan_entry(self) -> str:
        return f"{self.iris_classname} -> {self.target} ({self.plan_kind})"


@dataclass(frozen=True)
class SchemaRegistration:
    schema_class: type
    target: str


@dataclass(frozen=True)
class ProductionRegistration:
    name: str
    definition: dict[str, Any]
    validation_subject: Any
    validation_report: ProductionValidationReport
    source: str
    class_registrations: tuple[ClassRegistration, ...] = ()


@dataclass
class MigrationManifest:
    settings: str
    mode: str | None = None
    namespace: str | None = None
    class_registrations: list[ClassRegistration] = field(default_factory=list)
    schema_registrations: list[SchemaRegistration] = field(default_factory=list)
    production_registrations: list[ProductionRegistration] = field(
        default_factory=list
    )

    def plan_class_entries(self) -> list[str]:
        entries = [entry.plan_entry for entry in self.class_registrations]
        for production in self.production_registrations:
            entries.extend(entry.plan_entry for entry in production.class_registrations)
        return entries

    def plan_schema_entries(self) -> list[str]:
        return [entry.target for entry in self.schema_registrations]

    def plan_production_entries(self) -> list[str]:
        return [entry.name for entry in self.production_registrations]

    def plan_validation_entries(self) -> list[str]:
        entries: list[str] = []
        for production in self.production_registrations:
            report = production.validation_report
            if report.has_issues:
                entries.extend(
                    f"{report.production_name}: {issue.to_text()}"
                    for issue in report.issues
                )
        return entries


class MigrationManifestBuilder:
    """Normalize migration settings once for planning and execution."""

    def __init__(self, utils):
        self._utils = utils

    def build(
        self,
        settings,
        path: str | None,
        *,
        filename: str | None = None,
        mode: str | None = None,
        namespace: str | None = None,
        strict_production_validation: bool = False,
    ) -> MigrationManifest:
        if not path:
            path = self._settings_path(settings)

        manifest = MigrationManifest(
            settings=filename or inspect.getfile(settings),
            mode=mode,
            namespace=namespace,
        )
        manifest.class_registrations.extend(
            self.build_class_registrations(
                getattr(settings, "CLASSES", {}),
                path,
                source="classes",
            )
        )
        manifest.schema_registrations.extend(
            self.build_schema_registrations(getattr(settings, "SCHEMAS", None))
        )
        manifest.production_registrations.extend(
            self.build_production_registrations(
                getattr(settings, "PRODUCTIONS", None),
                path,
                strict_production_validation=strict_production_validation,
            )
        )
        return manifest

    @staticmethod
    def _settings_path(settings) -> str:
        return os.path.dirname(inspect.getfile(settings))

    def build_class_registrations(
        self,
        class_items: dict[str, Any] | None,
        root_path: str | None = None,
        *,
        source: str = "classes",
    ) -> list[ClassRegistration]:
        if class_items is None:
            return []
        if not isinstance(class_items, dict):
            raise ValueError("CLASSES must be a dictionary.")

        registrations: list[ClassRegistration] = []
        for iris_classname, value in class_items.items():
            registrations.append(
                self.class_registration(
                    iris_classname,
                    value,
                    root_path,
                    source=source,
                )
            )
        return registrations

    def class_registration(
        self,
        iris_classname: str,
        value: Any,
        root_path: str | None = None,
        *,
        source: str = "classes",
    ) -> ClassRegistration:
        if inspect.isclass(value):
            if self._utils.is_persistent_message_class(value):
                return ClassRegistration(
                    iris_classname=iris_classname,
                    action="persistent_message",
                    target=self._utils._python_classname(value),
                    plan_kind="PersistentMessage",
                    source=source,
                    cls=value,
                )
            if self._utils._is_message_schema_class(value):
                raise ValueError(
                    f"{self._utils._python_classname(value)} is a Message/"
                    "PydanticMessage and cannot be registered in CLASSES. "
                    f"Use SCHEMAS = [{value.__name__}] if you need DTL "
                    "support. Otherwise, no migration is required for this "
                    "message."
                )
            return ClassRegistration(
                iris_classname=iris_classname,
                action="component_class",
                target=self._utils._python_classname(value),
                source=source,
                cls=value,
                module=value.__module__,
                classname=value.__name__,
                path=self._class_path(value, root_path),
            )

        if inspect.ismodule(value):
            return ClassRegistration(
                iris_classname=iris_classname,
                action="module_file",
                target=f"{value.__name__}.*",
                source=source,
                module=value.__name__,
                file=f"{value.__name__}.py",
                path=self._module_path(value, root_path),
            )

        if isinstance(value, dict):
            return self._dict_class_registration(
                iris_classname,
                value,
                source=source,
            )

        raise ValueError(f"Invalid migration class entry: {value!r}.")

    def classify_class_setting(
        self,
        value: Any,
        root_path: str | None = None,
    ) -> tuple[str, str]:
        if inspect.isclass(value):
            if self._utils.is_persistent_message_class(value):
                return "persistent_message", self._utils._python_classname(value)
            if self._utils._is_message_schema_class(value):
                return "message_schema", self._utils._python_classname(value)
            return "component", self._utils._python_classname(value)

        if inspect.ismodule(value):
            return "component", f"{value.__name__}.*"

        if isinstance(value, dict):
            if "path" in value and "module" in value and "class" in value:
                cls = self._utils._try_import_class(
                    value["module"],
                    value["class"],
                    value["path"],
                )
                target = f"{value['module']}.{value['class']}"
                if cls is not None:
                    if self._utils.is_persistent_message_class(cls):
                        return "persistent_message", target
                    if self._utils._is_message_schema_class(cls):
                        return "message_schema", target
                return "component", target
            if "path" in value and "package" in value:
                return "component", f"{value['package']} package"
            if "path" in value and "file" in value:
                return "component", value["file"]
            if "path" in value:
                return "component", value["path"]

        raise ValueError(f"Invalid migration class entry: {value!r}.")

    def _dict_class_registration(
        self,
        iris_classname: str,
        value: dict[str, Any],
        *,
        source: str,
    ) -> ClassRegistration:
        if "path" in value and "module" in value and "class" in value:
            cls = self._utils._try_import_class(
                value["module"],
                value["class"],
                value["path"],
            )
            target = f"{value['module']}.{value['class']}"
            if cls is not None:
                if self._utils.is_persistent_message_class(cls):
                    return ClassRegistration(
                        iris_classname=iris_classname,
                        action="persistent_message",
                        target=target,
                        plan_kind="PersistentMessage",
                        source=source,
                        cls=cls,
                    )
                if self._utils._is_message_schema_class(cls):
                    raise ValueError(
                        f"{target} is a Message/PydanticMessage and cannot be "
                        "registered in CLASSES. Use SCHEMAS if you need DTL "
                        "support. Otherwise, no migration is required for this "
                        "message."
                    )
            return ClassRegistration(
                iris_classname=iris_classname,
                action="component_descriptor",
                target=target,
                source=source,
                module=value["module"],
                classname=value["class"],
                path=value["path"],
            )

        if "path" in value and "package" in value:
            return ClassRegistration(
                iris_classname=iris_classname,
                action="package",
                target=f"{value['package']} package",
                source=source,
                package=value["package"],
                path=value["path"],
            )

        if "path" in value and "file" in value:
            return ClassRegistration(
                iris_classname=iris_classname,
                action="file",
                target=value["file"],
                source=source,
                file=value["file"],
                path=value["path"],
            )

        if "path" in value:
            return ClassRegistration(
                iris_classname=iris_classname,
                action="folder",
                target=value["path"],
                source=source,
                path=value["path"],
            )

        raise ValueError(f"Invalid value for {iris_classname}.")

    def build_schema_registrations(
        self,
        schemas: list[type] | None,
    ) -> list[SchemaRegistration]:
        if schemas is None:
            return []
        if not isinstance(schemas, list):
            raise ValueError("SCHEMAS must be a list of message classes.")
        registrations: list[SchemaRegistration] = []
        for cls in schemas:
            self._utils._validate_dtl_schema_class(cls, "SCHEMAS")
            registrations.append(
                SchemaRegistration(
                    schema_class=cls,
                    target=self._utils._python_classname(cls),
                )
            )
        return registrations

    def build_production_registrations(
        self,
        productions: list[Any] | None,
        root_path: str | None = None,
        *,
        strict_production_validation: bool = False,
    ) -> list[ProductionRegistration]:
        if productions is None:
            return []
        if not isinstance(productions, list):
            raise ValueError("PRODUCTIONS must be a list.")

        registrations: list[ProductionRegistration] = []
        for production in productions:
            registration = self.production_registration(production, root_path)
            if strict_production_validation and registration.validation_report.has_issues:
                raise ProductionValidationError(registration.validation_report)
            registrations.append(registration)
        return registrations

    def production_registration(
        self,
        production: Any,
        root_path: str | None = None,
    ) -> ProductionRegistration:
        plan_report = validate_production_entry(production, strict=False, warn=False)
        if self._utils._is_production_object(production):
            definition, extra_registrations = self.normalize_production_dict(
                production.to_dict(),
                root_path,
            )
            class_registrations = [
                *self.production_object_class_registrations(production, root_path),
                *extra_registrations,
            ]
            return ProductionRegistration(
                name=production.name,
                definition=definition,
                validation_subject=production,
                validation_report=plan_report,
                source="production_object",
                class_registrations=tuple(class_registrations),
            )

        if not isinstance(production, dict) or not production:
            raise ValueError("Each PRODUCTION entry must be a non-empty dict.")

        production_copy = copy.deepcopy(production)
        production_name = next(iter(production_copy.keys()))
        definition, class_registrations = self.normalize_production_dict(
            production_copy,
            root_path,
        )
        return ProductionRegistration(
            name=production_name,
            definition=definition,
            validation_subject=definition,
            validation_report=plan_report,
            source="legacy_dict",
            class_registrations=tuple(class_registrations),
        )

    def production_object_class_registrations(
        self,
        production,
        root_path: str | None = None,
    ) -> list[ClassRegistration]:
        registrations: list[ClassRegistration] = []
        registered: set[tuple[str, str, str]] = set()

        for registration in getattr(production, "message_registrations", lambda: ())():
            registrations.append(
                ClassRegistration(
                    iris_classname=registration.iris_classname,
                    action="persistent_message",
                    target=self._utils._python_classname(registration.message_class),
                    plan_kind="PersistentMessage",
                    source="production",
                    cls=registration.message_class,
                    sync_schema=registration.sync_schema,
                )
            )

        for item in production.component_registrations():
            cls = item.component_class
            if not inspect.isclass(cls):
                continue
            key = (item.class_name, cls.__module__, cls.__name__)
            if key in registered:
                continue
            registered.add(key)
            registrations.append(
                ClassRegistration(
                    iris_classname=item.class_name,
                    action="component_class",
                    target=self._utils._python_classname(cls),
                    source="production",
                    cls=cls,
                    module=cls.__module__,
                    classname=cls.__name__,
                    path=self._class_path(cls, root_path),
                )
            )

        for item in getattr(production, "adapter_registrations", lambda: ())():
            cls = item.adapter_class
            if not inspect.isclass(cls):
                continue
            key = (item.adapter_class_name, cls.__module__, cls.__name__)
            if key in registered:
                continue
            registered.add(key)
            registrations.append(
                ClassRegistration(
                    iris_classname=item.adapter_class_name,
                    action="component_class",
                    target=self._utils._python_classname(cls),
                    source="production",
                    cls=cls,
                    module=cls.__module__,
                    classname=cls.__name__,
                    path=self._class_path(cls, root_path),
                )
            )
        return registrations

    def normalize_production_dict(
        self,
        production: dict[str, Any],
        root_path: str | None = None,
    ) -> tuple[dict[str, Any], list[ClassRegistration]]:
        if not isinstance(production, dict) or not production:
            raise ValueError("Each PRODUCTION entry must be a non-empty dict.")

        production_name = next(iter(production.keys()))
        production["Production"] = production.pop(production_name)
        return production, self.normalize_production_items(production, root_path)

    def normalize_production_items(
        self,
        production: dict[str, Any],
        root_path: str | None = None,
    ) -> list[ClassRegistration]:
        registrations: list[ClassRegistration] = []
        if "Item" not in production["Production"]:
            return registrations

        for index, item in enumerate(production["Production"]["Item"]):
            if "@ClassName" not in item:
                raise ValueError(f"Missing @ClassName for {item.get('@Name')}.")
            class_ref = item["@ClassName"]
            item_name = item["@Name"]
            if inspect.isclass(class_ref):
                registrations.append(
                    ClassRegistration(
                        iris_classname=item_name,
                        action="component_class",
                        target=self._utils._python_classname(class_ref),
                        source="production",
                        cls=class_ref,
                        module=class_ref.__module__,
                        classname=class_ref.__name__,
                        path=self._class_path(class_ref, root_path),
                    )
                )
                production["Production"]["Item"][index]["@ClassName"] = item_name
            elif isinstance(class_ref, dict):
                registrations.extend(
                    self.build_class_registrations(
                        {item_name: class_ref},
                        None,
                        source="production",
                    )
                )
                production["Production"]["Item"][index]["@ClassName"] = item_name
            elif not isinstance(class_ref, str):
                raise ValueError(f"Invalid value for {item_name}.")

        return registrations

    @staticmethod
    def _class_path(klass: type, root_path: str | None) -> str:
        if root_path:
            return root_path
        return os.path.dirname(inspect.getfile(klass))

    @staticmethod
    def _module_path(module, root_path: str | None) -> str:
        if root_path:
            return root_path
        return os.path.dirname(inspect.getfile(module))
