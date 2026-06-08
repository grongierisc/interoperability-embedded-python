from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SourceConnection:
    target: str
    source: str
    detail: str = ""
    interaction: str = "request"


_PYTHON_REQUEST_METHODS = {
    "send_request_sync",
    "send_request_async",
    "send_request_async_ng",
    "send_generator_request",
}
_PYTHON_MULTI_REQUEST_METHODS = {"send_multi_request_sync"}
_OBJECTSCRIPT_STRING = r'"(?:""|[^"])*"'
_OBJECTSCRIPT_CLASS_RE = re.compile(
    r"(?im)^\s*Class\s+(?P<class>[A-Za-z%][\w%]*(?:\.[A-Za-z%][\w%]*)*)\b"
)
_OBJECTSCRIPT_EXTENDS_RE = re.compile(
    r"(?ims)^\s*Class\s+[A-Za-z%][\w%]*(?:\.[A-Za-z%][\w%]*)*"
    r"\s+Extends\s+(?P<super>\([^)]+\)|[^{\[]+)"
)
_OBJECTSCRIPT_SEND_RE = re.compile(
    rf"(?i)\b(?P<method>SendRequest(?:Sync|Async|AsyncNG)?)\s*"
    rf"\(\s*(?P<target>{_OBJECTSCRIPT_STRING}|\.\.[A-Za-z%][\w%]*)"
)
_OBJECTSCRIPT_PROPERTY_DEFAULT_RE = re.compile(
    rf"(?im)^\s*Property\s+(?P<name>[A-Za-z%][\w%]*)\b"
    rf"[^\n]*\bInitialExpression\s*=\s*(?P<value>{_OBJECTSCRIPT_STRING})"
)
_IGNORED_SOURCE_PARTS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "node_modules",
    "venv",
}
_LOW_PRIORITY_SOURCE_PARTS = {"docs", "test", "tests"}


def infer_source_connections(
    class_name: str,
    host_settings: dict[str, Any],
    *,
    root: Path | None = None,
) -> list[SourceConnection]:
    """Infer static request targets from local Python or ObjectScript source."""
    normalized_class_name = str(class_name or "").strip()
    if not normalized_class_name:
        return []

    source_root = root or Path.cwd()
    source = _objectscript_source_index(_root_key(source_root)).get(
        normalized_class_name
    )
    python_class_name = _iop_python_class_name(
        host_settings,
        source,
    )
    if python_class_name:
        return _infer_python_connections(
            python_class_name,
            host_settings,
            source_root,
        )
    return _infer_objectscript_connections(
        normalized_class_name,
        host_settings,
        source_root,
        source=source,
    )


def _infer_python_connections(
    class_name: str,
    _host_settings: dict[str, Any],
    root: Path,
) -> list[SourceConnection]:
    candidates = [
        info
        for info in _python_source_index(_root_key(root))
        if _python_class_matches(class_name, info.class_name, info.module_hint)
    ]
    candidates.sort(key=lambda item: (_source_rank(item.path), item.path, item.class_name))

    connections: list[SourceConnection] = []
    for candidate in candidates[:1]:
        connections.extend(candidate.connections)
    return _unique_connections(connections)


def _infer_objectscript_connections(
    class_name: str,
    host_settings: dict[str, Any],
    root: Path,
    *,
    source: _ObjectScriptSource | None = None,
) -> list[SourceConnection]:
    source = source or _objectscript_source_index(_root_key(root)).get(class_name)
    if source is None:
        return []

    property_defaults = _objectscript_property_defaults(source.text)
    connections: list[SourceConnection] = []
    for match in _OBJECTSCRIPT_SEND_RE.finditer(source.text):
        method_name = match.group("method")
        interaction = _objectscript_method_interaction(method_name)
        target_expression = match.group("target").strip()
        if target_expression.startswith('"'):
            targets = [_decode_objectscript_string(target_expression)]
            detail = f"{method_name} literal"
        else:
            setting_name = target_expression[2:]
            targets = (
                _split_targets(host_settings.get(setting_name, ""))
                or property_defaults.get(setting_name, [])
            )
            detail = f"{method_name} {target_expression}"

        for target in targets:
            connections.append(
                SourceConnection(
                    target=target,
                    source="ObjectScript source",
                    detail=detail,
                    interaction=interaction,
                )
            )
    return _unique_connections(connections)


def _iop_python_class_name(
    host_settings: dict[str, Any],
    source: _ObjectScriptSource | None,
) -> str:
    defaults = _objectscript_property_defaults(source.text) if source else {}
    if source is not None and not _objectscript_extends_iop(source.text):
        return ""
    module = (
        _string_setting(host_settings, "%module")
        or _first_default(defaults, "%module")
    )
    classname = (
        _string_setting(host_settings, "%classname")
        or _first_default(defaults, "%classname")
    )
    if not module or not classname:
        return ""
    return f"Python.{module}.{classname}"


@dataclass(frozen=True)
class _PythonClassInfo:
    class_name: str
    module_hint: str
    path: str
    connections: tuple[SourceConnection, ...]


