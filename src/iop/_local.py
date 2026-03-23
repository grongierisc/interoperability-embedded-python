"""Local director: thin instance-method wrapper around static _Director calls.

This gives the CLI a uniform interface so it can swap between
_LocalDirector and _RemoteDirector without any branching.
"""

from __future__ import annotations

import json
import os
from typing import Optional

from ._director import _Director
from ._utils import _Utils
from ._director_protocol import DirectorProtocol as _DirectorProtocol  # noqa: F401 --- IGNORE ---


class _LocalDirector(_DirectorProtocol):
    """Local director: thin instance-method wrapper around static _Director calls."""

    # ------------------------------------------------------------------
    # Production lifecycle
    # ------------------------------------------------------------------

    def get_default_production(self) -> str:
        return _Director.get_default_production()

    def set_default_production(self, production_name: str = "") -> None:
        _Director.set_default_production(production_name)

    def list_productions(self) -> dict:
        return _Director.list_productions()

    def status_production(self) -> dict:
        return _Director.status_production()

    def start_production(self, production_name: Optional[str] = None) -> None:
        _Director.start_production(production_name)

    def start_production_with_log(self, production_name: Optional[str] = None) -> None:
        _Director.start_production_with_log(production_name)

    def stop_production(self) -> None:
        _Director.stop_production()

    def shutdown_production(self) -> None:
        _Director.shutdown_production()

    def restart_production(self) -> None:
        _Director.restart_production()

    def update_production(self) -> None:
        _Director.update_production()

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def log_production_top(self, top: int = 10) -> None:
        _Director.log_production_top(top)

    def log_production(self) -> None:
        _Director.log_production()

    # ------------------------------------------------------------------
    # Test
    # ------------------------------------------------------------------

    def test_component(
        self,
        target: Optional[str],
        message=None,
        classname: Optional[str] = None,
        body: "str | dict | None" = None,
        restart: bool = True,  # ignored locally — included to satisfy DirectorProtocol
    ):
        return _Director.test_component(target, message, classname, body)

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_production(self, production_name: str) -> dict:
        return json.loads(_Utils.export_production(production_name))

    # ------------------------------------------------------------------
    # Init / setup
    # ------------------------------------------------------------------

    def setup(self, path: Optional[str] = None) -> None:
        _Utils.setup(path)

    # ------------------------------------------------------------------
    # Migrate
    # ------------------------------------------------------------------

    def migrate(self, path: str) -> None:
        _Utils.migrate(path)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    def namespace(self) -> str:
        return os.getenv('IRISNAMESPACE', 'not set')
