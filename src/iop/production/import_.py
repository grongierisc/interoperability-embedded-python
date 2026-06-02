from __future__ import annotations

from typing import Any, Optional

from .common import _text_value


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _production_payload(data: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    if not isinstance(data, dict) or not data:
        raise ValueError("Production data must be a non-empty dictionary.")

    if "Production" in data:
        production_data = data["Production"]
        if not isinstance(production_data, dict):
            raise ValueError("Production data must be a dictionary.")
        production_name = production_data.get("@Name") or "Production"
        return production_name, production_data

    production_name = next(iter(data.keys()))
    production_data = data[production_name]
    if not isinstance(production_data, dict):
        raise ValueError("Production data must be a dictionary.")
    production_name = production_data.get("@Name") or production_name
    return production_name, production_data


def _split_settings(
    settings: Any,
) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    host_settings: dict[str, Any] = {}
    adapter_settings: dict[str, Any] = {}
    other_settings: list[dict[str, Any]] = []

    for setting in _as_list(settings):
        if not isinstance(setting, dict):
            continue
        target = setting.get("@Target", "Host")
        name = setting.get("@Name", "")
        value = setting.get("#text", "")
        if target in ("", "Host"):
            host_settings[name] = value
        elif target == "Adapter":
            adapter_settings[name] = value
        else:
            other_settings.append(dict(setting))
    return host_settings, adapter_settings, other_settings


def _normalize_connections(
    connections: Any,
) -> tuple[dict[str, list[dict[str, Any]]], set[str], list[str]]:
    connection_map: dict[str, list[dict[str, Any]]] = {}
    runtime_sources: set[str] = set()
    warnings: list[str] = []

    if connections is None:
        return connection_map, runtime_sources, warnings

    if isinstance(connections, dict):
        warnings.extend(str(value) for value in _as_list(connections.get("warnings")))
        if "items" in connections:
            for item in _as_list(connections.get("items")):
                if not isinstance(item, dict):
                    continue
                source = (
                    item.get("item")
                    or item.get("name")
                    or item.get("source_item")
                    or ""
                )
                if not source:
                    continue
                item_warnings = [value for value in _as_list(item.get("warnings")) if value]
                warnings.extend(
                    f"{source}: {value}"
                    for value in item_warnings
                )
                discovered = False
                for target in _as_list(item.get("connections")):
                    normalized = _normalize_connection_target(target)
                    if normalized is not None:
                        discovered = True
                        connection_map.setdefault(source, []).append(normalized)
                for edge in _as_list(item.get("edges")):
                    normalized = _normalize_connection_target(edge)
                    if normalized is not None:
                        discovered = True
                        connection_map.setdefault(source, []).append(normalized)
                if not item_warnings or discovered:
                    runtime_sources.add(source)
            return connection_map, runtime_sources, warnings

        for source, targets in connections.items():
            if source in ("production", "warnings"):
                continue
            runtime_sources.add(str(source))
            for target in _as_list(targets):
                normalized = _normalize_connection_target(target)
                if normalized is not None:
                    connection_map.setdefault(str(source), []).append(normalized)
        return connection_map, runtime_sources, warnings

    if isinstance(connections, list):
        for edge in connections:
            if not isinstance(edge, dict):
                continue
            source = edge.get("source_item") or edge.get("item") or ""
            if not source and "." in str(edge.get("source", "")):
                source, _, source_port = str(edge["source"]).rpartition(".")
                edge = {**edge, "source_port": source_port}
            if not source:
                continue
            runtime_sources.add(str(source))
            normalized = _normalize_connection_target(edge)
            if normalized is not None:
                connection_map.setdefault(str(source), []).append(normalized)
        return connection_map, runtime_sources, warnings

    warnings.append(f"Ignoring invalid runtime connections: {connections!r}")
    return connection_map, runtime_sources, warnings


def _normalize_runtime_item_metadata(connections: Any) -> dict[str, dict[str, str]]:
    metadata: dict[str, dict[str, str]] = {}
    if not isinstance(connections, dict):
        return metadata
    for item in _as_list(connections.get("items")):
        if not isinstance(item, dict):
            continue
        item_name = (
            item.get("item")
            or item.get("name")
            or item.get("source_item")
            or ""
        )
        if not item_name:
            continue
        adapter_class_name = (
            item.get("adapter_class_name")
            or item.get("adapter")
            or item.get("AdapterClassName")
            or item.get("Adapter")
            or ""
        )
        if adapter_class_name:
            metadata[str(item_name)] = {
                "adapter_class_name": str(adapter_class_name)
            }
    return metadata


def _normalize_connection_target(value: Any) -> Optional[dict[str, Any]]:
    if isinstance(value, str):
        if not value:
            return None
        return {"target": value, "source_port": ""}
    if not isinstance(value, dict):
        return None
    target = value.get("target") or value.get("name") or value.get("to") or ""
    if not target:
        return None
    source_port = value.get("source_port") or value.get("port") or ""
    metadata = dict(value.get("metadata") or {})
    known_keys = {
        "target",
        "name",
        "to",
        "source_port",
        "port",
        "interaction",
        "metadata",
    }
    for key, item in value.items():
        if key not in known_keys and item is not None:
            metadata.setdefault(str(key), item)
    normalized: dict[str, Any] = {
        "target": str(target),
        "source_port": str(source_port),
    }
    if value.get("interaction"):
        normalized["interaction"] = str(value["interaction"])
    if metadata:
        normalized["metadata"] = metadata
    return normalized


def _normalize_queue_info(value: Any) -> tuple[dict[str, dict[str, Any]], list[str]]:
    queue_map: dict[str, dict[str, Any]] = {}
    warnings: list[str] = []
    if value is None:
        return queue_map, warnings

    if isinstance(value, dict):
        warnings.extend(str(item) for item in _as_list(value.get("warnings")) if item)
        if "items" in value:
            for item in _as_list(value.get("items")):
                normalized = _normalize_queue_item(item)
                if normalized is None:
                    continue
                item_name, info = normalized
                queue_map[item_name] = info
            return queue_map, warnings

        for item_name, info in value.items():
            if item_name in ("production", "warnings"):
                continue
            if isinstance(info, dict):
                queue_map[str(item_name)] = dict(info)
        return queue_map, warnings

    if isinstance(value, list):
        for item in value:
            normalized = _normalize_queue_item(item)
            if normalized is None:
                continue
            item_name, info = normalized
            queue_map[item_name] = info
        return queue_map, warnings

    warnings.append(f"Ignoring invalid queue info: {value!r}")
    return queue_map, warnings


def _normalize_queue_item(value: Any) -> Optional[tuple[str, dict[str, Any]]]:
    if not isinstance(value, dict):
        return None
    item_name = value.get("item") or value.get("name") or value.get("queue_name") or ""
    if not item_name:
        return None
    info = dict(value)
    info.pop("item", None)
    info.setdefault("queue_name", info.pop("name", item_name))
    return str(item_name), info


def _setting_targets(value: Any) -> list[str]:
    text = _text_value(value).strip()
    if not text:
        return []
    return [part.strip() for part in text.split(",") if part.strip()]


def _matching_host_setting(component: Any, target_name: str) -> str:
    for name, value in component.host_settings.items():
        if target_name in _setting_targets(value):
            return name
    return ""


def _is_internal_runtime_target(target_name: str) -> bool:
    return target_name in {"Ens.Alert", "Ens.ScheduleHandler"}
