import ast
import importlib
import importlib.resources
import importlib.util
import inspect
import json
import os
import sys
import warnings
from functools import wraps
from typing import Any

from pydantic import TypeAdapter

from ..messages.base import _Message, _PydanticMessage
from ..messages.persistent import (
    is_persistent_message_class,
    register_persistent_message_class,
)
from ..production.validation import validate_production_entry
from ..runtime import iris as _iris
from ..runtime.environment import remove_sys_path, temporary_sys_path
from .io import (
    dict_to_xml as _dict_to_xml,
)
from .io import (
    guess_path as _guess_path,
)
from .io import (
    stream_to_string as _stream_to_string,
)
from .io import (
    string_to_stream as _string_to_stream,
)
from .io import (
    xml_to_json as _xml_to_json,
)
from .manifest import (
    ClassRegistration,
    MigrationManifest,
    MigrationManifestBuilder,
)
from .plans import (
    MigrationPlanner,
)
from .plans import (
    format_migration_plan as _format_migration_plan,
)
from .plans import (
    format_migration_success as _format_migration_success,
)
from .plans import (
    format_plan_section as _plans_format_plan_section,
)

_persistent_message_registry: dict[str, tuple[type, bool]] = {}


def raise_on_error(sc):
    """
    If the status code is an error, raise an exception

    :param sc: The status code returned by the Iris API
    """
    if _iris.get_iris().system.Status.IsError(sc):
        raise RuntimeError(_iris.get_iris().system.Status.GetOneStatusText(sc))


def setup(path: str | None = None):

    if path is None:
        # get the path of the data folder with importlib.resources
        try:
            path = str(importlib.resources.files("iop").joinpath("cls"))
        except ModuleNotFoundError:
            path = None

    if path:
        raise_on_error(
            _iris.get_iris().cls("%SYSTEM.OBJ").LoadDir(path, "uk", "*.cls", 1)
        )

    # compile loaded classes by package (avoids parallel worker crashes in IRIS 2026.1+)
    raise_on_error(_iris.get_iris().cls("%SYSTEM.OBJ").Compile("IOP.*", "cb"))


def register_message_schema(msg_cls: type):
    """
    It takes a class and registers the schema

    :param cls: The class to register
    """
    if is_persistent_message_class(msg_cls):
        raise ValueError(
            f"{_python_classname(msg_cls)} is a PersistentMessage. "
            "Register it in CLASSES, not SCHEMAS."
        )
    if not inspect.isclass(msg_cls):
        raise ValueError("SCHEMAS entries must be message classes.")
    if issubclass(msg_cls, _PydanticMessage):
        schema = msg_cls.model_json_schema()
    elif issubclass(msg_cls, _Message):
        type_adapter = TypeAdapter(msg_cls)
        schema = type_adapter.json_schema()
    else:
        raise ValueError(
            f"{_python_classname(msg_cls)} cannot be registered as a "
            "DTL schema. Use a Message or PydanticMessage subclass."
        )
    schema_name = msg_cls.__module__ + "." + msg_cls.__name__
    schema_str = json.dumps(schema)
    categories = schema_name
    register_schema(schema_name, schema_str, categories)


def register_schema(schema_name: str, schema_str: str, categories: str):
    """
    It takes a schema name, a schema string, and a category string, and registers the schema

    :param schema_name: The name of the schema
    :type schema_name: str
    :param schema_str: The schema as a string
    :type schema_str: str
    :param categories: The categories of the schema
    :type categories: str
    """
    raise_on_error(
        _iris.get_iris()
        .cls("IOP.Message.JSONSchema")
        .Import(schema_str, categories, schema_name)
    )


def register_persistent_message(
    msg_cls: type, iris_classname: str, sync_schema: bool = True
):
    """
    Register a PersistentMessage as a native IRIS message body class.

    :param msg_cls: PersistentMessage subclass to register
    :param iris_classname: IRIS class name to generate, usually the CLASSES key
    :param sync_schema: when True, sync the IRIS schema immediately
    """
    register_persistent_message_class(msg_cls, iris_classname, sync_schema=sync_schema)


