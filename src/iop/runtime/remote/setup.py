from __future__ import annotations

import importlib.resources
import os

import requests


def setup_remote_classes(client, path: str | None = None) -> None:
    """Upload and compile IOP .cls files to remote IRIS via the Atelier REST API."""
    paths_to_upload: list[str] = []
    if path is None:
        try:
            paths_to_upload.append(str(importlib.resources.files("iop").joinpath("cls")))
        except ModuleNotFoundError:
            pass
    else:
        paths_to_upload.append(path)

    atelier_base = f"{client._url}/api/atelier/v1"
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
                    f"{atelier_base}/{client._namespace}/doc/{doc_name}",
                    json={"enc": False, "content": content},
                    params={"ignoreConflict": "1"},
                    auth=client._auth,
                    verify=client._verify,
                    timeout=30,
                )
                client._raise_for_status(resp)
                doc_names.append(doc_name)
                print(f"Uploaded: {doc_name}")

    if not doc_names:
        raise RuntimeError("No .cls files found to upload.")

    resp = requests.post(
        f"{atelier_base}/{client._namespace}/action/compile",
        json=doc_names,
        params={"flags": "cuk"},
        auth=client._auth,
        verify=client._verify,
        timeout=120,
    )
    client._raise_for_status(resp)
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
