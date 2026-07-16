from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from importlib.resources import files
from pathlib import Path

AGENTS = ("codex", "claude", "gemini")
MANAGED_START = "<!-- iop-agent-guidance:start -->"
MANAGED_END = "<!-- iop-agent-guidance:end -->"

_AGENT_PATHS = {
    "codex": ("AGENTS.md", ".codex/skills"),
    "claude": ("CLAUDE.md", ".claude/skills"),
    "gemini": ("GEMINI.md", ".gemini/skills"),
}

_SKILL_DESCRIPTIONS = {
    "build-iop-app": (
        "Build or modify an IoP application using production graphs, messages, "
        "components, tests, and the relevant bundled cookbook. Use for new or "
        "changed Business Services, Business Processes, Business Operations, "
        "routes, settings, healthcare flows, or complete productions."
    ),
    "validate-iop-app": (
        "Validate an IoP application with unit tests, strict migration dry-run, "
        "and optional IRIS runtime checks. Use after changing messages, components, "
        "production topology, settings, migration files, or runtime behavior."
    ),
}


class AgentGuidanceConflictError(ValueError):
    """Raised when installed framework-owned guidance would be overwritten."""

    def __init__(self, paths: Iterable[Path]):
        self.paths = tuple(paths)
        joined = ", ".join(str(path) for path in self.paths)
        super().__init__(
            "agent guidance conflicts with existing files: "
            f"{joined}. Re-run with --force-agent-guidance to replace them."
        )


@dataclass(frozen=True)
class InstallResult:
    target: Path
    agents: tuple[str, ...]
    written: tuple[Path, ...]
    unchanged: tuple[Path, ...]


def install_agent_guidance(
    target: str | Path = ".",
    *,
    agents: Iterable[str] | None = None,
    force: bool = False,
) -> InstallResult:
    """Install version-matched IoP guidance into an application repository."""
    target_path = Path(target).expanduser().resolve()
    selected_agents = _normalize_agents(agents)
    owned_files = _owned_file_manifest(target_path, selected_agents)
    root_files = _root_file_manifest(target_path, selected_agents)

    conflicts = [
        path
        for path, content in owned_files.items()
        if path.exists() and path.read_bytes() != content
    ]
    if conflicts and not force:
        raise AgentGuidanceConflictError(conflicts)

    manifest = {**owned_files, **root_files}
    written: list[Path] = []
    unchanged: list[Path] = []
    for path, content in manifest.items():
        if path.exists() and path.read_bytes() == content:
            unchanged.append(path)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        written.append(path)

    return InstallResult(
        target=target_path,
        agents=selected_agents,
        written=tuple(written),
        unchanged=tuple(unchanged),
    )


def _normalize_agents(agents: Iterable[str] | None) -> tuple[str, ...]:
    values = tuple(agents or AGENTS)
    invalid = sorted(set(values) - set(AGENTS))
    if invalid:
        raise ValueError(f"unsupported agents: {', '.join(invalid)}")
    return tuple(agent for agent in AGENTS if agent in values)


def _owned_file_manifest(
    target: Path,
    agents: tuple[str, ...],
) -> dict[Path, bytes]:
    manifest: dict[Path, bytes] = {}
    resource_root = files("iop.ai")
    for resource_dir, destination in (
        (resource_root.joinpath("guidance"), target / ".config" / "AGENTS"),
        (
            resource_root.joinpath("skills"),
            target / ".config" / "AGENTS" / "skills",
        ),
    ):
        _add_resource_tree(manifest, resource_dir, destination)

    for agent in agents:
        _, skills_root = _AGENT_PATHS[agent]
        for skill_name, description in _SKILL_DESCRIPTIONS.items():
            wrapper = _skill_wrapper(skill_name, description)
            path = target / skills_root / skill_name / "SKILL.md"
            manifest[path] = wrapper.encode("utf-8")
    return manifest


def _root_file_manifest(
    target: Path,
    agents: tuple[str, ...],
) -> dict[Path, bytes]:
    manifest: dict[Path, bytes] = {}
    for agent in agents:
        root_name, _ = _AGENT_PATHS[agent]
        path = target / root_name
        current = path.read_text(encoding="utf-8") if path.exists() else ""
        merged = _merge_managed_block(current, _root_block(agent))
        manifest[path] = merged.encode("utf-8")
    return manifest


def _add_resource_tree(manifest, resource, destination: Path) -> None:
    for child in resource.iterdir():
        child_destination = destination / child.name
        if child.is_dir():
            _add_resource_tree(manifest, child, child_destination)
        elif child.name != "__pycache__":
            manifest[child_destination] = child.read_bytes()


def _merge_managed_block(content: str, block: str) -> str:
    managed = f"{MANAGED_START}\n{block.rstrip()}\n{MANAGED_END}"
    start = content.find(MANAGED_START)
    end = content.find(MANAGED_END)
    if start >= 0 and end >= start:
        end += len(MANAGED_END)
        return f"{content[:start]}{managed}{content[end:]}"
    if not content.strip():
        return f"{managed}\n"
    return f"{content.rstrip()}\n\n{managed}\n"


def _root_block(agent: str) -> str:
    import_line = {
        "codex": "Read `.config/AGENTS/instructions.md` before changing code.",
        "claude": "@.config/AGENTS/instructions.md",
        "gemini": "@./.config/AGENTS/instructions.md",
    }[agent]
    return "\n".join(
        (
            "# IoP Agent Guidance",
            "",
            "This repository contains an IoP application.",
            import_line,
            "Use `build-iop-app` for application changes.",
            "Use `validate-iop-app` for verification.",
        )
    )


def _skill_wrapper(skill_name: str, description: str) -> str:
    return (
        "---\n"
        f"name: {skill_name}\n"
        f"description: {description}\n"
        "---\n\n"
        f"Read and follow `.config/AGENTS/skills/{skill_name}/SKILL.md`. "
        "Load its referenced files only when the workflow calls for them.\n"
    )