def _python_classname(value: Any) -> str:
    module = getattr(value, "__module__", "")
    name = getattr(value, "__name__", repr(value))
    return f"{module}.{name}" if module else str(name)


def _is_message_schema_class(value: Any) -> bool:
    try:
        return (
            inspect.isclass(value)
            and (issubclass(value, _Message) or issubclass(value, _PydanticMessage))
            and not is_persistent_message_class(value)
        )
    except TypeError:
        return False


def get_python_settings() -> tuple[str, str, str]:
    import iris_utils._cli

    pythonlib = iris_utils._cli.find_libpython()
    pythonpath = _get_python_path()
    pythonversion = sys.version[:4]

    if not pythonlib:
        pythonlib = ""

    return pythonlib, pythonpath, pythonversion


def _get_python_path() -> str:

    if "VIRTUAL_ENV" in os.environ:
        return os.path.join(
            os.environ["VIRTUAL_ENV"],
            "lib",
            f"python{sys.version[:4]}",
            "site-packages",
        )
    return ""


def register_component(
    module: str,
    classname: str,
    path: str,
    overwrite: int = 1,
    iris_classname: str = "Python",
):
    """Register a Python component as an IRIS proxy class.

    Prefer a Python Production graph in PRODUCTIONS for new application
    components. Use register_component() directly for standalone bindings,
    legacy migration helpers, or manual proxy registration only.

    :param module: The name of the module that contains the class
    :type module: str
    :param classname: The name of the class you want to register
    :type classname: str
    :param path: The path to the component
    :type path: str
    :param overwrite: 0 = no, 1 = yes
    :type overwrite: int
    :param iris_classname: The name of the class in the Iris class hierarchy
    :type iris_classname: str
    :return: The return value is a string.
    """
    path = os.path.abspath(os.path.normpath(path))
    fullpath = guess_path(module, path)
    pythonlib, pythonpath, pythonversion = get_python_settings()
    try:
        _iris.get_iris().cls("IOP.Utils").dispatchRegisterComponent(
            module,
            classname,
            path,
            fullpath,
            overwrite,
            iris_classname,
            pythonlib,
            pythonpath,
            pythonversion,
        )
    except RuntimeError as e:
        raise RuntimeError(
            "Could not register component "
            f"{iris_classname} from {module}.{classname}. "
            "If IRIS reports that IOP.Utils is missing, initialize the IRIS "
            f"support classes with `iop --init`. Original IRIS error: {e}"
        ) from e


def bind_component(
    module: str,
    classname: str,
    path: str,
    overwrite: int = 1,
    iris_classname: str = "Python",
):
    """Public alias for register_component().

    Prefer a Python Production graph in PRODUCTIONS for new application
    components. Use bind_component() directly only for standalone bindings,
    legacy migration helpers, or manual proxy registration.
    """
    return register_component(module, classname, path, overwrite, iris_classname)


def unregister_component(iris_classname: str):
    """
    Remove an IOP-generated IRIS proxy class binding.

    This does not delete Python source files or production items. IRIS refuses
    to remove the proxy when it is still referenced by a production item.
    """
    iris_classname = str(iris_classname or "").strip()
    if not iris_classname:
        raise ValueError("IRIS class name is required.")
    status = (
        _iris.get_iris()
        .cls("IOP.Utils")
        .DeleteComponentProxy(iris_classname)
    )
    raise_on_error(status)


def unbind_component(iris_classname: str):
    """
    Public alias for removing an IOP-generated IRIS proxy class binding.
    """
    return unregister_component(iris_classname)


def list_component_bindings(unused_only: bool = False) -> list[dict[str, Any]]:
    """
    List IOP-generated IRIS proxy class bindings.

    When unused_only is True, return only proxy classes that are not referenced
    by any production item.
    """
    data = (
        _iris.get_iris()
        .cls("IOP.Utils")
        .ListComponentProxies(1 if unused_only else 0)
    )
    if isinstance(data, list):
        return data
    return json.loads(data)


