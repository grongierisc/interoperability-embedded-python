from __future__ import annotations

import json
import keyword
import re
from dataclasses import is_dataclass
from pprint import pformat
from typing import Any

from pydantic import BaseModel

from .common import _bool_text, _text_value
from .types import GraphNode, ProductionGraph


def production_to_dict(production) -> dict[str, Any]:
    data: dict[str, Any] = {
        "@Name": production.name,
        "@TestingEnabled": _bool_text(production.testing_enabled),
        "@LogGeneralTraceEvents": _bool_text(production.log_general_trace_events),
        "Description": production.description,
        "ActorPoolSize": _text_value(production.actor_pool_size),
    }
    if production._items:
        data["Item"] = [item.to_dict() for item in production._items]
    return {production.name: data}


def production_to_xml(production) -> str:
    from ..migration import utils as migration_utils

    return migration_utils.dict_to_xml(
        {"Production": production_to_dict(production)[production.name]}
    )


def production_to_python(production) -> str:
    names = {item.name for item in production.items}
    variables = _component_variable_names(production.items)
    route_targets = _route_targets(production, names)

    lines = [
        "# Generated from IRIS production export.",
        "# Review before using as source of truth; some runtime/dynamic routing intent",
        "# cannot be fully reconstructed from deployed IRIS metadata.",
        "from iop import Production",
        "",
        "",
    ]
    lines.extend(_production_constructor_lines(production))
    lines.append("")

    for item in production.items:
        lines.extend(_component_lines(item, variables[item.name], route_targets))
        lines.append("")

    route_lines = _connection_lines(production, variables, names)
    if route_lines:
        lines.extend(route_lines)
        lines.append("")

    if production.graph().warnings:
        lines.append("# Import warnings:")
        lines.extend(f"# - {warning}" for warning in production.graph().warnings)
        lines.append("")

    lines.append("PRODUCTIONS = [prod]")
    return "\n".join(lines) + "\n"


def _production_constructor_lines(production) -> list[str]:
    kwargs = [
        ("testing_enabled", _bool_literal(production.testing_enabled), False),
        (
            "log_general_trace_events",
            _bool_literal(production.log_general_trace_events),
            False,
        ),
        ("actor_pool_size", _int_literal(production.actor_pool_size), 2),
        ("description", production.description, ""),
    ]
    rendered = [
        (name, value)
        for name, value, default in kwargs
        if value != default
    ]
    if not rendered:
        return [f"prod = Production({_literal(production.name)})"]

    lines = [f"prod = Production({_literal(production.name)},"]
    for name, value in rendered:
        lines.append(f"    {name}={_literal(value)},")
    lines.append(")")
    return lines


def _component_lines(item, variable_name: str, route_targets) -> list[str]:
    kwargs: list[tuple[str, Any]] = [
        ("class_name", item.class_name or ""),
    ]
    optional_fields = [
        ("kind", item.kind, "component"),
        ("category", item.category, ""),
        ("pool_size", _int_literal(item.pool_size), 1),
        ("enabled", _bool_literal(item.enabled), True),
        ("foreground", _bool_literal(item.foreground), False),
        ("comment", item.comment, ""),
        ("log_trace_events", _bool_literal(item.log_trace_events), False),
        ("schedule", item.schedule, ""),
    ]
    kwargs.extend(
        (name, value)
        for name, value, default in optional_fields
        if value != default
    )

    settings = {
        name: value
        for name, value in item.host_settings.items()
        if (item.name, name) not in route_targets
    }
    if settings:
        kwargs.append(("settings", settings))
    if item.adapter_settings:
        kwargs.append(("adapter_settings", dict(item.adapter_settings)))

    lines = [f"{variable_name} = prod.component("]
    lines.append(f"    {_literal(item.name)},")
    for name, value in kwargs:
        lines.extend(_keyword_lines(name, value))
    lines.append(")")

    for setting in item.other_settings:
        target = setting.get("@Target", "")
        name = setting.get("@Name", "")
        value = setting.get("#text", "")
        lines.append(
            f"{variable_name}.other_setting({_literal(target)}, "
            f"{_literal(name)}, {_literal(value)})"
        )
    return lines


