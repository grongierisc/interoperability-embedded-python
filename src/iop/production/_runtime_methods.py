from __future__ import annotations

from typing import Any

from ..runtime.protocol import DirectorProtocol as _DirectorProtocol
from . import actions as _actions
from .component import ComponentRef
from .inspection import component_runtime_info, inspect_component
from .planning import (
    ProductionApplyResult,
    ProductionChangePlan,
    ProductionVerifyResult,
)
from .types import TargetSettingRef


class _ProductionRuntimeMixin:
    """Runtime-facing Production methods kept separate from graph authoring."""

    def start(self, detach: bool = True) -> None:
        _actions.start(self, detach=detach)

    def stop(self) -> None:
        _actions.stop(self)

    def restart(self) -> None:
        _actions.restart(self)

    def kill(self) -> None:
        _actions.kill(self)

    def status(self) -> dict:
        return _actions.status(self)

    def queue(self, *, refresh: bool = True) -> dict[str, dict[str, Any]]:
        return _actions.queue(self, refresh=refresh)

    def queue_info(self, *, refresh: bool = True) -> dict[str, dict[str, Any]]:
        return self.queue(refresh=refresh)

    def update(self) -> None:
        _actions.update(self)

    def inspect_component(
        self,
        component: ComponentRef | TargetSettingRef | str,
        *,
        refresh: bool = True,
    ) -> dict[str, Any]:
        return inspect_component(self, component, refresh=refresh)

    def start_component(self, component: ComponentRef | TargetSettingRef | str) -> None:
        _actions.start_component(self, component)

    def stop_component(self, component: ComponentRef | TargetSettingRef | str) -> None:
        _actions.stop_component(self, component)

    def restart_component(
        self,
        component: ComponentRef | TargetSettingRef | str,
    ) -> None:
        _actions.restart_component(self, component)

    def export(self) -> dict:
        return _actions.export(self)

    def set_default(self) -> None:
        _actions.set_default(self)

    def sync(self, *, root_path: str | None = None, update: bool = True) -> None:
        _actions.sync(self, root_path=root_path, update_runtime=update)

    def apply(
        self,
        plan: ProductionChangePlan | None = None,
        *,
        allow_destructive: bool = False,
        backup_dir: str = ".iop/backups",
        root_path: str | None = None,
        update: bool = True,
    ) -> ProductionApplyResult:
        return _actions.apply(
            self,
            plan=plan,
            allow_destructive=allow_destructive,
            backup_dir=backup_dir,
            root_path=root_path,
            update_runtime=update,
        )

    def verify(self, plan: ProductionChangePlan) -> ProductionVerifyResult:
        return _actions.verify(self, plan)

    @staticmethod
    def rollback_backup(
        backup_path: str,
        *,
        director: _DirectorProtocol | None = None,
        namespace: str | None = None,
        allow_destructive: bool = False,
        update: bool = True,
    ) -> ProductionVerifyResult:
        return _actions.rollback_backup(
            backup_path,
            director=director,
            namespace=namespace,
            allow_destructive=allow_destructive,
            update_runtime=update,
        )

    def log(self, top: int | None = None) -> None:
        _actions.log(self, top)

    def test_component(
        self,
        target_or_ref: str | TargetSettingRef | ComponentRef,
        message: Any = None,
        classname: str | None = None,
        body: str | dict | None = None,
    ) -> Any:
        return _actions.test_component(
            self,
            target_or_ref,
            message=message,
            classname=classname,
            body=body,
        )

    def test(
        self,
        target_or_ref: str | TargetSettingRef | ComponentRef,
        message: Any = None,
        classname: str | None = None,
        body: str | dict | None = None,
    ) -> Any:
        return self.test_component(
            target_or_ref,
            message=message,
            classname=classname,
            body=body,
        )

    def _raise_if_existing_production_not_running(self, director: Any) -> None:
        _actions.raise_if_existing_production_not_running(self, director)

    def _require_current_production(self, director: Any, action: str) -> None:
        _actions.require_current_production(self, director, action)

    def _require_current_runtime(self, director: Any, action: str) -> None:
        _actions.require_current_runtime(self, director, action)

    def _read_status(self, director: Any, action: str) -> tuple[str, str]:
        return _actions.read_status(self, director, action)

    def _switch_running_production_message(self, current_production: str) -> str:
        return _actions.switch_running_production_message(self, current_production)

    def _component_runtime_info(self, component_name: str) -> dict[str, Any]:
        return component_runtime_info(self, component_name)
