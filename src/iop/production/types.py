from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass, field
from typing import Any, overload

from ..components.settings import Category, Setting, controls


class TargetSetting(Setting):
    """Production target setting descriptor created by target()."""

    def __init__(self, **kwargs: Any):
        kwargs.setdefault("iris_type", "Ens.DataType.ConfigName")
        kwargs.setdefault("category", Category.BASIC)
        kwargs.setdefault("control", controls.production_item())
        super().__init__("", **kwargs)

    @overload
    def __get__(self, instance: None, owner: type | None = None) -> TargetSetting: ...

    @overload
    def __get__(self, instance: object, owner: type | None = None) -> str: ...

    def __get__(self, instance, owner=None):
        return super().__get__(instance, owner)


def target(**kwargs: Any) -> TargetSetting:
    """Declare an outbound target setting on a component class."""
    return TargetSetting(**kwargs)


@dataclass
class TargetSettingRef:
    """Bound reference to a component target setting inside a Production."""

    production: Any
    component: Any
    name: str

    @property
    def item_name(self) -> str:
        return self.component.name

    @property
    def path(self) -> str:
        return f"{self.item_name}.{self.name}"

    def resolve(self) -> str:
        return self.production.resolve_target_setting_ref(self)

    def __str__(self) -> str:
        return self.path


@dataclass(frozen=True)
class PersistentMessageRegistration:
    iris_classname: str
    message_class: type
    sync_schema: bool = True


@dataclass(frozen=True)
class GraphNode:
    name: str
    class_name: str
    kind: str = "component"
    enabled: bool | str = True
    category: str = ""
    adapter_class_name: str = ""

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "name": self.name,
            "class_name": self.class_name,
            "kind": self.kind,
            "enabled": self.enabled,
            "category": self.category,
        }
        if self.adapter_class_name:
            data["adapter_class_name"] = self.adapter_class_name
        return data


@dataclass(frozen=True)
class GraphEdge:
    """Possible communication route between two production items.

    An IRIS production topology can be modeled as a directed multigraph of
    possible communication routes. A graph edge is not an execution dependency
    and does not imply DAG semantics.
    """

    source_item: str
    target: str
    source_target_setting: str = ""
    origin: str = "authored"
    interaction: str = "request"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        origin = self.origin or "authored"
        if origin not in {"authored", "runtime", "inferred"}:
            raise ValueError(f"Unsupported GraphEdge origin: {origin!r}")
        object.__setattr__(self, "origin", origin)
        object.__setattr__(self, "interaction", self.interaction or "unknown")
        object.__setattr__(self, "metadata", dict(self.metadata or {}))

    @property
    def runtime(self) -> bool:
        return self.origin == "runtime"

    @property
    def inferred(self) -> bool:
        return self.origin == "inferred"

    @property
    def source(self) -> str:
        if self.source_target_setting:
            return f"{self.source_item}.{self.source_target_setting}"
        return self.source_item

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "source": self.source,
            "source_item": self.source_item,
            "source_target_setting": self.source_target_setting,
            "target": self.target,
            "origin": self.origin,
            "interaction": self.interaction,
        }
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        if self.runtime:
            data["runtime"] = True
        if self.inferred:
            data["inferred"] = True
        return data


@dataclass(frozen=True)
class ProductionGraph:
    production_name: str
    nodes: tuple[GraphNode, ...]
    edges: tuple[GraphEdge, ...]
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "production": self.production_name,
            "nodes": [node.to_dict() for node in self.nodes],
            "edges": [edge.to_dict() for edge in self.edges],
        }
        if self.warnings:
            data["warnings"] = list(self.warnings)
        return data

    def to_text(self) -> str:
        outgoing: dict[str, list[GraphEdge]] = {node.name: [] for node in self.nodes}
        node_names = set(outgoing)
        for edge in self.edges:
            outgoing.setdefault(edge.source_item, []).append(edge)

        lines = [self.production_name]
        for node in self.nodes:
            label = f" [{node.class_name}]" if node.class_name else ""
            lines.append(f"  {node.name}{label}")
            for edge in sorted(
                outgoing.get(node.name, ()),
                key=lambda item: (item.source_target_setting, item.target),
            ):
                source_target_setting = edge.source_target_setting or "(runtime)"
                suffix = "" if edge.target in node_names else " (unresolved)"
                labels = []
                if edge.origin != "authored":
                    labels.append(edge.origin)
                if edge.interaction not in ("", "request"):
                    labels.append(edge.interaction)
                label = f" [{', '.join(labels)}]" if labels else ""
                lines.append(
                    f"    {source_target_setting} -> {edge.target}{suffix}{label}"
                )
        if self.warnings:
            lines.append("  warnings:")
            lines.extend(f"    {warning}" for warning in self.warnings)
        return "\n".join(lines)

    def to_mermaid(self, *, direction: str = "LR") -> str:
        """Render the production topology as a Mermaid flowchart."""
        direction = _mermaid_direction(direction)
        node_ids = _mermaid_node_ids(self.nodes, self.edges)
        defined_node_names = {node.name for node in self.nodes}

        lines = [
            f"flowchart {direction}",
            f"  %% Production: {_mermaid_comment(self.production_name)}",
        ]
        for node in self.nodes:
            lines.append(
                f"  {node_ids[node.name]}[\"{_mermaid_node_label(node)}\"]"
            )

        unresolved_names = sorted({
            name
            for edge in self.edges
            for name in (edge.source_item, edge.target)
            if name not in defined_node_names
        })
        for name in unresolved_names:
            lines.append(
                f"  {node_ids[name]}[\"{_mermaid_text(name)}<br/>(unresolved)\"]"
            )

        for edge in sorted(
            self.edges,
            key=lambda item: (
                item.source_item,
                item.source_target_setting,
                item.target,
                item.origin,
                item.interaction,
            ),
        ):
            lines.append(
                "  "
                f"{node_ids[edge.source_item]} "
                f"-- \"{_mermaid_edge_label(edge)}\" --> "
                f"{node_ids[edge.target]}"
            )

        if self.warnings:
            lines.append("  %% Warnings:")
            lines.extend(
                f"  %% - {_mermaid_comment(warning)}"
                for warning in self.warnings
            )
        return "\n".join(lines) + "\n"

    def __str__(self) -> str:
        return self.to_text()


