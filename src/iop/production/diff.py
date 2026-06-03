from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from .common import PRODUCTION_SETTING_FIELDS, _bool_text, _text_value
from .types import (
    GraphEdge,
    ProductionDiff,
    ProductionDiffEntry,
    _canonical_value,
)

if TYPE_CHECKING:
    from .component import ComponentRef
    from .model import Production


def _diff_productions(
    desired: Production,
    current: Production,
    *,
    include_graph_metadata: bool = False,
) -> ProductionDiff:
    changes: list[ProductionDiffEntry] = []
    warnings = _diff_warnings(desired, current)

    if current.name != desired.name:
        changes.append(
            ProductionDiffEntry(
                action="change",
                kind="production",
                path="production.name",
                before=current.name,
                after=desired.name,
            )
        )

    _diff_mapping_values(
        changes,
        kind="production",
        base_path="production",
        before=_production_signature(current),
        after=_production_signature(desired),
    )
    _diff_items(changes, desired=desired, current=current)
    _diff_connections(
        changes,
        desired=desired,
        current=current,
        include_graph_metadata=include_graph_metadata,
    )

    return ProductionDiff(
        production_name=desired.name,
        changes=tuple(changes),
        warnings=tuple(warnings),
    )


def _diff_warnings(desired: Production, current: Production) -> list[str]:
    warnings = []
    warnings.extend(f"desired: {warning}" for warning in desired.graph().warnings)
    warnings.extend(f"current: {warning}" for warning in current.graph().warnings)
    return warnings


def _production_signature(production: Production) -> dict[str, Any]:
    signature = {
        "testing_enabled": _bool_text(production.testing_enabled),
        "log_general_trace_events": _bool_text(production.log_general_trace_events),
        "actor_pool_size": _text_value(production.actor_pool_size),
        "description": production.description,
    }
    signature.update(
        {
            field_name: _text_value(getattr(production, field_name))
            for field_name in PRODUCTION_SETTING_FIELDS
        }
    )
    return signature


def _item_signatures(production: Production) -> dict[str, dict[str, Any]]:
    return {item.name: _item_signature(item) for item in production.items}


def _item_signature(item: ComponentRef) -> dict[str, Any]:
    return {
        "class_name": item.class_name or "",
        "category": item.category,
        "pool_size": _text_value(item.pool_size),
        "enabled": _bool_text(item.enabled),
        "foreground": _bool_text(item.foreground),
        "comment": item.comment,
        "log_trace_events": _bool_text(item.log_trace_events),
        "schedule": item.schedule,
        "host_settings": _settings_signature(item.host_settings),
        "adapter_settings": _settings_signature(item.adapter_settings),
        "other_settings": _canonical_value(item.other_settings),
    }


def _settings_signature(settings: dict[str, Any]) -> dict[str, str]:
    return {key: _text_value(settings[key]) for key in sorted(settings)}


def _diff_items(
    changes: list[ProductionDiffEntry],
    *,
    desired: Production,
    current: Production,
) -> None:
    desired_items = _item_signatures(desired)
    current_items = _item_signatures(current)

    for item_name in sorted(current_items.keys() - desired_items.keys()):
        changes.append(
            ProductionDiffEntry(
                action="remove",
                kind="item",
                path=f"items.{item_name}",
                before=current_items[item_name],
            )
        )

    for item_name in sorted(desired_items.keys() - current_items.keys()):
        changes.append(
            ProductionDiffEntry(
                action="add",
                kind="item",
                path=f"items.{item_name}",
                after=desired_items[item_name],
            )
        )

    for item_name in sorted(desired_items.keys() & current_items.keys()):
        _diff_item_fields(
            changes,
            item_name=item_name,
            before=current_items[item_name],
            after=desired_items[item_name],
        )


