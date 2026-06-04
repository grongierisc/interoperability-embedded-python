from __future__ import annotations

import getpass
import hashlib
import json
import os
import socket
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .diff import _connection_signature, _item_signature, _production_signature
from .types import ProductionDiffEntry

SAFE = "safe"
DESTRUCTIVE = "destructive"
UNSUPPORTED = "unsupported"

_ITEM_FIELD_OPS = {
    "category",
    "pool_size",
    "enabled",
    "foreground",
    "comment",
    "log_trace_events",
    "schedule",
}


@dataclass(frozen=True)
class ProductionPlanOperation:
    """One granular operation in a production change plan."""

    id: str
    op_type: str
    action: str
    kind: str
    path: str
    before: Any = None
    after: Any = None
    risk: str = SAFE
    reason: str = ""
    detail: str = ""

    @property
    def supported(self) -> bool:
        return self.risk != UNSUPPORTED

    @property
    def allowed_by_default(self) -> bool:
        return self.risk == SAFE

    @property
    def requires_allow_destructive(self) -> bool:
        return self.risk == DESTRUCTIVE

    def can_apply(self, *, allow_destructive: bool = False) -> bool:
        if not self.supported:
            return False
        if self.allowed_by_default:
            return True
        return bool(allow_destructive and self.requires_allow_destructive)

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "op_type": self.op_type,
            "action": self.action,
            "kind": self.kind,
            "path": self.path,
            "risk": self.risk,
            "allowed_by_default": self.allowed_by_default,
        }
        if self.before is not None:
            data["before"] = self.before
        if self.after is not None:
            data["after"] = self.after
        if self.reason:
            data["reason"] = self.reason
        if self.detail:
            data["detail"] = self.detail
        data.update(_operation_target_data(self))
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProductionPlanOperation:
        return cls(
            id=str(data["id"]),
            op_type=str(data["op_type"]),
            action=str(data.get("action", "")),
            kind=str(data.get("kind", "")),
            path=str(data.get("path", "")),
            before=data.get("before"),
            after=data.get("after"),
            risk=str(data.get("risk", SAFE)),
            reason=str(data.get("reason", "")),
            detail=str(data.get("detail", "")),
        )

    def to_text(self) -> str:
        suffix = f" [{self.risk}]"
        reason = f": {self.reason}" if self.reason else ""
        return f"{self.id} {self.op_type} {self.path}{suffix}{reason}"


@dataclass(frozen=True)
class ProductionChangePlan:
    """Versioned desired-vs-current production change plan."""

    id: str
    production_name: str
    namespace: str = ""
    created_at: str = ""
    source_fingerprint: str = ""
    desired_fingerprint: str = ""
    operations: tuple[ProductionPlanOperation, ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def has_changes(self) -> bool:
        return bool(self.operations)

    @property
    def safe_operations(self) -> tuple[ProductionPlanOperation, ...]:
        return tuple(op for op in self.operations if op.allowed_by_default)

    @property
    def blocked_operations(self) -> tuple[ProductionPlanOperation, ...]:
        return tuple(op for op in self.operations if not op.allowed_by_default)

    def operations_for_apply(
        self,
        *,
        allow_destructive: bool = False,
    ) -> tuple[ProductionPlanOperation, ...]:
        return tuple(
            op for op in self.operations if op.can_apply(allow_destructive=allow_destructive)
        )

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "id": self.id,
            "production": self.production_name,
            "namespace": self.namespace,
            "created_at": self.created_at,
            "source_fingerprint": self.source_fingerprint,
            "desired_fingerprint": self.desired_fingerprint,
            "has_changes": self.has_changes,
            "operations": [op.to_dict() for op in self.operations],
        }
        if self.warnings:
            data["warnings"] = list(self.warnings)
        if self.metadata:
            data["metadata"] = dict(self.metadata)
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProductionChangePlan:
        return cls(
            id=str(data["id"]),
            production_name=str(data.get("production") or data.get("production_name")),
            namespace=str(data.get("namespace") or ""),
            created_at=str(data.get("created_at") or ""),
            source_fingerprint=str(data.get("source_fingerprint") or ""),
            desired_fingerprint=str(data.get("desired_fingerprint") or ""),
            operations=tuple(
                ProductionPlanOperation.from_dict(op)
                for op in data.get("operations", ())
            ),
            warnings=tuple(str(item) for item in data.get("warnings", ())),
            metadata=dict(data.get("metadata") or {}),
        )

    def to_text(self) -> str:
        lines = [
            f"Production change plan: {self.production_name}",
            f"  id: {self.id}",
        ]
        if self.namespace:
            lines.append(f"  namespace: {self.namespace}")
        if not self.operations:
            lines.append("  no changes")
        else:
            lines.append("  operations:")
            lines.extend(f"    {op.to_text()}" for op in self.operations)
        if self.warnings:
            lines.append("  warnings:")
            lines.extend(f"    {warning}" for warning in self.warnings)
        return "\n".join(lines)

    def save(self, path: str | os.PathLike[str]) -> None:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self.to_dict(), indent=2, sort_keys=True),
            encoding="utf-8",
        )

    @classmethod
    def load(cls, path: str | os.PathLike[str]) -> ProductionChangePlan:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def __str__(self) -> str:
        return self.to_text()


