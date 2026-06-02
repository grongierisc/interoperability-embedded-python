from __future__ import annotations

from typing import Any

from .import_ import _normalize_queue_info
from .runtime import _ProductionRuntime


def inspect_component(production, component, *, refresh: bool = True) -> dict[str, Any]:
    """Return design-time and runtime details for a production component."""
    component_name = production._runtime_component_name(component)
    ref = production.item(component_name)
    graph = production.graph()
    outgoing = [
        edge.to_dict()
        for edge in graph.edges
        if edge.source_item == component_name
    ]
    incoming = [
        edge.to_dict()
        for edge in graph.edges
        if edge.target == component_name
    ]
    info: dict[str, Any] = {
        "production": production.name,
        "name": ref.name,
        "class_name": ref.class_name or "",
        "adapter_class_name": ref.adapter_class_name,
        "kind": ref.kind,
        "category": ref.category,
        "enabled": ref.enabled,
        "pool_size": ref.pool_size,
        "foreground": ref.foreground,
        "comment": ref.comment,
        "log_trace_events": ref.log_trace_events,
        "schedule": ref.schedule,
        "settings": {
            "Host": dict(ref.host_settings),
            "Adapter": dict(ref.adapter_settings),
            "Other": [dict(setting) for setting in ref.other_settings],
        },
        "ports": sorted(ref.port_names),
        "outgoing": outgoing,
        "incoming": incoming,
    }

    if refresh:
        runtime_info = component_runtime_info(production, component_name)
        if runtime_info:
            info["runtime"] = runtime_info
    elif component_name in production._queue_info:
        info["runtime"] = {"queue": dict(production._queue_info[component_name])}
    return info


def component_runtime_info(production, component_name: str) -> dict[str, Any]:
    director = _ProductionRuntime(production).director
    runtime: dict[str, Any] = {}
    warnings: list[str] = []

    try:
        status = director.status_production()
    except Exception as exc:
        warnings.append(f"Could not fetch production status: {exc}")
    else:
        if isinstance(status, dict):
            production_name = status.get("Production") or status.get("production") or ""
            state = status.get("Status") or status.get("status") or ""
            runtime["production_status"] = dict(status)
            runtime["current_production"] = str(production_name)
            runtime["status"] = str(state)
            runtime["is_current_production"] = production_name == production.name
            runtime["is_running"] = (
                production_name == production.name and str(state).lower() == "running"
            )
        else:
            warnings.append(f"Production status response is invalid: {status!r}")

    try:
        queue_info = director.export_production_queue_info(production.name)
    except Exception as exc:
        warnings.append(f"Could not fetch queue info: {exc}")
    else:
        queue_map, queue_warnings = _normalize_queue_info(queue_info)
        warnings.extend(queue_warnings)
        production._queue_info = queue_map
        if component_name in queue_map:
            runtime["queue"] = dict(queue_map[component_name])

    if warnings:
        runtime["warnings"] = warnings
    return runtime