def _connection_lines(production, variables: dict[str, str], item_names: set[str]) -> list[str]:
    grouped = _route_targets(production, item_names)
    lines: list[str] = []
    unresolved: list[str] = []

    for source_item, source_port in sorted(grouped):
        targets = grouped[(source_item, source_port)]
        source_var = variables[source_item]
        source_expr = f"{source_var}.port({_literal(source_port)})"
        valid_targets = [target for target in targets if target in variables]
        invalid_targets = [target for target in targets if target not in variables]
        for target in invalid_targets:
            unresolved.append(f"{source_item}.{source_port} -> {target}")
        if not valid_targets:
            continue
        if len(valid_targets) == 1:
            lines.append(
                f"prod.connect({source_expr}, {variables[valid_targets[0]]})"
            )
        else:
            for target in valid_targets:
                lines.append(
                    f"prod.connect_add({source_expr}, {variables[target]})"
                )

    for edge in production.edges:
        if not edge.source_port:
            unresolved.append(f"{edge.source_item} -> {edge.target}")

    if unresolved:
        lines.append("# TODO: review unresolved or runtime-only routes:")
        lines.extend(f"# - {value}" for value in sorted(set(unresolved)))
    return lines


def _route_targets(production, item_names: set[str]) -> dict[tuple[str, str], list[str]]:
    grouped: dict[tuple[str, str], list[str]] = {}
    for edge in production.edges:
        if not edge.source_port:
            continue
        if edge.source_item not in item_names:
            continue
        key = (edge.source_item, edge.source_port)
        grouped.setdefault(key, [])
        if edge.target not in grouped[key]:
            grouped[key].append(edge.target)
    return grouped


def _component_variable_names(items) -> dict[str, str]:
    names: dict[str, str] = {}
    used: set[str] = set()
    for item in items:
        base = _safe_identifier(item.name)
        candidate = base
        index = 2
        while candidate in used:
            candidate = f"{base}_{index}"
            index += 1
        used.add(candidate)
        names[item.name] = candidate
    return names


def _safe_identifier(value: str) -> str:
    candidate = re.sub(r"\W+", "_", value).strip("_").lower()
    if not candidate:
        candidate = "component"
    if candidate[0].isdigit():
        candidate = f"component_{candidate}"
    if keyword.iskeyword(candidate):
        candidate = f"{candidate}_component"
    return candidate


def _keyword_lines(name: str, value: Any) -> list[str]:
    if isinstance(value, dict):
        return _dict_keyword_lines(name, value)
    return [f"    {name}={_literal(value)},"]


def _dict_keyword_lines(name: str, value: dict[str, Any]) -> list[str]:
    if not value:
        return []
    lines = [f"    {name}={{"]
    for key, item in value.items():
        lines.append(f"        {_literal(key)}: {_literal(item)},")
    lines.append("    },")
    return lines


def _literal(value: Any) -> str:
    if isinstance(value, dict):
        return pformat(value, sort_dicts=False)
    return repr(value)


def _bool_literal(value: Any) -> bool | str:
    if isinstance(value, bool):
        return value
    normalized = str(value).strip().lower()
    if normalized in {"true", "1", "yes", "on"}:
        return True
    if normalized in {"false", "0", "no", "off"}:
        return False
    return str(value)


def _int_literal(value: Any) -> int | str:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    text = str(value).strip()
    if text.isdigit():
        return int(text)
    return text


def production_graph(production) -> ProductionGraph:
    nodes = tuple(
        GraphNode(
            name=item.name,
            class_name=item.class_name or "",
            kind=item.kind,
            enabled=item.enabled,
            category=item.category,
            adapter_class_name=item.adapter_class_name,
        )
        for item in production._items
    )
    return ProductionGraph(
        production_name=production.name,
        nodes=nodes,
        edges=tuple(production._edges),
        warnings=tuple(production._graph_warnings),
    )


def message_to_classname_body(message: Any) -> tuple[str | None, str | dict | None]:
    classname = f"{message.__class__.__module__}.{message.__class__.__name__}"
    if isinstance(message, BaseModel):
        return classname, message.model_dump_json()
    if is_dataclass(message):
        from ..messages.serialization import dataclass_to_dict

        return classname, json.dumps(dataclass_to_dict(message))
    return None, None