@dataclass(frozen=True)
class ProductionApplyResult:
    """Result returned after applying a production change plan."""

    plan_id: str
    production_name: str
    backup_path: str = ""
    operations: tuple[dict[str, Any], ...] = ()
    updated_runtime: bool = False

    @property
    def applied(self) -> int:
        return sum(1 for op in self.operations if op.get("status") == "applied")

    @property
    def skipped(self) -> int:
        return sum(1 for op in self.operations if op.get("status") == "skipped")

    @property
    def failed(self) -> int:
        return sum(1 for op in self.operations if op.get("status") == "failed")

    @property
    def success(self) -> bool:
        return self.failed == 0

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "plan_id": self.plan_id,
            "production": self.production_name,
            "success": self.success,
            "applied": self.applied,
            "skipped": self.skipped,
            "failed": self.failed,
            "updated_runtime": self.updated_runtime,
            "operations": list(self.operations),
        }
        if self.backup_path:
            data["backup_path"] = self.backup_path
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProductionApplyResult:
        return cls(
            plan_id=str(data.get("plan_id") or data.get("plan") or ""),
            production_name=str(data.get("production") or ""),
            backup_path=str(data.get("backup_path") or ""),
            operations=tuple(dict(op) for op in data.get("operations", ())),
            updated_runtime=bool(data.get("updated_runtime", False)),
        )

    def to_text(self) -> str:
        lines = [
            f"Production apply result: {self.production_name}",
            f"  plan: {self.plan_id}",
            f"  applied: {self.applied}, skipped: {self.skipped}, failed: {self.failed}",
        ]
        if self.backup_path:
            lines.append(f"  backup: {self.backup_path}")
        if self.operations:
            lines.append("  operations:")
            for op in self.operations:
                lines.append(
                    f"    {op.get('id', '')} {op.get('op_type', '')}: "
                    f"{op.get('status', 'unknown')}"
                )
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_text()


@dataclass(frozen=True)
class ProductionVerifyResult:
    """Result returned after verifying a production change plan."""

    plan_id: str
    production_name: str
    converged_operations: tuple[str, ...] = ()
    failed_operations: tuple[dict[str, Any], ...] = ()
    residual_operations: tuple[dict[str, Any], ...] = ()
    warnings: tuple[str, ...] = ()

    @property
    def success(self) -> bool:
        return not self.failed_operations

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "plan_id": self.plan_id,
            "production": self.production_name,
            "success": self.success,
            "converged_operations": list(self.converged_operations),
            "failed_operations": list(self.failed_operations),
            "residual_operations": list(self.residual_operations),
        }
        if self.warnings:
            data["warnings"] = list(self.warnings)
        return data

    def to_text(self) -> str:
        lines = [
            f"Production verify result: {self.production_name}",
            f"  plan: {self.plan_id}",
            f"  success: {str(self.success).lower()}",
            f"  converged: {len(self.converged_operations)}",
            f"  failed: {len(self.failed_operations)}",
            f"  residual: {len(self.residual_operations)}",
        ]
        if self.failed_operations:
            lines.append("  failed operations:")
            lines.extend(
                f"    {op.get('id', '')} {op.get('path', '')}" for op in self.failed_operations
            )
        if self.residual_operations:
            lines.append("  residual operations:")
            lines.extend(
                f"    {op.get('id', '')} {op.get('path', '')}"
                for op in self.residual_operations
            )
        if self.warnings:
            lines.append("  warnings:")
            lines.extend(f"    {warning}" for warning in self.warnings)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.to_text()


def build_change_plan(desired, current) -> ProductionChangePlan:
    diff = desired.diff_deployable(current)
    operations = tuple(_operation_from_diff(index, change) for index, change in enumerate(diff.changes, start=1))
    created_at = datetime.now(UTC).isoformat()
    source_fingerprint = production_fingerprint(current)
    desired_fingerprint = production_fingerprint(desired)
    plan_id = _plan_id(
        desired.name,
        source_fingerprint,
        desired_fingerprint,
        operations,
    )
    namespace = getattr(desired, "namespace", None) or getattr(current, "namespace", None) or ""
    return ProductionChangePlan(
        id=plan_id,
        production_name=desired.name,
        namespace=str(namespace or ""),
        created_at=created_at,
        source_fingerprint=source_fingerprint,
        desired_fingerprint=desired_fingerprint,
        operations=operations,
        warnings=diff.warnings,
        metadata={
            "generator": "iop.production.plan.v1",
            "default_policy": "safe-only",
        },
    )


