from __future__ import annotations

from typing import Any

from .component import ComponentRef
from .import_ import (
    _as_list,
    _is_internal_runtime_target,
    _matching_host_setting,
    _normalize_connections,
    _normalize_queue_info,
    _normalize_runtime_item_metadata,
    _production_payload,
    _setting_targets,
    _split_production_settings,
    _split_settings,
)
from .source_inference import infer_source_connections
from .types import GraphEdge


def production_from_dict(
    production_cls,
    data: dict[str, Any],
    *,
    connections: Any = None,
    queue_info: Any = None,
    namespace: str | None = None,
    director: Any = None,
):
    production_name, production_data = _production_payload(data)
    production_settings = _split_production_settings(production_data.get("Setting"))
    production = production_cls._new_unhydrated(
        production_name,
        testing_enabled=production_data.get("@TestingEnabled", False),
        log_general_trace_events=production_data.get("@LogGeneralTraceEvents", False),
        actor_pool_size=production_data.get("ActorPoolSize", 2),
        description=production_data.get("Description", ""),
        shutdown_timeout=production_settings.get("shutdown_timeout", 120),
        update_timeout=production_settings.get("update_timeout", 10),
        alert_notification_manager=production_settings.get(
            "alert_notification_manager", ""
        ),
        alert_notification_operation=production_settings.get(
            "alert_notification_operation", ""
        ),
        alert_notification_recipients=production_settings.get(
            "alert_notification_recipients", ""
        ),
        alert_action_window=production_settings.get("alert_action_window", 60),
        namespace=namespace,
        director=director,
    )

    _add_imported_items(production, production_data)
    _apply_queue_info(production, queue_info)
    _apply_runtime_item_metadata(production, connections)
    runtime_sources, runtime_sources_with_targets = _apply_runtime_connections(
        production, connections
    )
    _infer_connections_from_host_settings(
        production,
        runtime_sources=runtime_sources,
        runtime_sources_with_targets=runtime_sources_with_targets,
    )
    _infer_connections_from_source(production)
    return production


def _add_imported_items(production, production_data: dict[str, Any]) -> None:
    for item_data in _as_list(production_data.get("Item", [])):
        if not isinstance(item_data, dict):
            continue
        host_settings, adapter_settings, other_settings = _split_settings(
            item_data.get("Setting", [])
        )
        ref = ComponentRef(
            production=production,
            name=item_data.get("@Name", ""),
            class_name=item_data.get("@ClassName", ""),
            adapter_class_name=(
                item_data.get("@AdapterClassName") or item_data.get("@Adapter") or ""
            ),
            kind=_component_kind(item_data),
            category=item_data.get("@Category", ""),
            pool_size=item_data.get("@PoolSize", 1),
            enabled=item_data.get("@Enabled", True),
            foreground=item_data.get("@Foreground", False),
            comment=item_data.get("@Comment", ""),
            log_trace_events=item_data.get("@LogTraceEvents", False),
            schedule=item_data.get("@Schedule", ""),
            host_settings=host_settings,
            adapter_settings=adapter_settings,
            other_settings=other_settings,
        )
        production._add_item(ref)


def _apply_queue_info(production, queue_info: Any) -> None:
    queue_map, queue_warnings = _normalize_queue_info(queue_info)
    production._graph_warnings.extend(queue_warnings)
    for item_name, info in queue_map.items():
        if item_name not in production._items_by_name:
            production._graph_warnings.append(f"Queue info item does not exist: {item_name}")
            continue
        production._queue_info[item_name] = dict(info)


def _apply_runtime_item_metadata(production, connections: Any) -> None:
    runtime_item_metadata = _normalize_runtime_item_metadata(connections)
    for item_name, metadata in runtime_item_metadata.items():
        ref = production._items_by_name.get(item_name)
        if ref is None:
            continue
        adapter_class_name = metadata.get("adapter_class_name", "")
        if adapter_class_name and not ref.adapter_class_name:
            ref.adapter_class_name = adapter_class_name
        kind = _normalize_component_kind(metadata.get("kind", ""))
        if kind:
            ref.kind = kind
        if "iop" in metadata:
            ref.runtime_metadata["iop"] = metadata["iop"]
        for setting_name in ("%module", "%classname", "%classpaths"):
            setting_value = metadata.get(setting_name, "")
            if setting_value and setting_name not in ref.host_settings:
                ref.host_settings[setting_name] = setting_value


