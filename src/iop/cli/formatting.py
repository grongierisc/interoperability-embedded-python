from __future__ import annotations

import dataclasses
import json
from typing import Any


def format_test_response(response: Any) -> str:
    """Pretty-print any test_component() return value."""
    if isinstance(response, dict):
        parts = []
        if response.get("error"):
            return f"Error: {response['error']}"
        if response.get("classname"):
            parts.append(f"classname: {response['classname']}")
        body = response.get("body", "")
        if body:
            try:
                parsed = json.loads(body)
                parts.append("body:\n" + json.dumps(parsed, indent=4))
            except (json.JSONDecodeError, TypeError):
                parts.append(f"body: {body}")
        if response.get("truncated"):
            parts.append("(response body was truncated)")
        return "\n".join(parts) if parts else str(response)

    if isinstance(response, str):
        if " : " in response:
            classname_part, _, body_part = response.partition(" : ")
            try:
                parsed = json.loads(body_part)
                return (
                    f"classname: {classname_part.strip()}\n"
                    f"body:\n{json.dumps(parsed, indent=4)}"
                )
            except (json.JSONDecodeError, TypeError):
                pass
        try:
            return json.dumps(json.loads(response), indent=4)
        except (json.JSONDecodeError, TypeError):
            return response

    if dataclasses.is_dataclass(response):
        return json.dumps(dataclasses.asdict(response), indent=4)
    return str(response)