def _diff_item_fields(
    changes: list[ProductionDiffEntry],
    *,
    item_name: str,
    before: dict[str, Any],
    after: dict[str, Any],
) -> None:
    scalar_fields = [
        "class_name",
        "category",
        "pool_size",
        "enabled",
        "foreground",
        "comment",
        "log_trace_events",
        "schedule",
    ]
    _diff_mapping_values(
        changes,
        kind="item",
        base_path=f"items.{item_name}",
        before={field: before[field] for field in scalar_fields},
        after={field: after[field] for field in scalar_fields},
    )
    _diff_mapping_values(
        changes,
        kind="setting",
        base_path=f"items.{item_name}.settings.Host",
        before=before["host_settings"],
        after=after["host_settings"],
    )
    _diff_mapping_values(
        changes,
        kind="setting",
        base_path=f"items.{item_name}.settings.Adapter",
        before=before["adapter_settings"],
        after=after["adapter_settings"],
    )
    if before["other_settings"] != after["other_settings"]:
        changes.append(
            ProductionDiffEntry(
                action="change",
                kind="setting",
                path=f"items.{item_name}.settings.Other",
                before=before["other_settings"],
                after=after["other_settings"],
            )
        )


def _diff_mapping_values(
    changes: list[ProductionDiffEntry],
    *,
    kind: str,
    base_path: str,
    before: dict[str, Any],
    after: dict[str, Any],
) -> None:
    for key in sorted(before.keys() - after.keys()):
        changes.append(
            ProductionDiffEntry(
                action="remove",
                kind=kind,
                path=f"{base_path}.{key}",
                before=before[key],
            )
        )
    for key in sorted(after.keys() - before.keys()):
        changes.append(
            ProductionDiffEntry(
                action="add",
                kind=kind,
                path=f"{base_path}.{key}",
                after=after[key],
            )
        )
    for key in sorted(before.keys() & after.keys()):
        if before[key] != after[key]:
            changes.append(
                ProductionDiffEntry(
                    action="change",
                    kind=kind,
                    path=f"{base_path}.{key}",
                    before=before[key],
                    after=after[key],
                )
            )


def _diff_connections(
    changes: list[ProductionDiffEntry],
    *,
    desired: Production,
    current: Production,
    include_graph_metadata: bool = False,
) -> None:
    desired_connections = _connection_signature(
        desired,
        include_graph_metadata=include_graph_metadata,
    )
    current_connections = _connection_signature(
        current,
        include_graph_metadata=include_graph_metadata,
    )

    for source in sorted(current_connections.keys() - desired_connections.keys()):
        changes.append(
            ProductionDiffEntry(
                action="remove",
                kind="connection",
                path=f"connections.{_connection_source_path(source)}",
                before=current_connections[source],
            )
        )
    for source in sorted(desired_connections.keys() - current_connections.keys()):
        changes.append(
            ProductionDiffEntry(
                action="add",
                kind="connection",
                path=f"connections.{_connection_source_path(source)}",
                after=desired_connections[source],
            )
        )
    for source in sorted(desired_connections.keys() & current_connections.keys()):
        before = current_connections[source]
        after = desired_connections[source]
        if before != after:
            changes.append(
                ProductionDiffEntry(
                    action="change",
                    kind="connection",
                    path=f"connections.{_connection_source_path(source)}",
                    before=before,
                    after=after,
                )
            )


def _connection_signature(
    production: Production,
    *,
    include_graph_metadata: bool = False,
) -> dict[tuple[str, str], list[Any]]:
    if include_graph_metadata:
        detailed_connections: dict[tuple[str, str], list[dict[str, Any]]] = {}
        for edge in production.graph().edges:
            source = (edge.source_item, edge.source_port)
            detailed_connections.setdefault(source, []).append(_edge_diff_value(edge))
        return {
            source: sorted(
                values,
                key=lambda value: json.dumps(value, sort_keys=True),
            )
            for source, values in sorted(detailed_connections.items())
        }

    connections: dict[tuple[str, str], set[str]] = {}
    for edge in production.graph().edges:
        source = (edge.source_item, edge.source_port)
        connections.setdefault(source, set()).add(edge.target)
    return {
        source: list(sorted(targets))
        for source, targets in sorted(connections.items())
    }


def _edge_diff_value(edge: GraphEdge) -> dict[str, Any]:
    data: dict[str, Any] = {
        "target": edge.target,
        "origin": edge.origin,
        "interaction": edge.interaction,
        "logical_name": edge.logical_name,
    }
    if edge.metadata:
        data["metadata"] = _canonical_value(edge.metadata)
    return data


def _connection_source_path(source: tuple[str, str]) -> str:
    source_item, source_port = source
    if source_port:
        return f"{source_item}.{source_port}"
    return source_item