def _apply_runtime_connections(production, connections: Any) -> tuple[set[str], set[str]]:
    connection_map, runtime_sources, warnings = _normalize_connections(connections)
    production._graph_warnings.extend(warnings)
    runtime_sources_with_targets: set[str] = set()

    for source_item, targets in connection_map.items():
        if source_item not in production._items_by_name:
            production._graph_warnings.append(
                f"Runtime connection source does not exist: {source_item}"
            )
            continue
        ref = production._items_by_name[source_item]
        for target in targets:
            target_name = target.get("target", "")
            if not target_name:
                continue
            source_target_setting = target.get(
                "source_target_setting",
                "",
            ) or _matching_host_setting(ref, target_name)
            if source_target_setting:
                ref.target_setting_names.add(source_target_setting)
            if target_name not in production._items_by_name:
                if _is_internal_runtime_target(target_name):
                    continue
                production._graph_warnings.append(
                    f"Runtime connection target does not exist: "
                    f"{source_item} -> {target_name}"
                )
            runtime_sources_with_targets.add(source_item)
            production._register_connection(
                source_item,
                source_target_setting,
                target_name,
                origin="runtime",
                interaction=target.get("interaction", "request"),
                metadata=target.get("metadata", {}),
                validate_target=False,
            )
    return runtime_sources, runtime_sources_with_targets


def _component_kind(item_data: dict[str, Any]) -> str:
    explicit_kind = _normalize_component_kind(
        item_data.get("@Kind")
        or item_data.get("@kind")
        or item_data.get("kind")
        or item_data.get("type")
        or item_data.get("role")
        or ""
    )
    if explicit_kind:
        return explicit_kind
    return _component_kind_from_class_name(str(item_data.get("@ClassName", "")))


def _component_kind_from_class_name(class_name: str) -> str:
    class_name = str(class_name or "")
    if not class_name.startswith(("Python.", "Ens.", "EnsLib.", "IOP.")):
        return "component"
    last_part = class_name.rpartition(".")[2].lower()
    if not last_part:
        return "component"
    if last_part.endswith("service"):
        return "service"
    if last_part.endswith("process"):
        return "process"
    if last_part.endswith("operation"):
        return "operation"
    return "component"


def _normalize_component_kind(kind: Any) -> str:
    normalized = str(kind or "").strip().lower()
    if normalized in {"service", "businessservice"}:
        return "service"
    if normalized in {"process", "businessprocess"}:
        return "process"
    if normalized in {"operation", "businessoperation"}:
        return "operation"
    if normalized in {"component", "host", "businesshost"}:
        return "component"
    return ""


def _infer_connections_from_host_settings(
    production,
    *,
    runtime_sources: set[str],
    runtime_sources_with_targets: set[str],
) -> None:
    for ref in production._items:
        if ref.name in runtime_sources_with_targets:
            continue
        for setting_name, value in ref.host_settings.items():
            if str(setting_name).startswith("%"):
                continue
            for target_name in _setting_targets(value):
                if target_name not in production._items_by_name:
                    continue
                ref.target_setting_names.add(setting_name)
                metadata = {"source": "Host setting fallback"}
                if ref.name in runtime_sources:
                    metadata["reason"] = "runtime discovery returned no targets"
                production._register_connection(
                    ref.name,
                    setting_name,
                    target_name,
                    origin="inferred",
                    metadata=metadata,
                    validate_target=False,
                )


def _infer_connections_from_source(production) -> None:
    existing = {
        (edge.source_item, edge.target): edge
        for edge in production._edges
    }
    for ref in production._items:
        for connection in infer_source_connections(
            ref.class_name,
            ref.host_settings,
            iop=_truthy(ref.runtime_metadata.get("iop")),
        ):
            target_name = connection.target
            if target_name not in production._items_by_name:
                continue
            key = (ref.name, target_name)
            if key in existing:
                existing[key] = _apply_source_connection_interaction(
                    production,
                    existing[key],
                    connection,
                )
                continue
            metadata = {"source": connection.source}
            if connection.detail:
                metadata["detail"] = connection.detail
            production._register_connection(
                ref.name,
                "",
                target_name,
                origin="inferred",
                interaction=connection.interaction,
                metadata=metadata,
                validate_target=False,
            )
            existing[key] = production._edges[-1]


def _apply_source_connection_interaction(
    production,
    edge: GraphEdge,
    connection,
) -> GraphEdge:
    if connection.interaction in ("", "request"):
        return edge
    if edge.interaction not in ("", "request", "unknown"):
        return edge

    metadata = dict(edge.metadata)
    metadata.setdefault("source", connection.source)
    if connection.detail:
        metadata.setdefault("detail", connection.detail)

    updated = GraphEdge(
        source_item=edge.source_item,
        source_target_setting=edge.source_target_setting,
        target=edge.target,
        origin=edge.origin,
        interaction=connection.interaction,
        metadata=metadata,
    )
    production._edges = [
        updated if existing is edge else existing
        for existing in production._edges
    ]
    return updated


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}
