from __future__ import annotations

import ast
import os
from typing import Any


def load_remote_settings_from_file(settings_path: str) -> dict[str, Any] | None:
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
    """Detect remote settings from env vars or settings files."""
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
        result = load_remote_settings_from_file(path)
        if result:
            return result

    return None
