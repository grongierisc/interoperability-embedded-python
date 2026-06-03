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
    production = production_cls(
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
            kind="component",
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


def _apply_runtime_connections(production, connections: Any) -> tuple[set[str], set[str]]:
    connection_map, runtime_sources, warnings = _normalize_connections(connections)
    production._graph_warnings.extend(warnings)
    runtime_sources_with_targets = {
        source_item for source_item, targets in connection_map.items() if targets
    }

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
            source_port = target.get("source_port", "") or _matching_host_setting(
                ref, target_name
            )
            if source_port:
                ref.port_names.add(source_port)
            if target_name not in production._items_by_name:
                if _is_internal_runtime_target(target_name):
                    continue
                production._graph_warnings.append(
                    f"Runtime connection target does not exist: "
                    f"{source_item} -> {target_name}"
                )
            production._register_connection(
                source_item,
                source_port,
                target_name,
                origin="runtime",
                interaction=target.get("interaction", "request"),
                metadata=target.get("metadata", {}),
                validate_target=False,
            )
    return runtime_sources, runtime_sources_with_targets


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
            for target_name in _setting_targets(value):
                if target_name not in production._items_by_name:
                    continue
                ref.port_names.add(setting_name)
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
