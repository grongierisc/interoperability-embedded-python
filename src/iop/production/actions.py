from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .component import ComponentRef
from .import_ import _normalize_queue_info
from .planning import (
    ProductionApplyResult,
    ProductionChangePlan,
    ProductionVerifyResult,
    create_backup,
    production_fingerprint,
    skipped_operation_results,
    verify_change_plan,
)
from .rendering import message_to_classname_body
from .runtime import _has_remote_director, _ProductionRuntime, _temporary_env
from .types import TargetSettingRef


def start(production, detach: bool = True) -> None:
    director = _ProductionRuntime(production).director
    if detach:
        director.start_production(production.name)
    else:
        director.start_production_with_log(production.name)


def stop(production) -> None:
    director = _ProductionRuntime(production).director
    require_current_production(production, director, "stop")
    director.stop_production()


def restart(production) -> None:
    director = _ProductionRuntime(production).director
    require_current_production(production, director, "restart")
    director.restart_production()


def kill(production) -> None:
    director = _ProductionRuntime(production).director
    require_current_production(production, director, "kill")
    director.shutdown_production()


def status(production) -> dict:
    return _ProductionRuntime(production).director.status_production()


def queue(production, *, refresh: bool = True) -> dict[str, dict[str, Any]]:
    if not refresh:
        return {name: dict(value) for name, value in production._queue_info.items()}
    info = _ProductionRuntime(production).director.export_production_queue_info(
        production.name
    )
    queue_map, _queue_warnings = _normalize_queue_info(info)
    production._queue_info = queue_map
    return {name: dict(value) for name, value in queue_map.items()}


def update(production) -> None:
    director = _ProductionRuntime(production).director
    require_current_production(production, director, "update")
    director.update_production()


def start_component(
    production,
    component: ComponentRef | TargetSettingRef | str,
) -> None:
    component_name = production._runtime_component_name(component)
    director = _ProductionRuntime(production).director
    require_current_runtime(
        production,
        director,
        f"start component {component_name!r} in production {production.name!r}",
    )
    director.start_component(component_name)


def stop_component(
    production,
    component: ComponentRef | TargetSettingRef | str,
) -> None:
    component_name = production._runtime_component_name(component)
    director = _ProductionRuntime(production).director
    require_current_runtime(
        production,
        director,
        f"stop component {component_name!r} in production {production.name!r}",
    )
    director.stop_component(component_name)


def restart_component(
    production,
    component: ComponentRef | TargetSettingRef | str,
) -> None:
    component_name = production._runtime_component_name(component)
    director = _ProductionRuntime(production).director
    require_current_runtime(
        production,
        director,
        f"restart component {component_name!r} in production {production.name!r}",
    )
    director.restart_component(component_name)


def export(production) -> dict:
    return _ProductionRuntime(production).director.export_production(production.name)


def set_default(production) -> None:
    _ProductionRuntime(production).director.set_default_production(production.name)


def sync(
    production, *, root_path: str | None = None, update_runtime: bool = True
) -> None:
    if _has_remote_director(production):
        raise NotImplementedError(
            "Production.sync() can only register directly with local IRIS. "
            "Use `iop --migrate <settings_file>` for remote migrations."
        )
    from ..migration import utils as migration_utils

    with _temporary_env("IRISNAMESPACE", production.namespace):
        migration_utils.set_productions_settings([production], root_path)
        if update_runtime:
            from ..runtime.local import _LocalDirector

            _LocalDirector().update_production()


def apply(
    production,
    *,
    plan: ProductionChangePlan | None = None,
    allow_destructive: bool = False,
    backup_dir: str = ".iop/backups",
    root_path: str | None = None,
    update_runtime: bool = True,
) -> ProductionApplyResult:
    director = _ProductionRuntime(production).director
    if _director_is_remote(director) or _has_remote_director(production):
        raise RuntimeError(
            "Remote production plan apply is not supported in v1. "
            "Run apply from a local IRIS environment."
        )

    if plan is None:
        plan = production.plan()
    assert plan is not None
    if plan.production_name != production.name:
        raise ValueError(
            f"Plan targets {plan.production_name!r}, not {production.name!r}."
        )

    apply_operations = plan.operations_for_apply(
        allow_destructive=allow_destructive,
    )
    skipped = skipped_operation_results(
        plan,
        allow_destructive=allow_destructive,
    )
    if not apply_operations:
        return ProductionApplyResult(
            plan_id=plan.id,
            production_name=plan.production_name,
            operations=tuple(skipped),
        )

    current, exported, connections, queues = _read_current_snapshot(production, director)
    current_fingerprint = production_fingerprint(current)
    if current_fingerprint != plan.source_fingerprint:
        raise RuntimeError(
            "Cannot apply production plan: current IRIS production changed since "
            "the plan was created."
        )

    backup_path = create_backup(
        backup_dir=backup_dir,
        plan=plan,
        current=current,
        current_export=exported,
        connections=connections,
        queues=queues,
    )

    _register_plan_classes(production, root_path=root_path)
    raw_result = director.apply_production_plan(
        plan.to_dict(),
        allow_destructive=allow_destructive,
    )
    if isinstance(raw_result, dict) and raw_result.get("error"):
        raise RuntimeError(str(raw_result["error"]))
    operation_results = _apply_operation_results(raw_result)
    operation_results.extend(skipped)
    updated_runtime = _update_runtime_if_current(
        production,
        director,
        update_runtime=update_runtime,
    )
    return ProductionApplyResult(
        plan_id=plan.id,
        production_name=plan.production_name,
        backup_path=str(backup_path),
        operations=tuple(operation_results),
        updated_runtime=updated_runtime,
    )


