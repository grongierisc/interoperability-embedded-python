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

import ast
import os
import signal
import time
from typing import Any

import requests
import urllib3

from .protocol import DirectorProtocol as _DirectorProtocol  # noqa: F401 --- IGNORE ---


class _RemoteDirector(_DirectorProtocol):
    """Implements DirectorProtocol over the IOP REST API."""

    def __init__(self, remote_settings: dict[str, Any]) -> None:
        self._url = remote_settings["url"].rstrip("/")
        self._base = self._url + "/api/iop"
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

    @staticmethod
    def _raise_for_status(resp: requests.Response) -> None:
        """Like resp.raise_for_status() but includes the response body error message."""
        if not resp.ok:
            try:
                body = resp.json()
                error = body.get("error") or body.get("message") or resp.text
            except Exception:
                error = resp.text or resp.reason
            raise requests.exceptions.HTTPError(
                f"{resp.status_code} {resp.reason}: {error}",
                response=resp,
            )

    def _get(self, path: str, params: dict | None = None) -> Any:
        p = {"namespace": self._namespace, **(params or {})}
        resp = requests.get(
            f"{self._base}{path}",
            params=p,
            auth=self._auth,
            verify=self._verify,
            timeout=30,
        )
        self._raise_for_status(resp)
        return resp.json()

    def _post(self, path: str, body: dict | None = None) -> Any:
        resp = requests.post(
            f"{self._base}{path}",
            json=(body or {}),
            params={"namespace": self._namespace},
            auth=self._auth,
            verify=self._verify,
            timeout=30,
        )
        self._raise_for_status(resp)
        return resp.json()

    def _put(self, path: str, body: dict | None = None) -> Any:
        resp = requests.put(
            f"{self._base}{path}",
            json=(body or {}),
            params={"namespace": self._namespace},
            auth=self._auth,
            verify=self._verify,
            timeout=30,
        )
        self._raise_for_status(resp)
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

    # ------------------------------------------------------------------
    # Migrate
    # ------------------------------------------------------------------

    def migrate(self, path: str) -> None:
        """Upload .py and .cls files from *path*'s folder to remote IRIS via the IOP migrate API.

        *path* must be an absolute path to the Python migration entrypoint
        file. The containing directory (and sub-directories) will be walked for
        ``.py`` / ``.cls`` files. ``REMOTE_SETTINGS`` fields (package,
        namespace, remote_folder) are read from that same entrypoint when
        present; otherwise the director's own namespace / defaults are used.
        """
        import importlib.util

        folder = os.path.dirname(path)

        # Try to read optional keys from the settings file
        package = "python"
        remote_folder = ""
        try:
            spec = importlib.util.spec_from_file_location("_iop_migrate_settings", path)
            mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
            spec.loader.exec_module(mod)  # type: ignore[union-attr]
            rs = getattr(mod, "REMOTE_SETTINGS", {})
            package = rs.get("package", package)
            remote_folder = rs.get("remote_folder", remote_folder)
        except Exception:
            pass

        body: list[dict] = []
        settings_file = os.path.basename(path)
        for dirpath, _, filenames in os.walk(folder):
            for fname in sorted(filenames):
                if not (fname.endswith(".py") or fname.endswith(".cls")):
                    continue
                full = os.path.join(dirpath, fname)
                rel = os.path.relpath(full, folder).replace(os.sep, "/")
                with open(full, encoding="utf-8") as fh:
                    body.append({"name": rel, "data": fh.read()})

        payload = {
            "namespace": self._namespace,
            "package": package,
            "remote_folder": remote_folder,
            "settings_file": settings_file,
            "body": body,
        }
        resp = requests.put(
            f"{self._base}/migrate",
            json=payload,
            params={"namespace": self._namespace},
            auth=self._auth,
            verify=self._verify,
            timeout=30,
        )
        self._raise_for_status(resp)
        # Server returns $$$OK (the integer 1) on success — not meaningful to print

    # ------------------------------------------------------------------
    # Init / setup — uploads .cls files via the Atelier API
    # ------------------------------------------------------------------

    def setup(self, path: str | None = None) -> None:
        """Upload and compile IOP .cls files to remote IRIS via the Atelier REST API.

        When *path* is ``None`` the bundled ``iop/cls/`` directory is used.
        Any explicit *path* must point to a directory containing ``.cls`` files.
        """
        import importlib.resources

        paths_to_upload: list[str] = []
        if path is None:
            try:
                paths_to_upload.append(
                    str(importlib.resources.files("iop").joinpath("cls"))
                )
            except ModuleNotFoundError:
                pass
        else:
            paths_to_upload.append(path)

        atelier_base = f"{self._url}/api/atelier/v1"
        doc_names: list[str] = []

        for cls_root in paths_to_upload:
            for dirpath, _, filenames in os.walk(cls_root):
                for fname in sorted(filenames):
                    if not fname.endswith(".cls"):
                        continue
                    full_path = os.path.join(dirpath, fname)
                    doc_name = (
                        os.path.relpath(full_path, cls_root)
                        .replace(os.sep, ".")
                        .replace("/", ".")
                    )
                    with open(full_path, encoding="utf-8") as fh:
                        content = fh.read().splitlines()
                    resp = requests.put(
                        f"{atelier_base}/{self._namespace}/doc/{doc_name}",
                        json={"enc": False, "content": content},
                        params={"ignoreConflict": "1"},
                        auth=self._auth,
                        verify=self._verify,
                        timeout=30,
                    )
                    self._raise_for_status(resp)
                    doc_names.append(doc_name)
                    print(f"Uploaded: {doc_name}")

        if not doc_names:
            raise RuntimeError("No .cls files found to upload.")

        # Compile all uploaded documents in one request
        resp = requests.post(
            f"{atelier_base}/{self._namespace}/action/compile",
            json=doc_names,
            params={"flags": "cuk"},
            auth=self._auth,
            verify=self._verify,
            timeout=120,
        )
        self._raise_for_status(resp)
        result = resp.json()
        for line in result.get("console", []):
            if line:
                print(line)
        errors = result.get("status", {}).get("errors", [])
        if errors:
            raise RuntimeError(f"Compilation errors: {errors}")
        print(
            "\n.cls files uploaded and compiled successfully."
            "\nNext step: ensure the 'iop' Python package is installed on the IRIS server:"
            "\n  python3 -m pip install iris-pex-embedded-python"
            "\nThis is required for full IOP Support; without it, only the migrate() and export_production() methods will work remotely."
        )

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


