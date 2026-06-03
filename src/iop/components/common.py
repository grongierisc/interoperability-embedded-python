import inspect
import traceback
import warnings
from enum import Enum
from types import UnionType
from typing import (
    Annotated,
    Any,
    ClassVar,
    Union,
    get_args,
    get_origin,
    get_type_hints,
)

from ..runtime import iris as _iris
from .debugpy import debugpython
from .log_manager import LogManager, logging
from .settings import Setting

_NO_VALUE = object()

_EXCLUDED_SETTING_NAMES = {
    "INFO_URL",
    "ICON_URL",
    "PERSISTENT_PROPERTY_LIST",
    "log_to_console",
    "logger",
    "iris_handle",
    "DISPATCH",
    "adapter",
    "Adapter",
    "buffer",
    "BusinessHost",
    "business_host",
    "business_host_python",
}

_PYTHON_TYPE_TO_IRIS = {
    int: "Integer",
    float: "Numeric",
    complex: "Numeric",
    bool: "Boolean",
    str: "String",
}

_SIMPLE_TYPE_NAMES = {
    "int": "Integer",
    "integer": "Integer",
    "float": "Numeric",
    "complex": "Numeric",
    "number": "Numeric",
    "numeric": "Numeric",
    "bool": "Boolean",
    "boolean": "Boolean",
    "str": "String",
    "string": "String",
}