def verify(production, plan: ProductionChangePlan) -> ProductionVerifyResult:
    director = _ProductionRuntime(production).director
    current = production.from_iris(
        plan.production_name,
        namespace=production.namespace,
        director=director,
    )
    return verify_change_plan(plan, current)


def rollback_backup(
    backup_path: str,
    *,
    director: Any = None,
    namespace: str | None = None,
    allow_destructive: bool = False,
    update_runtime: bool = True,
) -> ProductionVerifyResult:
    if not allow_destructive:
        raise RuntimeError(
            "Rollback restores a full production export and requires "
            "allow_destructive=True."
        )
    if director is None:
        from ..runtime.local import _LocalDirector

        director = _LocalDirector()
    if _director_is_remote(director):
        raise RuntimeError(
            "Remote production rollback is not supported in v1. "
            "Run rollback from a local IRIS environment."
        )

    path = Path(backup_path)
    production_data = json.loads((path / "production.json").read_text(encoding="utf-8"))
    metadata = json.loads((path / "metadata.json").read_text(encoding="utf-8"))
    production_name = metadata.get("production") or next(iter(production_data))

    from ..migration import utils as migration_utils

    with _temporary_env("IRISNAMESPACE", namespace or metadata.get("namespace") or None):
        migration_utils.register_production_definition(
            production_name,
            _normalized_production_definition(production_name, production_data),
        )
        if update_runtime:
            _update_runtime_if_current_name(
                production_name,
                director,
                update_runtime=True,
            )

    from .model import Production

    restored = Production.from_iris(
        production_name,
        director=director,
        namespace=namespace or metadata.get("namespace") or None,
    )
    expected = _production_from_export(
        production_name,
        production_data,
        director=director,
        namespace=namespace or metadata.get("namespace") or None,
    )
    result_plan = ProductionChangePlan(
        id=str(metadata.get("plan_id") or ""),
        production_name=production_name,
        namespace=str(namespace or metadata.get("namespace") or ""),
        source_fingerprint=production_fingerprint(expected),
        desired_fingerprint=production_fingerprint(expected),
    )
    if production_fingerprint(restored) != production_fingerprint(expected):
        return ProductionVerifyResult(
            plan_id=result_plan.id,
            production_name=production_name,
            failed_operations=(
                {"id": "rollback", "path": production_name, "status": "failed"},
            ),
        )
    return ProductionVerifyResult(
        plan_id=result_plan.id,
        production_name=production_name,
        converged_operations=("rollback",),
    )


def log(production, top: int | None = None) -> None:
    director = _ProductionRuntime(production).director
    if top is None:
        director.log_production()
    else:
        director.log_production_top(top)


def test_component(
    production,
    target_or_ref: str | TargetSettingRef | ComponentRef,
    message: Any = None,
    classname: str | None = None,
    body: str | dict | None = None,
) -> Any:
    director = _ProductionRuntime(production).director
    target_name = production.resolve_target(target_or_ref)

    raise_if_existing_production_not_running(production, director)

    if classname is None and body is None and message is not None:
        classname, body = message_to_classname_body(message)
        if classname is not None:
            message = None
    return director.test_component(
        target_name,
        message=message,
        classname=classname,
        body=body,
    )


def raise_if_existing_production_not_running(production, director: Any) -> None:
    production_name, state = read_status(production, director, "test")
    state_lower = str(state).lower()
    if production_name == production.name and str(state).lower() == "running":
        return

    if (
        production_name
        and production_name != production.name
        and state_lower == "running"
    ):
        raise RuntimeError(
            f"Production {production.name!r} exists but is not running "
            f"(currently running production is {production_name!r}). "
            f"{switch_running_production_message(production, production_name)} "
            "Do that before calling `prod.test(...)`."
        )
    if production_name and production_name != production.name:
        detail = f"current default production is {production_name!r}"
    elif state:
        detail = f"current status is {state!r}"
    else:
        detail = "runtime status did not report a running production"
    raise RuntimeError(
        f"Production {production.name!r} exists but is not running ({detail}). "
        f"Start it with `iop --start {production.name} --detach` or "
        "`prod.start()` before calling `prod.test(...)`."
    )