def production_fingerprint(production) -> str:
    payload = production.to_dict()
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def create_backup(
    *,
    backup_dir: str | os.PathLike[str],
    plan: ProductionChangePlan,
    current,
    current_export: dict[str, Any],
    connections: Any,
    queues: Any,
) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    backup_path = Path(backup_dir) / f"{timestamp}-{plan.id[:12]}"
    backup_path.mkdir(parents=True, exist_ok=False)
    _write_json(backup_path / "production.json", current_export)
    (backup_path / "production.xml").write_text(current.to_xml(), encoding="utf-8")
    _write_json(backup_path / "connections.json", connections or {})
    _write_json(backup_path / "queues.json", queues or {})
    plan.save(backup_path / "plan.json")
    _write_json(
        backup_path / "metadata.json",
        {
            "backup_id": backup_path.name,
            "created_at": datetime.now(UTC).isoformat(),
            "user": getpass.getuser(),
            "host": socket.gethostname(),
            "namespace": plan.namespace,
            "production": plan.production_name,
            "plan_id": plan.id,
            "source_fingerprint": plan.source_fingerprint,
            "desired_fingerprint": plan.desired_fingerprint,
        },
    )
    return backup_path


def verify_change_plan(plan: ProductionChangePlan, current) -> ProductionVerifyResult:
    converged: list[str] = []
    failed: list[dict[str, Any]] = []
    residual: list[dict[str, Any]] = []

    for operation in plan.operations:
        if not operation.allowed_by_default:
            residual.append(operation.to_dict())
            continue
        if _operation_converged(operation, current):
            converged.append(operation.id)
        else:
            failed.append(operation.to_dict())

    return ProductionVerifyResult(
        plan_id=plan.id,
        production_name=plan.production_name,
        converged_operations=tuple(converged),
        failed_operations=tuple(failed),
        residual_operations=tuple(residual),
        warnings=tuple(current.graph().warnings),
    )


def operation_result(
    operation: ProductionPlanOperation,
    *,
    status: str,
    message: str = "",
) -> dict[str, Any]:
    data = operation.to_dict()
    data["status"] = status
    if message:
        data["message"] = message
    return data


def skipped_operation_results(
    plan: ProductionChangePlan,
    *,
    allow_destructive: bool,
) -> list[dict[str, Any]]:
    results = []
    for operation in plan.operations:
        if operation.can_apply(allow_destructive=allow_destructive):
            continue
        if operation.risk == DESTRUCTIVE:
            message = "requires allow_destructive=True"
        elif operation.risk == UNSUPPORTED:
            message = operation.reason or "unsupported operation"
        else:
            message = "operation is not applicable"
        results.append(operation_result(operation, status="skipped", message=message))
    return results


def _operation_from_diff(index: int, change: ProductionDiffEntry) -> ProductionPlanOperation:
    op_type, risk, reason = _classify_change(change)
    return ProductionPlanOperation(
        id=f"{index:04d}-{op_type}",
        op_type=op_type,
        action=change.action,
        kind=change.kind,
        path=change.path,
        before=change.before,
        after=change.after,
        risk=risk,
        reason=reason,
        detail=change.detail,
    )


def _classify_change(change: ProductionDiffEntry) -> tuple[str, str, str]:
    if change.kind == "item":
        if change.action == "add":
            return "add_item", SAFE, ""
        if change.action == "remove":
            return "delete_item", DESTRUCTIVE, "item deletion is destructive"
        field_name = _item_field_name(change.path)
        if field_name == "class_name":
            return "replace_item_class", DESTRUCTIVE, "class replacement can change runtime behavior"
        if field_name in _ITEM_FIELD_OPS:
            return "set_item_field", SAFE, ""
        return "set_item_field", UNSUPPORTED, "unsupported item field"

    if change.kind == "setting":
        if change.action == "remove":
            return "remove_setting", DESTRUCTIVE, "setting removal is destructive"
        return "set_setting", SAFE, ""

    if change.kind == "connection":
        source_item, source_target_setting = _connection_source(change.path)
        if not source_item or not source_target_setting:
            return (
                "set_route_setting",
                UNSUPPORTED,
                "runtime-only route has no source setting to mutate",
            )
        if change.action == "remove":
            return "remove_route", DESTRUCTIVE, "route removal is destructive"
        return "set_route_setting", SAFE, ""

    if change.kind == "production":
        return "set_production_field", SAFE, ""

    return "unsupported", UNSUPPORTED, "unsupported diff entry"