def list_bindings(unused_only: bool = False) -> list[dict[str, Any]]:
    """
    Public alias for listing IOP-generated IRIS proxy class bindings.
    """
    return list_component_bindings(unused_only=unused_only)


def register_folder(path: str, overwrite: int = 1, iris_package_name: str = "Python"):
    """
    > This function takes a path to a folder, and registers all the Python files in that folder as IRIS
    classes

    :param path: the path to the folder containing the files you want to register
    :type path: str
    :param overwrite:
    :type overwrite: int
    :param iris_package_name: The name of the iris package you want to register the file to
    :type iris_package_name: str
    """
    path = os.path.normpath(path)
    # get the absolute path of the folder
    path = os.path.abspath(path)
    for filename in os.listdir(path):
        if filename.endswith(".py"):
            _register_file(filename, path, overwrite, iris_package_name)
        else:
            continue


def register_file(file: str, overwrite: int = 1, iris_package_name: str = "Python"):
    """
    It takes a file name, a boolean to overwrite existing components, and the name of the Iris
    package that the file is in. It then opens the file, parses it, and looks for classes that extend
    BusinessOperation, BusinessProcess, or BusinessService. If it finds one, it calls register_component
    with the module name, class name, path, overwrite boolean, and the full Iris package name

    :param file: the name of the file containing the component
    :type file: str
    :param overwrite: if the component already exists, overwrite it
    :type overwrite: int
    :param iris_package_name: the name of the iris package that you want to register the components to
    :type iris_package_name: str
    """
    head_tail = os.path.split(file)
    return _register_file(head_tail[1], head_tail[0], overwrite, iris_package_name)


def _register_file(
    filename: str, path: str, overwrite: int = 1, iris_package_name: str = "Python"
):
    """
    It takes a file name, a path, a boolean to overwrite existing components, and the name of the Iris
    package that the file is in. It then opens the file, parses it, and looks for classes that extend
    BusinessOperation, BusinessProcess, or BusinessService. If it finds one, it calls register_component
    with the module name, class name, path, overwrite boolean, and the full Iris package name

    :param filename: the name of the file containing the component
    :type filename: str
    :param path: the path to the directory containing the files to be registered
    :type path: str
    :param overwrite: if the component already exists, overwrite it
    :type overwrite: int
    :param iris_package_name: the name of the iris package that you want to register the components to
    :type iris_package_name: str
    """
    # pour chaque classe dans le module, appeler register_component
    f = os.path.join(path, filename)
    with open(f) as file:
        node = ast.parse(file.read())
        # list of class in the file
        classes = [n for n in node.body if isinstance(n, ast.ClassDef)]
        for klass in classes:
            extend = ""
            if len(klass.bases) == 1:
                base = klass.bases[0]
                if isinstance(base, ast.Name):
                    extend = base.id
                elif isinstance(base, ast.Attribute):
                    extend = base.attr
            if extend in (
                "BusinessOperation",
                "BusinessProcess",
                "BusinessService",
                "PollingBusinessService",
                "DuplexService",
                "DuplexProcess",
                "DuplexOperation",
                "InboundAdapter",
                "OutboundAdapter",
            ):
                module = filename_to_module(filename)
                iris_class_name = f"{iris_package_name}.{module}.{klass.name}"
                # strip "_" for iris class name
                iris_class_name = iris_class_name.replace("_", "")
                register_component(module, klass.name, path, overwrite, iris_class_name)


def register_package(
    package: str, path: str, overwrite: int = 1, iris_package_name: str = "Python"
):
    """
    It takes a package name, a path to the package, a flag to overwrite existing files, and the name of
    the iris package to register the files to. It then loops through all the files in the package and
    registers them to the iris package

    :param package: the name of the package you want to register
    :type package: str
    :param path: the path to the directory containing the package
    :type path: str
    :param overwrite: 0 = don't overwrite, 1 = overwrite
    :type overwrite: int
    :param iris_package_name: The name of the package in the Iris package manager
    :type iris_package_name: str
    """
    for filename in os.listdir(os.path.join(path, package)):
        if filename.endswith(".py"):
            _register_file(
                filename, os.path.join(path, package), overwrite, iris_package_name
            )
        else:
            continue