@dataclass(frozen=True)
class _ObjectScriptSource:
    text: str
    path: str


@lru_cache(maxsize=8)
def _python_source_index(root: str) -> tuple[_PythonClassInfo, ...]:
    root_path = Path(root)
    infos: list[_PythonClassInfo] = []
    for path in _iter_source_files(root_path, "*.py"):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue

        module_hint = _python_module_hint(root_path, path)
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            connections = tuple(_python_class_connections(node))
            infos.append(
                _PythonClassInfo(
                    class_name=node.name,
                    module_hint=module_hint,
                    path=str(path),
                    connections=connections,
                )
            )
    return tuple(infos)


@lru_cache(maxsize=8)
def _objectscript_source_index(root: str) -> dict[str, _ObjectScriptSource]:
    root_path = Path(root)
    sources: dict[str, _ObjectScriptSource] = {}
    candidates: list[tuple[tuple[int, str], str, _ObjectScriptSource]] = []
    for path in _iter_source_files(root_path, "*.cls"):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            try:
                text = path.read_text()
            except OSError:
                continue
        except OSError:
            continue
        match = _OBJECTSCRIPT_CLASS_RE.search(text)
        if match is None:
            continue
        class_name = match.group("class")
        source = _ObjectScriptSource(text=text, path=str(path))
        candidates.append(((_source_rank(str(path)), str(path)), class_name, source))

    for _, class_name, source in sorted(candidates, key=lambda item: item[0]):
        sources.setdefault(class_name, source)
    return sources


def _python_class_connections(class_node: ast.ClassDef) -> list[SourceConnection]:
    string_values = _python_string_values(class_node)
    connections: list[SourceConnection] = []

    for node in ast.walk(class_node):
        if not isinstance(node, ast.Call):
            continue
        call_name = _python_call_name(node.func)
        if call_name in _PYTHON_REQUEST_METHODS:
            for target, detail, interaction in _python_request_targets(
                node,
                string_values,
                call_name,
            ):
                connections.append(
                    SourceConnection(
                        target=target,
                        source="Python source",
                        detail=detail,
                        interaction=interaction,
                    )
                )
        elif call_name in _PYTHON_MULTI_REQUEST_METHODS:
            for target, detail, interaction in _python_multi_request_targets(
                node,
                string_values,
                call_name,
            ):
                connections.append(
                    SourceConnection(
                        target=target,
                        source="Python source",
                        detail=detail,
                        interaction=interaction,
                    )
                )
    return _unique_connections(connections)


def _python_string_values(class_node: ast.ClassDef) -> dict[str, list[str]]:
    values: dict[str, list[str]] = {}
    for node in class_node.body:
        if isinstance(node, ast.Assign):
            literal = _python_literal_string(node.value)
            if literal is None:
                continue
            for target in node.targets:
                _add_python_assignment_value(
                    values,
                    target,
                    literal,
                    class_body=True,
                )
        elif isinstance(node, ast.AnnAssign):
            literal = _python_literal_string(node.value)
            if literal is None:
                literal = _python_setting_default(node.annotation)
            if literal is None:
                continue
            _add_python_assignment_value(
                values,
                node.target,
                literal,
                class_body=True,
            )
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    literal = _python_literal_string(child.value)
                    if literal is None:
                        continue
                    for target in child.targets:
                        _add_python_assignment_value(
                            values,
                            target,
                            literal,
                            class_body=False,
                        )
                elif isinstance(child, ast.AnnAssign):
                    literal = _python_literal_string(child.value)
                    if literal is None:
                        continue
                    _add_python_assignment_value(
                        values,
                        child.target,
                        literal,
                        class_body=False,
                    )
    return values


def _python_request_targets(
    call: ast.Call,
    string_values: dict[str, list[str]],
    call_name: str,
) -> list[tuple[str, str, str]]:
    target_node = _python_call_target_node(call)
    if target_node is None:
        return []
    return _resolve_python_targets(
        target_node,
        string_values,
        call_name,
        _python_call_interaction(call_name),
    )


def _python_multi_request_targets(
    call: ast.Call,
    string_values: dict[str, list[str]],
    call_name: str,
) -> list[tuple[str, str, str]]:
    if not call.args:
        return []
    collection = call.args[0]
    if not isinstance(collection, (ast.List, ast.Tuple)):
        return []

    targets: list[tuple[str, str, str]] = []
    for item in collection.elts:
        if not isinstance(item, ast.Tuple) or not item.elts:
            continue
        targets.extend(
            _resolve_python_targets(
                item.elts[0],
                string_values,
                call_name,
                "sync",
            )
        )
    return targets


def _resolve_python_targets(
    node: ast.AST,
    string_values: dict[str, list[str]],
    call_name: str,
    interaction: str,
) -> list[tuple[str, str, str]]:
    literal = _python_literal_string(node)
    if literal is not None:
        return [(literal, f"{call_name} literal", interaction)]

    name = _python_reference_name(node)
    if name is None:
        return []
    return [
        (value, f"{call_name} {name}", interaction)
        for value in string_values.get(name, [])
    ]


