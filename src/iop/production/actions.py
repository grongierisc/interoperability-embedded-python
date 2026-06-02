from __future__ import annotations

from typing import Any

from .component import ComponentRef
from .import_ import _normalize_queue_info
from .rendering import message_to_classname_body
from .runtime import _has_remote_director, _ProductionRuntime, _temporary_env
from .types import Port


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


def start_component(production, component: ComponentRef | Port | str) -> None:
    component_name = production._runtime_component_name(component)
    director = _ProductionRuntime(production).director
    require_current_runtime(
        production,
        director,
        f"start component {component_name!r} in production {production.name!r}",
    )
    director.start_component(component_name)


def stop_component(production, component: ComponentRef | Port | str) -> None:
    component_name = production._runtime_component_name(component)
    director = _ProductionRuntime(production).director
    require_current_runtime(
        production,
        director,
        f"stop component {component_name!r} in production {production.name!r}",
    )
    director.stop_component(component_name)


def restart_component(production, component: ComponentRef | Port | str) -> None:
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


def log(production, top: int | None = None) -> None:
    director = _ProductionRuntime(production).director
    if top is None:
        director.log_production()
    else:
        director.log_production_top(top)


def test_component(
    production,
    target_or_port: str | Port | ComponentRef,
    message: Any = None,
    classname: str | None = None,
    body: str | dict | None = None,
) -> Any:
    director = _ProductionRuntime(production).director
    target_name = production.resolve_target(target_or_port)

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