def filename_to_module(filename) -> str:
    """
    It takes a filename and returns the module name

    :param filename: The name of the file to be imported
    :return: The module name
    """
    module = ""

    path, file = os.path.split(filename)
    mod = file.split(".")[0]
    packages = path.replace(os.sep, ("."))
    if len(packages) > 1:
        module = packages + "." + mod
    else:
        module = mod

    return module


def migrate(
    filename=None,
    mode: str | None = None,
    namespace: str | None = None,
    strict_production_validation: bool = False,
):
    """Read a migration file and apply its registrations to IRIS.

    New Python-authored applications should normally export Production objects
    through PRODUCTIONS. CLASSES remains available for standalone bindings,
    native PersistentMessage classes, and legacy migration files. SCHEMAS
    registers Message or PydanticMessage schemas for DTL support.
    """
    settings, path = _load_settings(filename)

    try:
        plan = _build_migration_plan(
            settings,
            path,
            filename,
            mode=mode,
            namespace=namespace,
            strict_production_validation=strict_production_validation,
        )
        print(format_migration_plan(plan))
        _register_settings_components(
            settings,
            path,
            strict_production_validation=strict_production_validation,
        )
        print(
            format_migration_success(
                filename or inspect.getfile(settings), namespace=namespace
            )
        )
    finally:
        _cleanup_sys_path(path)


def explain_migration(
    filename=None,
    mode: str | None = None,
    namespace: str | None = None,
    strict_production_validation: bool = False,
):
    """Return a human-readable migration plan without writing to IRIS."""
    settings, path = _load_settings(filename)
    try:
        plan = _build_migration_plan(
            settings,
            path,
            filename,
            mode=mode,
            namespace=namespace,
            strict_production_validation=strict_production_validation,
        )
        return _format_migration_plan(plan)
    finally:
        _cleanup_sys_path(path)


def format_migration_success(filename, namespace: str | None = None):
    return _format_migration_success(filename, namespace)


def format_migration_plan(plan):
    return _format_migration_plan(plan)


def _format_plan_section(title, entries):
    return _plans_format_plan_section(title, entries)


def _build_migration_plan(
    settings,
    path,
    filename=None,
    mode: str | None = None,
    namespace: str | None = None,
    strict_production_validation: bool = False,
):
    return MigrationPlanner(sys.modules[__name__]).build(
        settings,
        path,
        filename=filename,
        mode=mode,
        namespace=namespace,
        strict_production_validation=strict_production_validation,
    )


def _build_migration_manifest(
    settings,
    path,
    filename=None,
    mode: str | None = None,
    namespace: str | None = None,
    strict_production_validation: bool = False,
) -> MigrationManifest:
    return MigrationManifestBuilder(sys.modules[__name__]).build(
        settings,
        path,
        filename=filename,
        mode=mode,
        namespace=namespace,
        strict_production_validation=strict_production_validation,
    )


def _load_settings(filename):
    """Load a migration settings module.

    Purpose:
        Resolve settings.py as a file-based module and keep imports local to the
        settings file directory for this process.

    Best practices:
        Keep modules imported by settings.py in the same project/package rooted
        near the settings file. Let IoP manage temporary import path setup.

    Common mistakes:
        Do not require users to set PYTHONPATH. Do not mutate environment
        variables to force imports when module/package layout should be fixed.

    Returns:
        tuple: (settings_module, path_added_to_sys)
    """
    path_added = None

    if filename:
        # check if the filename is absolute or relative
        if not os.path.isabs(filename):
            raise ValueError("The filename must be absolute")

        # add the path to the system path to the beginning
        path_added = os.path.normpath(os.path.dirname(filename))
        sys.path.insert(0, path_added)
        # import the specified file using its real module stem. This keeps
        # component classes defined in demo.py as demo.ClassName instead of
        # rewriting them to settings.ClassName.
        settings = import_module_from_path(_module_name_from_file(filename), filename)
    else:
        # import settings from the settings module
        import settings  # type: ignore

    return settings, path_added


