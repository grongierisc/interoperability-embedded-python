from __future__ import annotations

import json
import os
from typing import Any

import xmltodict


def dict_to_xml(data: dict[str, Any]) -> str:
    xml = xmltodict.unparse(data, pretty=True)
    xml = xml.replace('<?xml version="1.0" encoding="utf-8"?>', "")
    return xml[1:]


def xml_to_json(xml_string: str) -> str:
    """Convert an XML production export to the JSON shape used by Production."""

    def postprocessor(path, key, value):
        return key, "" if value is None else value

    data = xmltodict.parse(xml_string, postprocessor=postprocessor)
    if "Production" in data:
        production_obj = data["Production"]
        production_name = production_obj.get("@Name", "Production")
        data = {production_name: production_obj}
    return json.dumps(data)


def stream_to_string(stream, buffer=1000000) -> str:
    string = ""
    stream.Rewind()
    while not stream.AtEnd:
        string += stream.Read(buffer)
    return string


def string_to_stream(iris, string: str, buffer=1000000):
    stream = iris.cls("%Stream.GlobalCharacter")._New()
    chunks = [string[i : i + buffer] for i in range(0, len(string), buffer)]
    for chunk in chunks:
        stream.Write(chunk)
    return stream


def guess_path(module: str, path: str) -> str:
    """Determine the full file path for a module name under a base path."""
    if not module:
        raise ValueError("Module name cannot be empty")

    if module.startswith("."):
        dot_count = len(module) - len(module.lstrip("."))
        module = module[dot_count:]
        for _ in range(dot_count - 1):
            path = os.path.dirname(path)

    if module.endswith(".py"):
        module_path = module.replace(".", os.sep)
    else:
        module_path = module.replace(".", os.sep) + ".py"
    return os.path.join(path, module_path)
