from __future__ import annotations

import json
from dataclasses import is_dataclass
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
