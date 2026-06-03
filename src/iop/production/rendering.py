from __future__ import annotations

import json
import keyword
import re
from dataclasses import is_dataclass
from pprint import pformat
from typing import Any

from pydantic import BaseModel

from .common import PRODUCTION_SETTING_FIELDS, _bool_text, _text_value
from .types import GraphNode, ProductionGraph


def production_to_dict(production) -> dict[str, Any]:
    data: dict[str, Any] = {
        "@Name": production.name,
        "@TestingEnabled": _bool_text(production.testing_enabled),
        "@LogGeneralTraceEvents": _bool_text(production.log_general_trace_events),
        "Description": production.description,
        "ActorPoolSize": _text_value(production.actor_pool_size),
    }
    production_settings = _production_settings_to_iris(production)
    if production_settings:
        data["Setting"] = production_settings
    if production._items:
        data["Item"] = [item.to_dict() for item in production._items]
    return {production.name: data}


def _production_settings_to_iris(production) -> list[dict[str, str]]:
    settings: list[dict[str, str]] = []
    for field_name, (iris_name, default) in PRODUCTION_SETTING_FIELDS.items():
        value = getattr(production, field_name)
        if _text_value(value) == _text_value(default):
            continue
        settings.append(
            {
                "@Name": iris_name,
                "#text": _text_value(value),
            }
        )
    return settings


def production_to_xml(production) -> str:
    from ..migration.io import dict_to_xml

    return dict_to_xml({"Production": production_to_dict(production)[production.name]})


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


def production_to_class(production) -> str:
    item_names = {item.name for item in production.items}
    route_targets = _valid_route_targets(
        _route_targets(production, item_names),
        item_names,
    )
    item_groups = _class_item_groups(production.items)
    used_items = {
        _class_item_type(kind)
        for kind, items in item_groups.items()
        if items
    }
    has_routes = bool(route_targets)
    imports = ["Production", *sorted(used_items)]
    if has_routes:
        imports.append("Route")

    class_name = _production_class_name(production.name)
    lines = [
        "# Generated from IRIS production export.",
        "# Review before using as source of truth; some runtime/dynamic routing intent",
        "# cannot be fully reconstructed from deployed IRIS metadata.",
    ]
    if _has_string_python_proxy_items(production.items):
        lines.extend(
            [
                "# TODO: replace Python.* string class names with imported Python",
                "# classes before re-migration, or ensure the proxy classes already exist.",
            ]
        )
    lines.extend(
        [
            f"from iop import {', '.join(imports)}",
            "",
            "",
            f"class {class_name}(Production):",
            f"    name = {_literal(production.name)}",
        ]
    )
    lines.extend(_class_production_setting_lines(production))
    lines.append("")

    for kind in ("component", "service", "process", "operation"):
        items = item_groups.get(kind, [])
        if not items:
            continue
        attr_name = _class_item_attr(kind)
        lines.append(f"    {attr_name} = (")
        for item in items:
            lines.extend(_class_item_lines(item, kind, route_targets))
        lines.append("    )")
        lines.append("")

    unresolved = _unresolved_class_routes(production, item_names)
    if unresolved:
        lines.append("    # TODO: review unresolved or runtime-only routes:")
        lines.extend(f"    # - {value}" for value in unresolved)
        lines.append("")
    if production.graph().warnings:
        lines.append("    # Import warnings:")
        lines.extend(f"    # - {warning}" for warning in production.graph().warnings)
        lines.append("")

    lines.append("")
    lines.append(f"PRODUCTIONS = [{class_name}()]")
    return "\n".join(lines) + "\n"


def _class_production_setting_lines(production) -> list[str]:
    return [
        f"    {name} = {_literal(value)}"
        for name, value, default in _production_setting_literals(production)
        if value != default
    ]


def _production_setting_literals(production) -> list[tuple[str, Any, Any]]:
    return [
        ("testing_enabled", _bool_literal(production.testing_enabled), False),
        (
            "log_general_trace_events",
            _bool_literal(production.log_general_trace_events),
            False,
        ),
        ("actor_pool_size", _int_literal(production.actor_pool_size), 2),
        ("description", production.description, ""),
        ("shutdown_timeout", _int_literal(production.shutdown_timeout), 120),
        ("update_timeout", _int_literal(production.update_timeout), 10),
        ("alert_notification_manager", production.alert_notification_manager, ""),
        ("alert_notification_operation", production.alert_notification_operation, ""),
        ("alert_notification_recipients", production.alert_notification_recipients, ""),
        ("alert_action_window", _int_literal(production.alert_action_window), 60),
    ]


def _class_item_groups(items) -> dict[str, list[Any]]:
    groups: dict[str, list[Any]] = {
        "component": [],
        "service": [],
        "process": [],
        "operation": [],
    }
    for item in items:
        groups[_class_item_kind(item)].append(item)
    return groups


def _class_item_kind(item) -> str:
    if item.kind in {"service", "process", "operation"}:
        return item.kind
    return "component"


def _class_item_type(kind: str) -> str:
    return {
        "component": "ComponentItem",
        "service": "ServiceItem",
        "process": "ProcessItem",
        "operation": "OperationItem",
    }[kind]