def _string_metadata(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


def _type_hints_with_extras(cls) -> dict[str, Any]:
    try:
        return get_type_hints(cls, include_extras=True)
    except Exception:
        hints: dict[str, Any] = {}
        for base in reversed(inspect.getmro(cls)):
            hints.update(getattr(base, "__annotations__", {}))
        return hints


def _unwrap_annotated(data_type: Any) -> tuple[Any, tuple[Any, ...]]:
    if get_origin(data_type) is Annotated:
        args = get_args(data_type)
        if args:
            return args[0], args[1:]
    return data_type, ()


def _setting_from_annotation(data_type: Any) -> tuple[Any, Setting | None]:
    data_type, metadata = _unwrap_annotated(data_type)
    setting = None
    for item in metadata:
        if isinstance(item, Setting):
            setting = item
    return data_type, setting


def _unwrap_optional(data_type: Any) -> Any:
    origin = get_origin(data_type)
    if origin in (Union, UnionType):
        args = [arg for arg in get_args(data_type) if arg is not type(None)]
        if len(args) == 1:
            return args[0]
    return data_type


def _iris_data_type(data_type: Any) -> str | None:
    if data_type is None or data_type == "":
        return None

    data_type, _ = _unwrap_annotated(data_type)
    data_type = _unwrap_optional(data_type)

    if data_type is Any or data_type is object:
        return "String"

    if isinstance(data_type, str):
        data_type = data_type.strip()
        return _SIMPLE_TYPE_NAMES.get(data_type.lower(), data_type)

    if data_type in _PYTHON_TYPE_TO_IRIS:
        return _PYTHON_TYPE_TO_IRIS[data_type]

    origin = get_origin(data_type)
    if origin in _PYTHON_TYPE_TO_IRIS:
        return _PYTHON_TYPE_TO_IRIS[origin]
    if origin is not None:
        return "String"

    return None


def _is_setting_member(name: str, value: Any) -> bool:
    if name.startswith("_") or name in _EXCLUDED_SETTING_NAMES:
        return False
    return not (
        inspect.ismethod(value) or inspect.isfunction(value) or inspect.isclass(value)
    )


def _custom_init_owner(cls: type) -> type | None:
    for base in inspect.getmro(cls):
        init = base.__dict__.get("__init__", _NO_VALUE)
        if init is _NO_VALUE or init is object.__init__:
            continue
        return base
    return None


class _Common:
    """Base class that defines common methods for all component types.

    Provides core functionality like initialization, teardown, connection handling
    and message type checking that is shared across component types.
    """

    INFO_URL: ClassVar[str]
    ICON_URL: ClassVar[str]
    iris_handle: Any = None
    _log_to_console: bool = False
    _logger: logging.Logger | None = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls._warn_if_custom_init_defined(stacklevel=2)

    @classmethod
    def _custom_init_warning_message(cls) -> str | None:
        if _custom_init_owner(cls) is None:
            return None
        classname = f"{cls.__module__}.{cls.__qualname__}"
        return (
            f"{classname} defines or inherits __init__(), but IoP/IRIS "
            "instantiates components with __new__() and does not call "
            "__init__(). Move startup logic to on_init(); use class attributes "
            "or iop.Setting for configurable defaults."
        )

    @classmethod
    def _warn_if_custom_init_defined(cls, stacklevel: int = 2) -> None:
        message = cls._custom_init_warning_message()
        if message is None:
            return
        warnings.warn(message, RuntimeWarning, stacklevel=stacklevel)

    def _log_custom_init_warning(self) -> None:
        message = self.__class__._custom_init_warning_message()
        if message is None:
            return
        try:
            self.log_warning(message)
        except Exception:
            try:
                warnings.warn(message, RuntimeWarning, stacklevel=2)
            except Exception:
                pass

    def _warn_if_custom_init(self) -> None:
        """Metadata-safe warning hook for ObjectScript __new__ allocations."""
        self._log_custom_init_warning()

    @staticmethod
    def get_adapter_type() -> str | None:
        """Get the adapter type for this component. Override in subclasses."""
        return None

    @property
    def logger(self) -> logging.Logger:
        if self._logger is None:
            self._logger = LogManager.get_logger(
                self.__class__.__name__, self.log_to_console
            )
        return self._logger

    @logger.setter
    def logger(self, value: logging.Logger) -> None:
        self._logger = value

    @property
    def log_to_console(self) -> bool:
        return self._log_to_console

    @log_to_console.setter
    def log_to_console(self, value: bool) -> None:
        self._log_to_console = value
        self.logger = LogManager.get_logger(self.__class__.__name__, value)

    # Lifecycle methods
    def on_init(self) -> None:
        """Initialize component when started."""
        pass

    def on_tear_down(self) -> None:
        """Clean up component before termination."""
        pass

    def on_connected(self) -> None:
        """Handle component connection/reconnection."""
        pass

    # Internal dispatch methods
    def _dispatch_on_connected(self, host_object: Any) -> None:
        self.on_connected()

    def _dispatch_on_init(self, host_object: Any) -> None:
        """Initialize component when started."""
        self._log_custom_init_warning()
        self.on_init()

    def _dispatch_on_tear_down(self, host_object: Any) -> None:
        self.on_tear_down()

    def _set_iris_handles(self, handle_current: Any, handle_partner: Any) -> None:
        """Internal method to set IRIS handles."""
        pass

    def _debugpy(self, host) -> None:
        """Set up debugpy for debugging."""
        if debugpython is not None:
            debugpython(self=self, host_object=host)

    # Component information methods
    @classmethod
    def _get_info(cls) -> list[str]:
        """Get component configuration information.

        Returns information used to display in Production config UI including:
        - Superclass
        - Description
        - InfoURL
        - IconURL
        - Adapter type (for Business Services/Operations)
        """
        ret = []
        desc = ""
        info_url = ""
        icon_url = ""
        super_class = ""
        adapter = ""
        try:
            # Get tuple of the class's base classes and loop through them until we find one of the public component classes.
            classes = inspect.getmro(cls)
            for cl in classes:
                classname = str(cl)[7:-1]
                if classname in [
                    "'iop.BusinessService'",
                    "'iop.BusinessOperation'",
                    "'iop.DuplexOperation'",
                    "'iop.DuplexService'",
                ]:
                    # Remove the apostrophes and set as super_class, then find if it uses an adapter
                    super_class = classname[1:-1]
                    adapter = cls.get_adapter_type() or ""
                    break
                elif classname in [
                    "'iop.BusinessProcess'",
                    "'iop.DuplexProcess'",
                    "'iop.InboundAdapter'",
                    "'iop.OutboundAdapter'",
                ]:
                    # Remove the apostrophes and set as super_class
                    super_class = classname[1:-1]
                    break

            if "" == super_class:
                return []
            ret.append(super_class)

            # Get the class documentation, if any
            class_desc = inspect.getdoc(cls)
            super_desc = inspect.getdoc(classes[1])
            if class_desc != super_desc:
                desc = class_desc
            ret.append(str(desc))

            info_url = inspect.getattr_static(cls, "INFO_URL", "")
            icon_url = inspect.getattr_static(cls, "ICON_URL", "")

            ret.append(info_url)
            ret.append(icon_url)

            if "" != adapter:
                ret.append(adapter)
        except Exception as e:
            raise e
        return ret

    @classmethod
    def _get_properties(cls) -> list[list[Any]]:
        """Get component properties for Production configuration.

        Returns list of property definitions containing:
        - Property name
        - Data type
        - Default value
        - Required flag
        - Category
        - Description
        - Control/editor context

        Only includes non-private class attributes and properties.
        """
        ret = []
        try:
            annotations = _type_hints_with_extras(cls)
            members = dict(inspect.getmembers(cls))

            names = [
                name
                for name, value in members.items()
                if _is_setting_member(name, value)
            ]
            for name in annotations:
                if (
                    name in names
                    or name.startswith("_")
                    or name in _EXCLUDED_SETTING_NAMES
                ):
                    continue
                value = members.get(name, _NO_VALUE)
                if value is not _NO_VALUE and not _is_setting_member(name, value):
                    continue
                names.append(name)

            for name in names:
                member_exists = name in members
                val = members.get(name, "")
                annotated_type, annotated_setting = _setting_from_annotation(
                    annotations.get(name)
                )
                value_setting = val if isinstance(val, Setting) else None
                setting_info = value_setting or annotated_setting

                if setting_info is not None and setting_info.exclude:
                    continue

                req = bool(setting_info.required) if setting_info is not None else False
                cat = setting_info.category if setting_info is not None else ""
                desc = setting_info.description if setting_info is not None else ""
                control = setting_info.control if setting_info is not None else ""

                if value_setting is not None:
                    val = value_setting.default if value_setting.has_default else ""
                elif (
                    not member_exists
                    and annotated_setting is not None
                    and annotated_setting.has_default
                ):
                    val = annotated_setting.default
                elif not member_exists:
                    val = ""

                if isinstance(val, property) or (val is None):
                    val = ""

                if setting_info is not None and setting_info.iris_type:
                    data_type = setting_info.iris_type
                else:
                    data_type_source = (
                        setting_info.data_type
                        if setting_info is not None and setting_info.data_type
                        else annotated_type
                    )
                    data_type = _iris_data_type(data_type_source)
                    if data_type is None:
                        data_type = _iris_data_type(type(val)) or "String"

                # Legacy attr_info() support. Values supplied here keep working
                # and can also provide the new control/editor context field.
                if hasattr(cls, name + "_info"):
                    func = getattr(cls, name + "_info")
                    if callable(func):
                        info_annotations = getattr(func, "__annotations__", {}).get(
                            "return"
                        )
                        if info_annotations is not None:
                            if bool(info_annotations.get("ExcludeFromSettings")):
                                continue
                            req = bool(info_annotations.get("IsRequired", req))
                            cat = _string_metadata(
                                info_annotations.get("Category", cat)
                            )
                            desc = _string_metadata(
                                info_annotations.get("Description", desc)
                            )
                            control = _string_metadata(
                                info_annotations.get(
                                    "Control",
                                    info_annotations.get("EditorContext", control),
                                )
                            )
                            dt = info_annotations.get("DataType")
                            if (dt is not None) and ("" != dt):
                                data_type = _iris_data_type(dt) or str(dt)
                        default = func()
                        if default is not None:
                            val = default

                ret.append(
                    [
                        name,  # Name
                        data_type,  # DataType
                        val,  # Default Value
                        req,  # Required
                        _string_metadata(cat),  # Category
                        _string_metadata(desc),  # Description
                        _string_metadata(control),  # Control/editor context
                    ]
                )
        except Exception as exc:
            raise RuntimeError(
                f"Failed to build settings metadata for "
                f"{cls.__module__}.{cls.__qualname__}"
            ) from exc
        return ret

    # Logging methods
    def _log(self) -> tuple[str, str | None]:
        """Get class and method name for logging.

        Returns:
            Tuple of (class_name, method_name)
        """
        current_class = self.__class__.__name__
        current_method = None
        try:
            frame = traceback.extract_stack()[-4]
            current_method = frame.name
        except Exception:
            pass
        return current_class, current_method

    def _logging(
        self, message: str, level: int, to_console: bool | None = None
    ) -> None:
        """Write log entry.

        Args:
            message: Message to log
            level: Log level
            to_console: If True, log to console instead of IRIS
        """
        current_class, current_method = self._log()
        if to_console is None:
            to_console = self.log_to_console
        self.logger.log(
            level,
            message,
            extra={
                "to_console": to_console,
                "class_name": current_class,
                "method_name": current_method,
            },
        )

    def trace(self, message: str, to_console: bool | None = None) -> None:
        """Write trace log entry.

        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self._logging(message, logging.DEBUG, to_console)

    def log_info(self, message: str, to_console: bool | None = None) -> None:
        """Write info log entry.

        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self._logging(message, logging.INFO, to_console)

    def log_alert(self, message: str, to_console: bool | None = None) -> None:
        """Write alert log entry.

        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self._logging(message, logging.CRITICAL, to_console)

    def log_warning(self, message: str, to_console: bool | None = None) -> None:
        """Write warning log entry.

        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self._logging(message, logging.WARNING, to_console)

    def log_error(self, message: str, to_console: bool | None = None) -> None:
        """Write error log entry.

        Args:
            message: Message to log
            to_console: If True, log to console instead of IRIS
        """
        self._logging(message, logging.ERROR, to_console)

    def log_assert(self, message: str) -> None:
        """Write a log entry of type "assert". Log entries can be viewed in the management portal.

        Parameters:
        message: a string that is written to the log.
        """
        iris = _iris.get_iris()
        current_class, current_method = self._log()
        iris.cls("Ens.Util.Log").LogAssert(current_class, current_method, message)

