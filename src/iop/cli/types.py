from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class CommandType(Enum):
    DEFAULT = auto()
    LIST = auto()
    START = auto()
    STOP = auto()
    KILL = auto()
    RESTART = auto()
    STATUS = auto()
    TEST = auto()
    VERSION = auto()
    EXPORT = auto()
    MIGRATE = auto()
    LOG = auto()
    QUEUE = auto()
    INIT = auto()
    BINDINGS = auto()
    UNBIND = auto()
    HELP = auto()
    UPDATE = auto()


@dataclass
class CommandArgs:
    """Container for parsed command arguments."""

    default: str | None = None
    list: bool = False
    start: str | None = None
    detach: bool = False
    stop: bool = False
    kill: bool = False
    restart: bool = False
    status: bool = False
    migrate: str | None = None
    export: str | None = None
    export_format: str = "json"
    version: bool = False
    log: str | None = None
    queue: str | None = None
    init: str | None = None
    bindings: bool = False
    unused: bool = False
    unbind: str | None = None
    test: str | None = None
    classname: str | None = None
    body: str | None = None
    namespace: str | None = None
    force_local: bool = False
    remote_settings: str | None = None
    update: bool = False
    migration_plan: bool = False
    strict_production_validation: bool = False
