from __future__ import annotations

from enum import Enum
from typing import Any, overload

_MISSING = object()


class Category(str, Enum):
    """Common IRIS production setting categories for Management Portal grouping."""

    INFO = "Info"
    BASIC = "Basic"
    CONNECTION = "Connection"
    ADDITIONAL = "Additional"
    ALERTING = "Alerting"
    DEV = "Dev"


def _string_value(value: Any) -> str:
    if isinstance(value, Enum):
        return str(value.value)
    return str(value)


class Setting:
    """Metadata for an IRIS production setting."""

    def __init__(
        self,
        default: Any = _MISSING,
        *,
        data_type: Any = None,
        iris_type: str | None = None,
        category: str | Category | None = None,
        required: bool = False,
        description: str = "",
        control: str | None = None,
        exclude: bool = False,
    ):
        self.default = default
        self.data_type = data_type
        self.iris_type = iris_type
        self.category = _string_value(category) if category is not None else None
        self.required = required
        self.description = description or ""
        self.control = control or ""
        self.exclude = exclude
        self.name = ""
        self.owner = None

    def __set_name__(self, owner, name):
        self.name = name
        self.owner = owner

    @overload
    def __get__(self, instance: None, owner: type | None = None) -> Setting: ...

    @overload
    def __get__(self, instance: object, owner: type | None = None) -> Any: ...

    def __get__(self, instance, owner=None):
        if instance is None:
            return self
        if self.name in instance.__dict__:
            return instance.__dict__[self.name]
        if self.default is _MISSING:
            return None
        return self.default

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value

    @property
    def has_default(self) -> bool:
        return self.default is not _MISSING


def setting(default: Any = _MISSING, **kwargs) -> Setting:
    return Setting(default, **kwargs)


class _Controls:
    """Helpers for IRIS production setting editor controls."""

    @staticmethod
    def raw(value: str) -> str:
        """Return an advanced IRIS editor context string unchanged."""
        return value

    @staticmethod
    def selector(
        context: str | None = None, *, multi_select: bool | None = None, **params
    ) -> str:
        """Build an IRIS selector editor context from a context search string."""
        query = []
        if multi_select is not None:
            query.append(f"multiSelect={1 if multi_select else 0}")
        if context:
            if not (context.startswith("{") and context.endswith("}")):
                context = "{" + context + "}"
            query.append(f"context={context}")
        for key, value in params.items():
            if value is not None:
                query.append(f"{key}={value}")
        return "selector" + (f"?{'&'.join(query)}" if query else "")

    @staticmethod
    def production_item(
        *,
        targets: bool = True,
        production_name: str = "@productionId",
        multi_select: bool = False,
    ) -> str:
        """Select production items, normally target components, from a production."""
        context = (
            "Ens.ContextSearch/ProductionItems?"
            f"targets={1 if targets else 0}&productionName={production_name}"
        )
        return _Controls.selector(context, multi_select=multi_select or None)

    @staticmethod
    def partner() -> str:
        """Select a partner setting value."""
        return "partnerSelector"

    @staticmethod
    def rule() -> str:
        """Select an IRIS rule definition."""
        return "ruleSelector"

    @staticmethod
    def credentials() -> str:
        """Select an IRIS credentials entry."""
        return "credentialsSelector"

    @staticmethod
    def directory() -> str:
        """Select a directory path."""
        return "directorySelector"

    @staticmethod
    def file() -> str:
        """Select a file path."""
        return "fileSelector"

    @staticmethod
    def dtl() -> str:
        """Select an IRIS DTL data transformation."""
        return "dtlSelector"

    @staticmethod
    def schedule() -> str:
        """Select an IRIS schedule."""
        return "scheduleSelector"

    @staticmethod
    def ssl_config() -> str:
        """Select an IRIS SSL/TLS configuration."""
        return "sslConfigSelector"

    @staticmethod
    def bpl() -> str:
        """Select an IRIS BPL business process."""
        return "bplSelector"

    @staticmethod
    def character_set() -> str:
        """Select an IRIS character set."""
        return _Controls.selector("Ens.ContextSearch/CharacterSets")

    charset = character_set

    @staticmethod
    def framing(*, host: str = "@currHostId", prop: str = "Framing") -> str:
        """Select a display-list value such as the current host framing option."""
        return _Controls.selector(
            f"Ens.ContextSearch/getDisplayList?host={host}&prop={prop}"
        )

    @staticmethod
    def local_interface() -> str:
        """Select a configured TCP local interface."""
        return _Controls.selector("Ens.ContextSearch/TCPLocalInterfaces")

    @staticmethod
    def schema_category(host: str) -> str:
        """Select a schema category for the specified host expression."""
        return _Controls.selector(f"Ens.ContextSearch/SchemaCategories?host={host}")

    @staticmethod
    def search_table(host: str) -> str:
        """Select a search table class for the specified host expression."""
        return _Controls.selector(f"Ens.ContextSearch/SearchTableClasses?host={host}")


controls = _Controls()
