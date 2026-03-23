"""Structural interface shared by _LocalDirector and _RemoteDirector.

Use ``DirectorProtocol`` for type annotations instead of the concrete union
``_LocalDirector | _RemoteDirector``.  Any object that implements all the
methods below will satisfy the protocol at type-check time (no inheritance
required).
"""

from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable


@runtime_checkable
class DirectorProtocol(Protocol):
    """Interface that both _LocalDirector and _RemoteDirector must satisfy."""

    # ------------------------------------------------------------------
    # Production lifecycle
    # ------------------------------------------------------------------

    def get_default_production(self) -> str: ...
    def set_default_production(self, production_name: str = "") -> None: ...
    def list_productions(self) -> dict: ...
    def status_production(self) -> dict: ...
    def start_production(self, production_name: Optional[str] = None) -> None: ...
    def start_production_with_log(self, production_name: Optional[str] = None) -> None: ...
    def stop_production(self) -> None: ...
    def shutdown_production(self) -> None: ...
    def restart_production(self) -> None: ...
    def update_production(self) -> None: ...

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def log_production_top(self, top: int = 10) -> None: ...
    def log_production(self) -> None: ...

    # ------------------------------------------------------------------
    # Test
    # ------------------------------------------------------------------

    def test_component(
        self,
        target: Optional[str],
        message=None,
        classname: Optional[str] = None,
        body: "str | dict | None" = None,
    ) -> Any: ...

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_production(self, production_name: str) -> dict: ...

    # ------------------------------------------------------------------
    # Init / setup
    # ------------------------------------------------------------------

    def setup(self, path: Optional[str] = None) -> None: ...

    # ------------------------------------------------------------------
    # Migrate
    # ------------------------------------------------------------------

    def migrate(self, path: str) -> None: ...

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    def namespace(self) -> str: ...