def _class_item_attr(kind: str) -> str:
    return {
        "component": "components",
        "service": "services",
        "process": "processes",
        "operation": "operations",
    }[kind]


def _class_item_lines(item, kind: str, route_targets) -> list[str]:
    kwargs: list[tuple[str, Any]] = []
    optional_fields = [
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
    if item.other_settings:
        kwargs.append(("other_settings", [dict(value) for value in item.other_settings]))

    routes = _class_item_route_values(item, route_targets)
    if routes:
        kwargs.append(("routes", routes))

    lines = []
    if _is_string_python_proxy_item(item):
        lines.extend(
            [
                "        # TODO: replace this proxy class name with the Python",
                "        # class object if this item should be auto-registered.",
            ]
        )
    lines.extend(
        [
            f"        {_class_item_type(kind)}(",
            f"            {_literal(item.name)},",
            f"            {_literal(item.class_name or '')},",
        ]
    )
    for name, value in kwargs:
        lines.extend(_class_keyword_lines(name, value))
    lines.append("        ),")
    return lines


def _class_item_route_values(item, route_targets) -> list[tuple[str, list[str]]]:
    values: list[tuple[str, list[str]]] = []
    for source_item, source_port in sorted(route_targets):
        if source_item != item.name:
            continue
        targets = route_targets[(source_item, source_port)]
        values.append((source_port, list(targets)))
    return values


def _valid_route_targets(
    route_targets: dict[tuple[str, str], list[str]],
    item_names: set[str],
) -> dict[tuple[str, str], list[str]]:
    valid_routes: dict[tuple[str, str], list[str]] = {}
    for source, targets in route_targets.items():
        valid_targets = [target for target in targets if target in item_names]
        if valid_targets:
            valid_routes[source] = valid_targets
    return valid_routes


def _class_keyword_lines(name: str, value: Any) -> list[str]:
    if isinstance(value, dict):
        return _indented_dict_keyword_lines(name, value, indent=12)
    if isinstance(value, list) and name == "routes":
        return _class_route_keyword_lines(value)
    if isinstance(value, list):
        return _indented_list_keyword_lines(name, value, indent=12)
    return [f"            {name}={_literal(value)},"]


def _class_route_keyword_lines(routes: list[tuple[str, list[str]]]) -> list[str]:
    if len(routes) == 1:
        port, targets = routes[0]
        target_literal = _class_route_targets_literal(targets)
        return [f"            routes=(Route({_literal(port)}, {target_literal}),),"]

    lines = ["            routes=("]
    for port, targets in routes:
        target_literal = _class_route_targets_literal(targets)
        lines.append(f"                Route({_literal(port)}, {target_literal}),")
    lines.append("            ),")
    return lines


def _class_route_targets_literal(targets: list[str]) -> str:
    return _literal(targets[0]) if len(targets) == 1 else _literal(tuple(targets))


def _has_string_python_proxy_items(items) -> bool:
    return any(_is_string_python_proxy_item(item) for item in items)


def _is_string_python_proxy_item(item) -> bool:
    return str(item.class_name or "").startswith("Python.")


def _indented_dict_keyword_lines(
    name: str,
    value: dict[str, Any],
    *,
    indent: int,
) -> list[str]:
    prefix = " " * indent
    item_prefix = " " * (indent + 4)
    lines = [f"{prefix}{name}={{"]
    for key, item in value.items():
        lines.append(f"{item_prefix}{_literal(key)}: {_literal(item)},")
    lines.append(f"{prefix}}},")
    return lines


def _indented_list_keyword_lines(
    name: str,
    value: list[Any],
    *,
    indent: int,
) -> list[str]:
    prefix = " " * indent
    item_prefix = " " * (indent + 4)
    lines = [f"{prefix}{name}=["]
    for item in value:
        lines.append(f"{item_prefix}{_literal(item)},")
    lines.append(f"{prefix}],")
    return lines


def _unresolved_class_routes(production, item_names: set[str]) -> list[str]:
    unresolved: list[str] = []
    for edge in production.edges:
        if not edge.source_port:
            unresolved.append(f"{edge.source_item} -> {edge.target}")
        elif edge.target not in item_names:
            unresolved.append(f"{edge.source_item}.{edge.source_port} -> {edge.target}")
    return sorted(set(unresolved))


def _production_class_name(production_name: str) -> str:
    parts = [
        part
        for part in re.split(r"\W+", production_name)
        if part
    ]
    if not parts:
        return "GeneratedProduction"
    candidate = parts[-1]
    if candidate == "Production" and len(parts) > 1:
        candidate = "".join(parts[-2:])
    else:
        candidate = "".join(
            part[:1].upper() + part[1:]
            for part in re.split(r"[_\s]+", candidate)
            if part
        )
    if not candidate or not candidate[0].isalpha():
        candidate = f"Generated{candidate}"
    if keyword.iskeyword(candidate) or candidate == "Production":
        candidate = f"{candidate}Definition"
    return candidate


def _production_constructor_lines(production) -> list[str]:
    rendered = [
        (name, value)
        for name, value, default in _production_setting_literals(production)
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