def _module_name_from_file(filename: str) -> str:
    return os.path.splitext(os.path.basename(filename))[0]


def _get_folder_path(filename, path_added_to_sys):
    """Get the folder path for migration operations.

    Args:
        filename: Original filename parameter
        path_added_to_sys: Path that was added to sys.path

    Returns:
        str: Folder path to use for migration
    """
    if filename:
        return os.path.dirname(filename)
    else:
        return os.getcwd()


def _classify_class_setting(value, root_path=None):
    return MigrationManifestBuilder(sys.modules[__name__]).classify_class_setting(
        value,
        root_path,
    )


def _validate_dtl_schema_class(cls, setting_name):
    if is_persistent_message_class(cls):
        raise ValueError(
            f"{_python_classname(cls)} is a PersistentMessage. Register it "
            "in CLASSES, not SCHEMAS."
        )
    if not _is_message_schema_class(cls):
        raise ValueError(
            f"{_python_classname(cls)} cannot be registered in "
            f"{setting_name}. Use a Message or PydanticMessage subclass."
        )


def _register_settings_components(
    settings,
    path,
    *,
    strict_production_validation: bool = False,
):
    """Register all components from settings (classes, productions, schemas).

    Args:
        settings: Settings module containing CLASSES, PRODUCTIONS, SCHEMAS
        path: Base path for component registration
    """
    # Use settings file location if path not provided
    if not path:
        path = os.path.dirname(inspect.getfile(settings))

    persistent_registry: dict[str, tuple[type, bool]] = {}
    manifest = _build_migration_manifest(settings, path)
    _execute_migration_manifest(
        manifest,
        persistent_registry=persistent_registry,
        strict_production_validation=strict_production_validation,
    )


def _execute_migration_manifest(
    manifest: MigrationManifest,
    *,
    persistent_registry: dict[str, tuple[type, bool]] | None = None,
    strict_production_validation: bool = False,
) -> None:
    for registration in manifest.class_registrations:
        _execute_class_registration(
            registration,
            persistent_registry=persistent_registry,
        )

    for production in manifest.production_registrations:
        for registration in production.class_registrations:
            _execute_class_registration(
                registration,
                persistent_registry=persistent_registry,
            )
        validate_production_entry(
            production.validation_subject,
            strict=strict_production_validation,
            warn=True,
        )
        register_production_definition(production.name, production.definition)

    for registration in manifest.schema_registrations:
        register_message_schema(registration.schema_class)


def _execute_class_registration(
    registration: ClassRegistration,
    *,
    persistent_registry: dict[str, tuple[type, bool]] | None = None,
) -> None:
    if registration.action == "persistent_message":
        _register_persistent_message_once(
            registration.cls,
            registration.iris_classname,
            sync_schema=registration.sync_schema,
            persistent_registry=persistent_registry,
        )
    elif registration.action in {"component_class", "component_descriptor"}:
        register_component(
            registration.module,
            registration.classname,
            registration.path,
            1,
            registration.iris_classname,
        )
    elif registration.action == "module_file":
        _register_file(
            registration.file,
            registration.path,
            1,
            registration.iris_classname,
        )
    elif registration.action == "package":
        register_package(
            registration.package,
            registration.path,
            1,
            registration.iris_classname,
        )
    elif registration.action == "file":
        _register_file(
            registration.file,
            registration.path,
            1,
            registration.iris_classname,
        )
    elif registration.action == "folder":
        register_folder(registration.path, 1, registration.iris_classname)
    else:
        raise ValueError(f"Invalid migration class action: {registration.action}.")


def _cleanup_sys_path(path):
    """Remove path from sys.path if it was added.

    Args:
        path: Path to remove from sys.path
    """
    remove_sys_path(path)


