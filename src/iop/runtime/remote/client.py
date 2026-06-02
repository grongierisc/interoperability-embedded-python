from __future__ import annotations

from typing import Any

import requests
import urllib3


class _RemoteClient:
    """Small HTTP client for the IOP REST API."""

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

    @staticmethod
    def _raise_for_status(resp: requests.Response) -> None:
        """Like resp.raise_for_status() but includes the response body error message."""
        if resp.ok:
            return
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

    def _delete(self, path: str, params: dict | None = None) -> Any:
        p = {"namespace": self._namespace, **(params or {})}
        resp = requests.delete(
            f"{self._base}{path}",
            params=p,
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