def _operation_converged(operation: ProductionPlanOperation, current) -> bool:
    if operation.op_type == "add_item":
        return _item_matches(current, operation.path, operation.after)
    if operation.op_type == "delete_item":
        item_name = _item_name(operation.path)
        return item_name not in current._items_by_name
    if operation.op_type in {"set_item_field", "replace_item_class"}:
        item_name = _item_name(operation.path)
        field_name = _item_field_name(operation.path)
        ref = current._items_by_name.get(item_name)
        if ref is None:
            return False
        return _item_signature(ref).get(field_name) == operation.after
    if operation.op_type == "set_production_field":
        field_name = operation.path.removeprefix("production.")
        return _production_signature(current).get(field_name) == operation.after
    if operation.op_type == "set_setting":
        parsed = _setting_path(operation.path)
        if parsed is None:
            return False
        item_name, target, setting_name = parsed
        ref = current._items_by_name.get(item_name)
        if ref is None:
            return False
        if target == "Host":
            return _string_value(ref.host_settings.get(setting_name)) == _string_value(operation.after)
        if target == "Adapter":
            return _string_value(ref.adapter_settings.get(setting_name)) == _string_value(operation.after)
        if target == "Other":
            return ref.other_settings == operation.after
        return False
    if operation.op_type == "remove_setting":
        parsed = _setting_path(operation.path)
        if parsed is None:
            return False
        item_name, target, setting_name = parsed
        ref = current._items_by_name.get(item_name)
        if ref is None:
            return True
        if target == "Host":
            return setting_name not in ref.host_settings
        if target == "Adapter":
            return setting_name not in ref.adapter_settings
        return False
    if operation.op_type == "set_route_setting":
        source_item, source_target_setting = _connection_source(operation.path)
        if not source_item or not source_target_setting:
            return False
        connections = _connection_signature(current)
        return (
            connections.get((source_item, source_target_setting), [])
            == operation.after
        )
    if operation.op_type == "remove_route":
        source_item, source_target_setting = _connection_source(operation.path)
        connections = _connection_signature(current)
        return (source_item, source_target_setting) not in connections
    return False


def _item_matches(current, path: str, expected: Any) -> bool:
    item_name = _item_name(path)
    ref = current._items_by_name.get(item_name)
    return ref is not None and _item_signature(ref) == expected


def _item_name(path: str) -> str:
    if not path.startswith("items."):
        return ""
    remainder = path.removeprefix("items.")
    if ".settings." in remainder:
        return remainder.split(".settings.", 1)[0]
    for field_name in ("class_name", *_ITEM_FIELD_OPS):
        suffix = f".{field_name}"
        if remainder.endswith(suffix):
            return remainder[: -len(suffix)]
    return remainder


def _item_field_name(path: str) -> str:
    for field_name in ("class_name", *_ITEM_FIELD_OPS):
        if path.endswith(f".{field_name}"):
            return field_name
    return ""


def _setting_path(path: str) -> tuple[str, str, str] | None:
    if not path.startswith("items.") or ".settings." not in path:
        return None
    item_name, rest = path.removeprefix("items.").split(".settings.", 1)
    if "." not in rest:
        return item_name, rest, ""
    target, setting_name = rest.split(".", 1)
    return item_name, target, setting_name


def _connection_source(path: str) -> tuple[str, str]:
    source = path.removeprefix("connections.")
    source_item, separator, source_target_setting = source.rpartition(".")
    if not separator:
        return source, ""
    return source_item, source_target_setting


def _string_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value)


def _operation_target_data(operation: ProductionPlanOperation) -> dict[str, Any]:
    if operation.op_type in {"add_item", "delete_item"}:
        return {"item": _item_name(operation.path)}
    if operation.op_type in {"set_item_field", "replace_item_class"}:
        return {
            "item": _item_name(operation.path),
            "field": _item_field_name(operation.path),
        }
    if operation.op_type in {"set_setting", "remove_setting"}:
        parsed = _setting_path(operation.path)
        if parsed is None:
            return {}
        item_name, target, setting_name = parsed
        return {
            "item": item_name,
            "target": target,
            "setting": setting_name,
        }
    if operation.op_type in {"set_route_setting", "remove_route"}:
        source_item, source_target_setting = _connection_source(operation.path)
        return {
            "source_item": source_item,
            "source_target_setting": source_target_setting,
            "item": source_item,
            "target": "Host",
            "setting": source_target_setting,
        }
    if operation.op_type == "set_production_field":
        return {"field": operation.path.removeprefix("production.")}
    return {}


def _plan_id(
    production_name: str,
    source_fingerprint: str,
    desired_fingerprint: str,
    operations: tuple[ProductionPlanOperation, ...],
) -> str:
    payload = {
        "production": production_name,
        "source": source_fingerprint,
        "desired": desired_fingerprint,
        "operations": [op.to_dict() for op in operations],
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _write_json(path: Path, data: Any) -> None:
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True, default=str),
        encoding="utf-8",
    )