def import_module_from_path(module_name, file_path):
    """Import one module from an absolute file path.

    Purpose:
        Execute a specific settings or component module by file location
        without relying on global PYTHONPATH configuration.

    Best practices:
        Use absolute paths and stable module/package layout so imports resolve
        from the project directory containing settings.py.

    Common mistakes:
        Do not patch PYTHONPATH or sys.path globally to make imports pass.
        Keep import fixes in project structure and import statements.
    """
    if not os.path.isabs(file_path):
        raise ValueError("The file path must be absolute")

    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot find module named {module_name} at {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def set_classes_settings(class_items, root_path=None, persistent_registry=None):
    """
    It takes a dictionary of classes and returns a dictionary of settings for each class

    :param class_items: a dictionary of classes
    :return: a dictionary of settings for each class
    """
    registrations = MigrationManifestBuilder(sys.modules[__name__]).build_class_registrations(
        class_items,
        root_path,
        source="classes",
    )
    for registration in registrations:
        _execute_class_registration(
            registration,
            persistent_registry=persistent_registry,
        )


def _try_import_class(module_name: str, class_name: str, path: str):
    path = os.path.abspath(os.path.normpath(path))
    fullpath = guess_path(module_name, path)
    with temporary_sys_path(path):
        module = _import_class_module(module_name, fullpath)
    if module is None:
        return None
    try:
        return getattr(module, class_name)
    except AttributeError as exc:
        raise ImportError(
            f"Module {module_name!r} does not define class {class_name!r}."
        ) from exc


def _import_class_module(module_name: str, fullpath: str):
    try:
        return import_module_from_path(module_name, fullpath)
    except FileNotFoundError:
        pass
    except ModuleNotFoundError as exc:
        if not _is_missing_target_module(exc, module_name):
            raise ImportError(
                f"Failed to import {module_name!r} from {fullpath!r}."
            ) from exc
    except Exception as exc:
        raise ImportError(
            f"Failed to import {module_name!r} from {fullpath!r}."
        ) from exc

    try:
        return importlib.import_module(module_name)
    except ModuleNotFoundError as exc:
        if _is_missing_target_module(exc, module_name):
            return None
        raise ImportError(f"Failed to import module {module_name!r}.") from exc


def _is_missing_target_module(exc: ModuleNotFoundError, module_name: str) -> bool:
    missing_name = getattr(exc, "name", None)
    return bool(
        missing_name
        and (module_name == missing_name or module_name.startswith(f"{missing_name}."))
    )


def _register_persistent_message_once(
    msg_cls: type,
    iris_classname: str,
    *,
    sync_schema: bool = True,
    persistent_registry: dict[str, tuple[type, bool]] | None = None,
):
    if persistent_registry is None:
        persistent_registry = _persistent_message_registry

    iris_classname = str(iris_classname or "").strip()
    python_classname = _python_classname(msg_cls)
    existing = persistent_registry.get(iris_classname)
    if existing is not None:
        existing_cls, existing_sync_schema = existing
        if _python_classname(
            existing_cls
        ) != python_classname or existing_sync_schema != bool(sync_schema):
            raise ValueError(
                f"Conflicting PersistentMessage registration for {iris_classname}."
            )
        return

    for existing_iris_classname, (
        existing_cls,
        existing_sync_schema,
    ) in persistent_registry.items():
        if _python_classname(existing_cls) != python_classname:
            continue
        if existing_sync_schema != bool(sync_schema):
            raise ValueError(
                f"Conflicting PersistentMessage sync_schema for {python_classname}."
            )
        raise ValueError(
            f"{python_classname} is already registered as {existing_iris_classname}."
        )

    persistent_registry[iris_classname] = (msg_cls, bool(sync_schema))
    if sync_schema:
        register_persistent_message(msg_cls, iris_classname)
    else:
        register_persistent_message(
            msg_cls,
            iris_classname,
            sync_schema=False,
        )


def set_productions_settings(
    production_list,
    root_path=None,
    persistent_registry=None,
    strict_production_validation: bool = False,
):
    """
    It takes a list of dictionaries and registers the productions
    """
    manifest = MigrationManifest(
        settings="PRODUCTIONS",
        production_registrations=MigrationManifestBuilder(
            sys.modules[__name__]
        ).build_production_registrations(production_list, root_path),
    )
    _execute_migration_manifest(
        manifest,
        persistent_registry=persistent_registry,
        strict_production_validation=strict_production_validation,
    )


def _is_production_object(value) -> bool:
    return (
        hasattr(value, "to_dict")
        and hasattr(value, "component_registrations")
        and hasattr(value, "name")
    )


def _register_production_object_messages(
    production,
    *,
    persistent_registry=None,
):
    registrations = MigrationManifestBuilder(
        sys.modules[__name__]
    ).production_object_class_registrations(production)
    for registration in registrations:
        if registration.action != "persistent_message":
            continue
        _execute_class_registration(
            registration,
            persistent_registry=persistent_registry,
        )


def _register_production_object_components(production, root_path=None):
    registrations = MigrationManifestBuilder(
        sys.modules[__name__]
    ).production_object_class_registrations(production, root_path)
    for registration in registrations:
        if registration.action == "persistent_message":
            continue
        _execute_class_registration(registration)


def handle_items(production, root_path=None):
    registrations = MigrationManifestBuilder(
        sys.modules[__name__]
    ).normalize_production_items(production, root_path)
    for registration in registrations:
        _execute_class_registration(registration)
    return production


def dict_to_xml(json):
    return _dict_to_xml(json)


def register_production(production_name, xml):
    """
    It takes a production name and an xml and registers the production

    :param production_name: the name of the production
    :type production_name: str
    :param xml: the xml of the production
    :type xml: str
    """
    # split the production name in the package name and the production name
    # the production name is the last part of the string
    package = ".".join(production_name.split(".")[:-1])
    production_name = production_name.split(".")[-1]
    stream = string_to_stream(xml)
    # register the production
    raise_on_error(
        _iris.get_iris()
        .cls("IOP.Utils")
        .CreateProduction(package, production_name, stream)
    )


def register_production_definition(production_name: str, production: dict):
    """
    Register a production definition through IRIS Ens.Config objects.

    :param production_name: full IRIS production class name
    :param production: normalized {"Production": {...}} dictionary
    """
    try:
        raise_on_error(
            _iris.get_iris()
            .cls("IOP.Utils")
            .CreateProductionFromJSON(production_name, json.dumps(production))
        )
    except RuntimeError as exc:
        if not _is_missing_production_class_error(exc, production_name):
            raise
        register_production(production_name, dict_to_xml(production))


def _is_missing_production_class_error(exc: RuntimeError, production_name: str) -> bool:
    message = str(exc)
    return "CLASS DOES NOT EXIST" in message and production_name in message


def export_production(production_name):
    """
    It takes a production name and exports the production

    :param production_name: the name of the production
    :type production_name: str
    """
    # export the production
    xdata = _iris.get_iris().cls("IOP.Utils").ExportProduction(production_name)
    # for each chunk of 1024 characters
    string = stream_to_string(xdata)
    # convert the xml to a dictionary
    return xml_to_json(string)


def export_production_connections(production_name):
    """
    Export runtime-discovered production item connections.

    The IRIS helper calls OnGetConnections for each production item and
    returns a JSON-compatible graph payload.
    """
    data = (
        _iris.get_iris().cls("IOP.Utils").ExportProductionConnections(production_name)
    )
    if isinstance(data, dict):
        return data
    return json.loads(data)


def export_production_queue_info(production_name):
    """
    Export queue counters for production items.
    """
    data = _iris.get_iris().cls("IOP.Utils").ExportProductionQueueInfo(production_name)
    if isinstance(data, dict):
        return data
    return json.loads(data)


def apply_production_plan(plan: dict, allow_destructive: bool = False) -> dict:
    """
    Apply a conservative granular production change plan locally in IRIS.
    """
    production_name = plan.get("production") or plan.get("production_name")
    if not production_name:
        raise ValueError("Production plan is missing the production name.")
    data = (
        _iris.get_iris()
        .cls("IOP.Utils")
        .ApplyProductionPlan(
            production_name,
            json.dumps(plan),
            1 if allow_destructive else 0,
        )
    )
    if isinstance(data, dict):
        return data
    return json.loads(data)


def xml_to_json(xml_string: str) -> str:
    return _xml_to_json(xml_string)


def stream_to_string(stream, buffer=1000000) -> str:
    return _stream_to_string(stream, buffer)


def string_to_stream(string: str, buffer=1000000):
    return _string_to_stream(_iris.get_iris(), string, buffer)


def guess_path(module: str, path: str) -> str:
    return _guess_path(module, path)


def _deprecated_static(name: str):
    target = globals()[name]

    @wraps(target)
    def wrapper(*args, **kwargs):
        warnings.warn(
            f"iop.migration.utils._Utils.{name}() and iop.Utils.{name}() are deprecated; "
            f"use iop.migration.utils.{name}() instead. This facade will be removed in v5.0.",
            DeprecationWarning,
            stacklevel=2,
        )
        return globals()[name](*args, **kwargs)

    return staticmethod(wrapper)


class _Utils:
    _persistent_message_registry = _persistent_message_registry
    raise_on_error = _deprecated_static("raise_on_error")
    setup = _deprecated_static("setup")
    register_message_schema = _deprecated_static("register_message_schema")
    register_schema = _deprecated_static("register_schema")
    register_persistent_message = _deprecated_static("register_persistent_message")
    _python_classname = _deprecated_static("_python_classname")
    _is_message_schema_class = _deprecated_static("_is_message_schema_class")
    get_python_settings = _deprecated_static("get_python_settings")
    _get_python_path = _deprecated_static("_get_python_path")
    register_component = _deprecated_static("register_component")
    bind_component = _deprecated_static("bind_component")
    unregister_component = _deprecated_static("unregister_component")
    unbind_component = _deprecated_static("unbind_component")
    list_component_bindings = _deprecated_static("list_component_bindings")
    list_bindings = _deprecated_static("list_bindings")
    register_folder = _deprecated_static("register_folder")
    register_file = _deprecated_static("register_file")
    _register_file = _deprecated_static("_register_file")
    register_package = _deprecated_static("register_package")
    filename_to_module = _deprecated_static("filename_to_module")
    migrate = _deprecated_static("migrate")
    explain_migration = _deprecated_static("explain_migration")
    format_migration_success = _deprecated_static("format_migration_success")
    format_migration_plan = _deprecated_static("format_migration_plan")
    _format_plan_section = _deprecated_static("_format_plan_section")
    _build_migration_plan = _deprecated_static("_build_migration_plan")
    _load_settings = _deprecated_static("_load_settings")
    _module_name_from_file = _deprecated_static("_module_name_from_file")
    _get_folder_path = _deprecated_static("_get_folder_path")
    _classify_class_setting = _deprecated_static("_classify_class_setting")
    _validate_dtl_schema_class = _deprecated_static("_validate_dtl_schema_class")
    _register_settings_components = _deprecated_static("_register_settings_components")
    _cleanup_sys_path = _deprecated_static("_cleanup_sys_path")
    import_module_from_path = _deprecated_static("import_module_from_path")
    set_classes_settings = _deprecated_static("set_classes_settings")
    _try_import_class = _deprecated_static("_try_import_class")
    _register_persistent_message_once = _deprecated_static(
        "_register_persistent_message_once"
    )
    set_productions_settings = _deprecated_static("set_productions_settings")
    _is_production_object = _deprecated_static("_is_production_object")
    _register_production_object_messages = _deprecated_static(
        "_register_production_object_messages"
    )
    _register_production_object_components = _deprecated_static(
        "_register_production_object_components"
    )
    handle_items = _deprecated_static("handle_items")
    dict_to_xml = _deprecated_static("dict_to_xml")
    register_production = _deprecated_static("register_production")
    register_production_definition = _deprecated_static(
        "register_production_definition"
    )
    export_production = _deprecated_static("export_production")
    export_production_connections = _deprecated_static("export_production_connections")
    export_production_queue_info = _deprecated_static("export_production_queue_info")
    xml_to_json = _deprecated_static("xml_to_json")
    stream_to_string = _deprecated_static("stream_to_string")
    string_to_stream = _deprecated_static("string_to_stream")
    guess_path = _deprecated_static("guess_path")
