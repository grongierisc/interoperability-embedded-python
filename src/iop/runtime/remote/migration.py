from __future__ import annotations

import importlib.util
import os

import requests


def upload_migration(client, path: str) -> None:
    """Upload .py and .cls files from *path*'s folder to remote IRIS."""
    folder = os.path.dirname(path)

    package = "python"
    remote_folder = ""
    try:
        spec = importlib.util.spec_from_file_location("_iop_migrate_settings", path)
        mod = importlib.util.module_from_spec(spec)  # type: ignore[arg-type]
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        remote_settings = getattr(mod, "REMOTE_SETTINGS", {})
        package = remote_settings.get("package", package)
        remote_folder = remote_settings.get("remote_folder", remote_folder)
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
        "namespace": client._namespace,
        "package": package,
        "remote_folder": remote_folder,
        "settings_file": settings_file,
        "body": body,
    }
    resp = requests.put(
        f"{client._base}/migrate",
        json=payload,
        params={"namespace": client._namespace},
        auth=client._auth,
        verify=client._verify,
        timeout=30,
    )
    client._raise_for_status(resp)