def require_current_production(production, director: Any, action: str) -> None:
    require_current_runtime(
        production,
        director,
        f"{action} production {production.name!r}",
    )


def require_current_runtime(production, director: Any, action: str) -> None:
    production_name, state = read_status(production, director, action)
    if production_name == production.name:
        return

    if production_name:
        detail = f"current/default production is {production_name!r}"
    elif state:
        detail = f"current status is {state!r}"
    else:
        detail = "runtime status did not report a current/default production"
    raise RuntimeError(
        f"Cannot {action}: {detail}. "
        f"Select {production.name!r} with `prod.set_default()` or start it with "
        "`prod.start()` before using this lifecycle method."
    )


def read_status(production, director: Any, action: str) -> tuple[str, str]:
    try:
        status = director.status_production()
    except Exception as exc:
        raise RuntimeError(
            f"Cannot {action}: could not verify production status ({exc})."
        ) from exc
    if not isinstance(status, dict):
        raise RuntimeError(
            f"Cannot {action}: production status response is invalid ({status!r})."
        )
    production_name = status.get("Production") or status.get("production") or ""
    state = status.get("Status") or status.get("status") or ""
    return str(production_name), str(state)


def switch_running_production_message(production, current_production: str) -> str:
    return (
        f"IRIS can run only one production at a time. Stop {current_production!r} "
        f"first with `iop --stop`, then start {production.name!r} with "
        f"`iop --start {production.name} --detach`; or call `prod.stop()` and "
        "`prod.start()` explicitly."
    )


def _read_current_snapshot(production, director: Any):
    exported = director.export_production(production.name)
    try:
        connections = director.export_production_connections(production.name)
    except Exception as exc:
        connections = {"warnings": [f"Could not export runtime connections: {exc}"]}
    try:
        queues = director.export_production_queue_info(production.name)
    except Exception as exc:
        queues = {"warnings": [f"Could not export queue info: {exc}"]}
    current = production.from_dict(
        exported,
        connections=connections,
        queue_info=queues,
        namespace=production.namespace,
        director=director,
    )
    return current, exported, connections, queues


def _register_plan_classes(production, *, root_path: str | None = None) -> None:
    from ..migration import utils as migration_utils

    with _temporary_env("IRISNAMESPACE", production.namespace):
        migration_utils._register_production_object_messages(production)
        migration_utils._register_production_object_components(production, root_path)


def _apply_operation_results(raw_result: Any) -> list[dict[str, Any]]:
    if raw_result is None:
        return []
    if isinstance(raw_result, str):
        raw_result = json.loads(raw_result)
    if isinstance(raw_result, dict):
        return [dict(item) for item in raw_result.get("operations", ())]
    if isinstance(raw_result, list):
        return [dict(item) for item in raw_result]
    return []


def _update_runtime_if_current(
    production,
    director: Any,
    *,
    update_runtime: bool,
) -> bool:
    return _update_runtime_if_current_name(
        production.name,
        director,
        update_runtime=update_runtime,
    )


def _update_runtime_if_current_name(
    production_name: str,
    director: Any,
    *,
    update_runtime: bool,
) -> bool:
    if not update_runtime:
        return False
    try:
        status = director.status_production()
    except Exception:
        return False
    current = status.get("Production") or status.get("production") or ""
    if current != production_name:
        return False
    director.update_production()
    return True


def _director_is_remote(director: Any) -> bool:
    try:
        from ..runtime.remote import _RemoteDirector
    except Exception:
        return False
    return isinstance(director, _RemoteDirector)


def _production_from_export(
    production_name: str,
    production_data: dict[str, Any],
    *,
    director: Any,
    namespace: str | None,
):
    from .model import Production

    return Production.from_dict(
        production_data,
        namespace=namespace,
        director=director,
    )


def _normalized_production_definition(
    production_name: str,
    production_data: dict[str, Any],
) -> dict[str, Any]:
    if "Production" in production_data:
        definition = production_data["Production"]
    else:
        definition = production_data.get(production_name)
        if definition is None and production_data:
            definition = production_data[next(iter(production_data))]
    if not isinstance(definition, dict):
        raise ValueError("Production backup must contain a production definition.")
    normalized = dict(definition)
    normalized.setdefault("@Name", production_name)
    return {"Production": normalized}
