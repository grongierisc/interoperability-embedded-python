from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .component import ComponentRef
from .types import GraphEdge, TargetSetting, TargetSettingRef, _edge_identity


class _ProductionAuthoringMixin:
    """Internal graph mutation and component-resolution behavior."""

    if TYPE_CHECKING:
        _items: list[ComponentRef]
        _items_by_name: dict[str, ComponentRef]
        _connections: dict[tuple[str, str], list[str]]
        _edges: list[GraphEdge]

        def item(self, name: str) -> ComponentRef: ...

        def resolve_target_setting_ref(
            self, target_setting_ref: TargetSettingRef
        ) -> str: ...

        def resolve_target(self, target_or_ref: str) -> str: ...

    def _component_name(self, target_component: ComponentRef | str) -> str:
        if isinstance(target_component, ComponentRef):
            if target_component.production is not self:
                raise ValueError("target component belongs to a different Production")
            return target_component.name
        target_name = str(target_component)
        if target_name not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {target_name}")
        return target_name

    def _runtime_component_name(
        self,
        component: ComponentRef | TargetSettingRef | str,
    ) -> str:
        if isinstance(component, TargetSettingRef):
            component_name = self.resolve_target_setting_ref(component)
        elif isinstance(component, ComponentRef):
            component_name = self._component_name(component)
        else:
            component_name = self.resolve_target(str(component))
        if component_name not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {component_name}")
        return component_name

    def _component_ref(self, item: ComponentRef | str) -> ComponentRef:
        if isinstance(item, ComponentRef):
            if item.production is not self:
                raise ValueError("component belongs to a different Production")
            return item
        return self.item(str(item))

    def _add_item(self, ref: ComponentRef) -> None:
        if not ref.name:
            raise ValueError("Production item name is required")
        if ref.name in self._items_by_name:
            raise ValueError(f"Production item already exists: {ref.name}")
        if ref.component_class is not None:
            for existing in self._items:
                if (
                    existing.component_class is not None
                    and existing.component_class is not ref.component_class
                    and existing.class_name == ref.class_name
                ):
                    raise ValueError(
                        f"Python classes {existing.component_class.__qualname__!r} and "
                        f"{ref.component_class.__qualname__!r} produce the same IRIS "
                        f"proxy class name {ref.class_name!r}. Rename one of the "
                        "Python classes or supply an explicit class_name= to resolve "
                        "the collision."
                    )
        self._items.append(ref)
        self._items_by_name[ref.name] = ref
        self._apply_target_defaults()

    def _apply_target_defaults(self) -> None:
        for ref in self._items:
            for setting_name, target_name in self._target_default_routes(ref):
                if setting_name not in ref.host_settings:
                    if setting_name in ref.target_setting_names:
                        continue
                    ref.host_settings[setting_name] = target_name
                ref.target_setting_names.add(setting_name)
                if str(ref.host_settings[setting_name]) != target_name:
                    continue
                if target_name not in self._items_by_name:
                    continue
                self._register_connection(ref.name, setting_name, target_name)

    def _target_default_routes(self, ref: ComponentRef) -> tuple[tuple[str, str], ...]:
        if ref.component_class is None:
            return ()
        routes: list[tuple[str, str]] = []
        for setting_name, descriptor in target_settings(ref.component_class):
            target_name = target_default_name(descriptor.default)
            if target_name:
                routes.append((setting_name, target_name))
        return tuple(routes)

    def _register_connection(
        self,
        source_item: str,
        source_target_setting: str,
        target_name: str,
        *,
        origin: str = "authored",
        interaction: str = "request",
        metadata: dict[str, Any] | None = None,
        replace_target_setting: bool = False,
        validate_target: bool = True,
    ) -> None:
        if source_item not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {source_item}")
        if validate_target and target_name not in self._items_by_name:
            raise ValueError(f"Production item does not exist: {target_name}")
        if source_target_setting:
            key = (source_item, source_target_setting)
            if replace_target_setting:
                self._connections[key] = [target_name]
            else:
                self._connections.setdefault(key, [])
                if target_name not in self._connections[key]:
                    self._connections[key].append(target_name)

        edge = GraphEdge(
            source_item=source_item,
            source_target_setting=source_target_setting,
            target=target_name,
            origin=origin,
            interaction=interaction,
            metadata=dict(metadata or {}),
        )
        if replace_target_setting and source_target_setting:
            self._edges = [
                existing
                for existing in self._edges
                if not (
                    existing.source_item == source_item
                    and existing.source_target_setting == source_target_setting
                )
            ]
        edge_key = _edge_identity(edge)
        self._edges = [
            existing
            for existing in self._edges
            if _edge_identity(existing) != edge_key
        ]
        self._edges.append(edge)


def connection_mode(mode: str) -> str:
    normalized = str(mode or "").strip().lower()
    if normalized in {"replace", "set"}:
        return "replace"
    if normalized in {"add", "append"}:
        return "add"
    if normalized in {"remove", "delete", "disconnect"}:
        return "remove"
    raise ValueError(
        "Unsupported connection mode: "
        f"{mode!r}. Expected 'replace', 'add', or 'remove'."
    )


def target_settings(component_class: type) -> tuple[tuple[str, TargetSetting], ...]:
    descriptors: dict[str, TargetSetting] = {}
    for base in reversed(component_class.__mro__):
        for name, value in base.__dict__.items():
            if isinstance(value, TargetSetting):
                descriptors[name] = value
    return tuple(descriptors.items())


def target_default_name(value: Any) -> str:
    if value is None:
        return ""
    name = getattr(value, "name", value)
    return str(name).strip()