def _python_call_target_node(call: ast.Call) -> ast.AST | None:
    for keyword in call.keywords:
        if keyword.arg == "target":
            return keyword.value
    if call.args:
        return call.args[0]
    return None


def _python_assignment_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    return _python_reference_name(node)


def _python_reference_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and node.value.id == "self"
    ):
        return f"self.{node.attr}"
    return None


def _python_literal_string(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    try:
        value = ast.literal_eval(node)
    except (ValueError, SyntaxError):
        return None
    if isinstance(value, str) and value:
        return value
    return None


def _python_setting_default(annotation: ast.AST) -> str | None:
    for node in ast.walk(annotation):
        if not isinstance(node, ast.Call):
            continue
        if _python_call_name(node.func) != "Setting":
            continue
        for keyword in node.keywords:
            if keyword.arg == "default":
                return _python_literal_string(keyword.value)
    return None


def _python_call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return None


def _python_call_interaction(call_name: str) -> str:
    normalized = str(call_name or "").lower()
    if "async" in normalized:
        return "async"
    if "sync" in normalized:
        return "sync"
    return "request"


def _objectscript_method_interaction(method_name: str) -> str:
    normalized = str(method_name or "").lower()
    if "async" in normalized:
        return "async"
    if "sync" in normalized:
        return "sync"
    return "request"


def _python_class_matches(
    requested_class: str,
    actual_class: str,
    module_hint: str,
) -> bool:
    parts = [part for part in requested_class.split(".") if part]
    if parts and parts[0] == "Python":
        parts = parts[1:]
    if not parts:
        return False
    if actual_class != parts[-1]:
        return False
    if len(parts) == 1:
        return True
    requested_module = ".".join(parts[:-1])
    return (
        module_hint == requested_module
        or module_hint.endswith(f".{requested_module}")
        or requested_module.endswith(f".{module_hint}")
    )


def _python_module_hint(root: Path, path: Path) -> str:
    try:
        relative = path.relative_to(root)
    except ValueError:
        relative = path
    without_suffix = relative.with_suffix("")
    return ".".join(part for part in without_suffix.parts if part != "__init__")


def _add_python_string_value(
    values: dict[str, list[str]],
    name: str | None,
    value: str,
) -> None:
    if name is None:
        return
    targets = values.setdefault(name, [])
    if value not in targets:
        targets.append(value)


def _add_python_assignment_value(
    values: dict[str, list[str]],
    target: ast.AST,
    value: str,
    *,
    class_body: bool,
) -> None:
    name = _python_assignment_name(target)
    _add_python_string_value(values, name, value)
    if class_body and isinstance(target, ast.Name):
        _add_python_string_value(values, f"self.{target.id}", value)


def _objectscript_property_defaults(text: str) -> dict[str, list[str]]:
    defaults: dict[str, list[str]] = {}
    for match in _OBJECTSCRIPT_PROPERTY_DEFAULT_RE.finditer(text):
        defaults[match.group("name")] = [
            _decode_objectscript_string(match.group("value"))
        ]
    return defaults


def _objectscript_extends_iop(text: str) -> bool:
    match = _OBJECTSCRIPT_EXTENDS_RE.search(text)
    if match is None:
        return False
    supers = {
        value.strip()
        for value in re.split(r"[\s(),]+", match.group("super"))
        if value.strip()
    }
    return any(value == "IOP.Common" or value.startswith("IOP.") for value in supers)


def _string_setting(settings: dict[str, Any], name: str) -> str:
    value = settings.get(name)
    if value is None:
        return ""
    return str(value).strip()


def _first_default(defaults: dict[str, list[str]], name: str) -> str:
    values = defaults.get(name, [])
    if not values:
        return ""
    return str(values[0]).strip()


def _decode_objectscript_string(value: str) -> str:
    return value[1:-1].replace('""', '"')


def _split_targets(value: Any) -> list[str]:
    if value is None:
        return []
    return [
        target.strip()
        for target in str(value).split(",")
        if target and target.strip()
    ]


def _iter_source_files(root: Path, pattern: str):
    try:
        paths = root.rglob(pattern)
    except OSError:
        return
    for path in paths:
        if _is_ignored_path(path):
            continue
        if path.is_file():
            yield path


def _is_ignored_path(path: Path) -> bool:
    return any(part in _IGNORED_SOURCE_PARTS for part in path.parts)


def _source_rank(path: str) -> int:
    parts = set(Path(path).parts)
    return 1 if parts & _LOW_PRIORITY_SOURCE_PARTS else 0


def _root_key(root: Path) -> str:
    try:
        return str(root.resolve())
    except OSError:
        return str(root.absolute())


def _unique_connections(connections: list[SourceConnection]) -> list[SourceConnection]:
    unique: list[SourceConnection] = []
    seen: set[tuple[str, str, str, str]] = set()
    for connection in connections:
        if not connection.target:
            continue
        key = (
            connection.target,
            connection.source,
            connection.detail,
            connection.interaction,
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(connection)
    return unique
