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

import json
import os
import signal
import time
from typing import Any, Dict, List, Optional, Union

import requests
import urllib3


class _RemoteDirector:
    """Implements the same interface as _Director but dispatches over HTTP."""

    def __init__(self, remote_settings: Dict[str, Any]) -> None:
        self._base = remote_settings["url"].rstrip("/") + "/api/iop"
        self._auth = (
            remote_settings.get("username", ""),
            remote_settings.get("password", ""),
        )
        self._namespace: str = remote_settings.get("namespace", "USER")
        self._verify: bool = remote_settings.get("verify_ssl", True)
        if not self._verify:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, path: str, params: Optional[dict] = None) -> Any:
        p = {"namespace": self._namespace, **(params or {})}
        resp = requests.get(
            f"{self._base}{path}", params=p, auth=self._auth,
            verify=self._verify, timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, body: Optional[dict] = None) -> Any:
        resp = requests.post(
            f"{self._base}{path}", json=(body or {}),
            params={"namespace": self._namespace},
            auth=self._auth, verify=self._verify, timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, body: Optional[dict] = None) -> Any:
        resp = requests.put(
            f"{self._base}{path}", json=(body or {}),
            params={"namespace": self._namespace},
            auth=self._auth, verify=self._verify, timeout=30,
        )
        resp.raise_for_status()
        return resp.json()

    def _check_error(self, data: Any) -> Any:
        if isinstance(data, dict) and "error" in data:
            raise RuntimeError(data["error"])
        return data

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

    def start_production(self, production_name: Optional[str] = None) -> None:
        body: dict = {}
        if production_name:
            body["production"] = production_name
        self._check_error(self._post("/start", body))

    def start_production_with_log(self, production_name: Optional[str] = None) -> None:
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

    def restart_production(self) -> dict:
        return self._check_error(self._post("/restart"))

    def update_production(self) -> dict:
        return self._check_error(self._post("/update"))

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _get_log_entries(
        self,
        top: int = 10,
        since_id: Optional[int] = None,
    ) -> List[dict]:
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
        target: Optional[str],
        message=None,           # ignored remotely — not serialisable over HTTP
        classname: Optional[str] = None,
        body: Optional[Union[str, dict]] = None,
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

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_production(self, production_name: str) -> dict:
        import xmltodict  # already required by _utils

        data = self._check_error(
            self._get("/export", {"production": production_name})
        )
        xml = data.get("xml", "")
        if not xml:
            return {}

        def _postprocessor(path, key, value):
            return key, "" if value is None else value

        return xmltodict.parse(xml, postprocessor=_postprocessor)


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


def _load_remote_settings_from_file(settings_path: str) -> Optional[Dict[str, Any]]:
    """Load a ``REMOTE_SETTINGS`` dict from an arbitrary settings.py file."""
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("_iop_settings_remote", settings_path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        remote = getattr(mod, "REMOTE_SETTINGS", None)
        if isinstance(remote, dict) and "url" in remote:
            return remote
    except Exception:
        pass
    return None


def get_remote_settings(
    explicit_settings_path: Optional[str] = None,
    fallback_settings_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """Detect remote settings from the environment or an explicit file.

    Priority:
    1. ``IOP_URL`` env var (direct inline configuration).
    2. ``explicit_settings_path`` — the file supplied via ``--remote-settings``.
    3. ``IOP_SETTINGS`` env var pointing to a settings.py with ``REMOTE_SETTINGS``.
    4. ``fallback_settings_path`` — e.g. the file passed via ``-m settings.py``;
       its ``REMOTE_SETTINGS`` dict is used when present.
    """
    url = os.environ.get("IOP_URL")
    if url:
        verify_raw = os.environ.get("IOP_VERIFY_SSL", "1")
        return {
            "url": url,
            "username": os.environ.get("IOP_USERNAME", ""),
            "password": os.environ.get("IOP_PASSWORD", ""),
            "namespace": os.environ.get("IOP_NAMESPACE", "USER"),
            "verify_ssl": verify_raw.lower() not in ("0", "false"),
        }

    for path in filter(None, [
        explicit_settings_path,
        os.environ.get("IOP_SETTINGS"),
        fallback_settings_path,
    ]):
        result = _load_remote_settings_from_file(path)
        if result:
            return result

    return None