@dataclass(frozen=True)
class ProductionDiffEntry:
    """One deterministic desired-vs-current production difference."""

    action: str
    kind: str
    path: str
    before: Any = None
    after: Any = None
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "action": self.action,
            "kind": self.kind,
            "path": self.path,
        }
        if self.before is not None:
            data["before"] = self.before
        if self.after is not None:
            data["after"] = self.after
        if self.detail:
            data["detail"] = self.detail
        return data

    def to_text(self) -> str:
        line = f"{self.action} {self.kind} {self.path}"
        if self.detail:
            return f"{line}: {self.detail}"
        if self.action == "change":
            return f"{line}: {_diff_value_text(self.before)} -> {_diff_value_text(self.after)}"
        if self.action == "add":
            return f"{line}: {_diff_value_text(self.after)}"
        if self.action == "remove":
            return f"{line}: {_diff_value_text(self.before)}"
        return line


@dataclass(frozen=True)
class ProductionDiff:
    """Directional diff from current runtime/imported state to desired Python state."""

    production_name: str
    changes: tuple[ProductionDiffEntry, ...]
    warnings: tuple[str, ...] = ()

    @property
    def has_changes(self) -> bool:
        return bool(self.changes)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "production": self.production_name,
            "has_changes": self.has_changes,
            "changes": [change.to_dict() for change in self.changes],
        }
        if self.warnings:
            data["warnings"] = list(self.warnings)
        return data

    def to_text(self) -> str:
        lines = [f"Production diff: {self.production_name}"]
        if self.changes:
            lines.extend(f"  {change.to_text()}" for change in self.changes)
        else:
            lines.append("  no changes")
        if self.warnings:
            lines.append("  warnings:")
            lines.extend(f"    {warning}" for warning in self.warnings)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_text()


def _edge_identity(edge: GraphEdge) -> tuple[Any, ...]:
    return (
        edge.source_item,
        edge.source_target_setting,
        edge.target,
        edge.origin,
        edge.interaction,
        tuple(
            sorted(
                (str(key), _canonical_value(value))
                for key, value in edge.metadata.items()
            )
        ),
    )


def _canonical_value(value: Any) -> Any:
    from .common import _bool_text

    if isinstance(value, dict):
        return {
            str(key): _canonical_value(value[key])
            for key in sorted(value, key=lambda item: str(item))
        }
    if isinstance(value, (list, tuple)):
        return [_canonical_value(item) for item in value]
    if isinstance(value, bool):
        return _bool_text(value)
    if value is None:
        return ""
    return value


def _diff_value_text(value: Any) -> str:
    if isinstance(value, str):
        return repr(value)
    try:
        return json.dumps(value, sort_keys=True)
    except TypeError:
        return repr(value)


def _mermaid_direction(value: str) -> str:
    direction = str(value or "").strip().upper()
    if direction not in {"TB", "TD", "BT", "RL", "LR"}:
        raise ValueError(f"Unsupported Mermaid flowchart direction: {value!r}")
    return direction


def _mermaid_node_ids(
    nodes: tuple[GraphNode, ...],
    edges: tuple[GraphEdge, ...],
) -> dict[str, str]:
    names: list[str] = [node.name for node in nodes]
    for edge in edges:
        for name in (edge.source_item, edge.target):
            if name not in names:
                names.append(name)

    used: set[str] = set()
    node_ids: dict[str, str] = {}
    for name in names:
        base = re.sub(r"\W+", "_", name).strip("_")
        if not base:
            base = "node"
        base = f"node_{base}"
        candidate = base
        index = 2
        while candidate in used:
            candidate = f"{base}_{index}"
            index += 1
        used.add(candidate)
        node_ids[name] = candidate
    return node_ids


def _mermaid_node_label(node: GraphNode) -> str:
    label = _mermaid_text(node.name)
    if node.class_name:
        label = f"{label}<br/>{_mermaid_text(node.class_name)}"
    return label


def _mermaid_edge_label(edge: GraphEdge) -> str:
    parts = [edge.source_target_setting or "(runtime)"]
    if edge.origin != "authored":
        parts.append(edge.origin)
    if edge.interaction not in ("", "request"):
        parts.append(edge.interaction)
    return _mermaid_text(" | ".join(parts))


def _mermaid_text(value: Any) -> str:
    text = str(value).replace("\r\n", "\n").replace("\r", "\n")
    text = " ".join(part.strip() for part in text.split("\n"))
    return html.escape(text, quote=True)


def _mermaid_comment(value: Any) -> str:
    return str(value).replace("\r\n", " ").replace("\n", " ")
