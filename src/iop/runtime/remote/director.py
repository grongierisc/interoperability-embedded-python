"""Remote director: mirrors _Director's interface over the IOP REST API.

Configure via environment variables:
    IOP_URL          Required. e.g. http://localhost:8080
    IOP_USERNAME     Optional. Default: ""
    IOP_PASSWORD     Optional. Default: ""
    IOP_NAMESPACE    Optional. Default: "USER"
    IOP_VERIFY_SSL   Optional. "0"/"false" to disable TLS verification.

Or pass a RemoteSettings dict directly (same shape as REMOTE_SETTINGS in settings.py).
"""

from __future__ import annotations

import signal
import time

import requests

from ..protocol import (
    DirectorProtocol as _DirectorProtocol,  # noqa: F401 --- IGNORE ---
)
from .client import _RemoteClient
from .migration import upload_migration
from .settings import (
    get_remote_settings,
)
from .settings import (
    load_remote_settings_from_file as _load_remote_settings_from_file,
)
from .setup import setup_remote_classes

__all__ = [
    "_RemoteDirector",
    "_load_remote_settings_from_file",
    "_print_log_entry",
    "get_remote_settings",
]


class _RemoteDirector(_RemoteClient, _DirectorProtocol):
    """Implements DirectorProtocol over the IOP REST API."""

    # ------------------------------------------------------------------
    # Production lifecycle
    # ------------------------------------------------------------------

    def get_default_production(self) -> str:
        data = self._check_error(self._get("/default"))
        return data.get("production") or "Not defined"

    def set_default_production(self, production_name: str = "") -> None:
        self._check_error(self._put("/default", {"production": production_name}))

    def list_productions(self) -> dict:
        return self._check_error(self._get("/list"))

    def status_production(self) -> dict:
        data = self._check_error(self._get("/status"))
        if not data.get("production"):
            data["production"] = self.get_default_production()
        return data

    def start_production(self, production_name: str | None = None) -> None:
        body: dict = {}
        if production_name:
            body["production"] = production_name
        self._check_error(self._post("/start", body))

    def start_production_with_log(self, production_name: str | None = None) -> None:
        """Start remotely then stream the log until Ctrl-C (which also stops)."""
        self.start_production(production_name)
        prod = production_name or self.get_default_production()
        print(f"Production '{prod}' started. Streaming log — Ctrl-C to stop.")
        running = True

        def _sigint(sig, frame):  # pragma: no cover
            nonlocal running
            running = False

        signal.signal(signal.SIGINT, _sigint)

        last_id = 0
        for entry in self._get_log_entries(top=10):
            _print_log_entry(entry)
            last_id = max(last_id, entry.get("id", 0))

        while running:
            time.sleep(1)
            entries = self._get_log_entries(since_id=last_id)
            for entry in entries:
                _print_log_entry(entry)
                last_id = max(last_id, entry.get("id", 0))

        self.stop_production()

    def stop_production(self) -> None:
        self._check_error(self._post("/stop"))

    def shutdown_production(self) -> None:
        self._check_error(self._post("/kill"))

    def restart_production(self) -> None:
        self._check_error(self._post("/restart"))

    def update_production(self) -> None:
        self._check_error(self._post("/update"))

    def start_component(self, component_name: str) -> None:
        self._check_error(
            self._post("/component/start", {"component": component_name})
        )

    def stop_component(self, component_name: str) -> None:
        self._check_error(
            self._post("/component/stop", {"component": component_name})
        )

    def restart_component(self, component_name: str) -> None:
        self._check_error(
            self._post("/component/restart", {"component": component_name})
        )

    def list_bindings(self, unused_only: bool = False) -> list[dict]:
        params = {"unused": 1} if unused_only else {}
        data = self._check_error(self._get("/bindings", params))
        return data if isinstance(data, list) else []

    def unbind_component(self, iris_classname: str) -> None:
        self._check_error(self._delete("/binding", {"class": iris_classname}))

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _get_log_entries(
        self,
        top: int = 10,
        since_id: int | None = None,
    ) -> list[dict]:
        params: dict = {}
        if since_id is not None:
            params["since_id"] = since_id
        else:
            params["top"] = top
        data = self._check_error(self._get("/log", params))
        return data if isinstance(data, list) else []

    def log_production_top(self, top: int = 10) -> None:
        entries = self._get_log_entries(top=top)
        for entry in reversed(entries):
            _print_log_entry(entry)

    def log_production(self) -> None:
        """Stream log continuously until Ctrl-C."""
        running = True

        def _sigint(sig, frame):  # pragma: no cover
            nonlocal running
            running = False

        signal.signal(signal.SIGINT, _sigint)

        last_id = 0
        for entry in self._get_log_entries(top=10):
            _print_log_entry(entry)
            last_id = max(last_id, entry.get("id", 0))

        while running:
            time.sleep(1)
            entries = self._get_log_entries(since_id=last_id)
            for entry in entries:
                _print_log_entry(entry)
                last_id = max(last_id, entry.get("id", 0))

    # ------------------------------------------------------------------
    # Test
    # ------------------------------------------------------------------

    def test_component(
        self,
        target: str | None,
        message=None,  # ignored remotely — not serialisable over HTTP
        classname: str | None = None,
        body: str | dict | None = None,
        restart: bool = True,
    ) -> dict:
        """Returns a dict: {"classname": "...", "body": "...", "truncated": false}.

        If *restart* is True the target component is stopped and restarted on
        the server before the test message is dispatched.
        """
        payload: dict = {"target": target or ""}
        if classname:
            payload["classname"] = classname
        if body is not None:
            payload["body"] = body
        if restart:
            payload["restart"] = True
        try:
            return self._check_error(self._post("/test", payload))
        except requests.exceptions.HTTPError as exc:
            try:
                err_msg = exc.response.json().get("error", str(exc))
            except Exception:
                err_msg = str(exc)
            raise RuntimeError(err_msg) from exc
        except requests.exceptions.RequestException as exc:
            raise RuntimeError(f"Remote test component error: {exc}") from exc

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_production(self, production_name: str) -> dict:
        return self._check_error(self._get("/export", {"production": production_name}))

    def export_production_connections(self, production_name: str) -> dict:
        return self._check_error(
            self._get("/connections", {"production": production_name})
        )

    def export_production_queue_info(self, production_name: str) -> dict:
        return self._check_error(self._get("/queues", {"production": production_name}))

    def apply_production_plan(
        self,
        plan: dict,
        allow_destructive: bool = False,
    ) -> dict:
        raise RuntimeError(
            "Remote production plan apply is not supported in v1. "
            "Run apply from a local IRIS environment."
        )

    # ------------------------------------------------------------------
    # Migrate
    # ------------------------------------------------------------------

    def migrate(
        self,
        path: str,
        strict_production_validation: bool = False,
    ) -> None:
        upload_migration(
            self,
            path,
            strict_production_validation=strict_production_validation,
        )

    # ------------------------------------------------------------------
    # Init / setup — uploads .cls files via the Atelier API
    # ------------------------------------------------------------------

    def setup(self, path: str | None = None) -> None:
        setup_remote_classes(self, path)

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    @property
    def namespace(self) -> str:
        return self._namespace


# ------------------------------------------------------------------
# Shared helpers
# ------------------------------------------------------------------


def _print_log_entry(entry: dict) -> None:
    print(
        entry.get("time_logged", ""),
        entry.get("type", ""),
        entry.get("config_name", ""),
        entry.get("job", ""),
        entry.get("message_id", ""),
        entry.get("session_id", ""),
        entry.get("source_class", ""),
        entry.get("source_method", ""),
        entry.get("text", ""),
    )