def _load_remote_settings_from_file(settings_path: str) -> dict[str, Any] | None:
    """Load a literal ``REMOTE_SETTINGS`` dict without executing the file."""
    try:
        with open(settings_path, encoding="utf-8") as fh:
            tree = ast.parse(fh.read(), filename=settings_path)
    except (OSError, SyntaxError):
        return None

    try:
        for node in tree.body:
            value = None
            targets = []
            if isinstance(node, ast.Assign):
                value = node.value
                targets = node.targets
            elif isinstance(node, ast.AnnAssign):
                value = node.value
                targets = [node.target]
            if value is None:
                continue
            if any(
                isinstance(target, ast.Name) and target.id == "REMOTE_SETTINGS"
                for target in targets
            ):
                remote = ast.literal_eval(value)
                if isinstance(remote, dict) and "url" in remote:
                    return remote
                return None
    except (ValueError, TypeError):
        return None
    return None


def get_remote_settings(
    explicit_settings_path: str | None = None,
    fallback_settings_path: str | None = None,
) -> dict[str, Any] | None:
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

    for path in filter(
        None,
        [
            explicit_settings_path,
            os.environ.get("IOP_SETTINGS"),
            fallback_settings_path,
        ],
    ):
        result = _load_remote_settings_from_file(path)
        if result:
            return result

    return None
