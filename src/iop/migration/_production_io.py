from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from ..runtime import iris as _iris
from .io import dict_to_xml, stream_to_string, string_to_stream, xml_to_json


def _raise_on_error(status: Any) -> None:
    iris = _iris.get_iris()
    if iris.system.Status.IsError(status):
        raise RuntimeError(iris.system.Status.GetOneStatusText(status))


def register_production(production_name: str, xml: str) -> None:
    package, _, short_name = production_name.rpartition(".")
    stream = string_to_stream(_iris.get_iris(), xml)
    _raise_on_error(
        _iris.get_iris().cls("IOP.Utils").CreateProduction(package, short_name, stream)
    )


def register_production_definition(
    production_name: str,
    production: dict,
    *,
    xml_fallback: Callable[[str, str], None] = register_production,
) -> None:
    try:
        _raise_on_error(
            _iris.get_iris()
            .cls("IOP.Utils")
            .CreateProductionFromJSON(production_name, json.dumps(production))
        )
    except RuntimeError as exc:
        if not is_missing_production_class_error(exc, production_name):
            raise
        xml_fallback(production_name, dict_to_xml(production))


def is_missing_production_class_error(
    exc: RuntimeError, production_name: str
) -> bool:
    message = str(exc)
    return "CLASS DOES NOT EXIST" in message and production_name in message


def export_production(production_name: str):
    data = _iris.get_iris().cls("IOP.Utils").ExportProduction(production_name)
    return xml_to_json(stream_to_string(data))


def export_production_connections(production_name: str) -> dict:
    data = _iris.get_iris().cls("IOP.Utils").ExportProductionConnections(
        production_name
    )
    return data if isinstance(data, dict) else json.loads(data)


def export_production_queue_info(production_name: str) -> dict:
    data = _iris.get_iris().cls("IOP.Utils").ExportProductionQueueInfo(production_name)
    return data if isinstance(data, dict) else json.loads(data)


def apply_production_plan(
    plan: dict, allow_destructive: bool = False
) -> dict:
    production_name = plan.get("production") or plan.get("production_name")
    if not production_name:
        raise ValueError("Production plan is missing the production name.")
    data = (
        _iris.get_iris()
        .cls("IOP.Utils")
        .ApplyProductionPlan(
            production_name,
            json.dumps(plan),
            1 if allow_destructive else 0,
        )
    )
    return data if isinstance(data, dict) else json.loads(data)
