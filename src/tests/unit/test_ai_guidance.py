from __future__ import annotations

from importlib.resources import files
from pathlib import Path

import pytest

from iop.ai import AgentGuidanceConflictError, install_agent_guidance


def test_install_agent_guidance_creates_all_agent_entrypoints(tmp_path):
    result = install_agent_guidance(tmp_path)

    assert result.agents == ("codex", "claude", "gemini")
    assert (tmp_path / "AGENTS.md").is_file()
    assert (tmp_path / "CLAUDE.md").is_file()
    assert (tmp_path / "GEMINI.md").is_file()
    for agent_dir in (".codex", ".claude", ".gemini"):
        for skill in ("build-iop-app", "validate-iop-app"):
            wrapper = tmp_path / agent_dir / "skills" / skill / "SKILL.md"
            assert wrapper.is_file()
            assert f"name: {skill}" in wrapper.read_text(encoding="utf-8")

    assert (
        tmp_path
        / ".config"
        / "AGENTS"
        / "skills"
        / "build-iop-app"
        / "references"
        / "cookbooks"
        / "index.md"
    ).is_file()


def test_install_agent_guidance_selects_agents_and_is_idempotent(tmp_path):
    first = install_agent_guidance(tmp_path, agents=["claude"])
    second = install_agent_guidance(tmp_path, agents=["claude"])

    assert first.written
    assert not second.written
    assert second.unchanged
    assert (tmp_path / "CLAUDE.md").is_file()
    assert not (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / "GEMINI.md").exists()


def test_install_agent_guidance_preserves_existing_root_guide(tmp_path):
    agents_file = tmp_path / "AGENTS.md"
    agents_file.write_text("# Project Rules\n\nKeep this text.\n", encoding="utf-8")

    install_agent_guidance(tmp_path, agents=["codex"])
    first = agents_file.read_text(encoding="utf-8")
    install_agent_guidance(tmp_path, agents=["codex"])
    second = agents_file.read_text(encoding="utf-8")

    assert "# Project Rules" in first
    assert "Keep this text." in first
    assert first.count("<!-- iop-agent-guidance:start -->") == 1
    assert second == first


def test_install_agent_guidance_preflights_conflicts_before_writing(tmp_path):
    conflict = (
        tmp_path
        / ".config"
        / "AGENTS"
        / "skills"
        / "build-iop-app"
        / "SKILL.md"
    )
    conflict.parent.mkdir(parents=True)
    conflict.write_text("local override\n", encoding="utf-8")

    with pytest.raises(AgentGuidanceConflictError) as exc_info:
        install_agent_guidance(tmp_path)

    assert conflict in exc_info.value.paths
    assert conflict.read_text(encoding="utf-8") == "local override\n"
    assert not (tmp_path / "AGENTS.md").exists()


def test_install_agent_guidance_force_replaces_owned_files(tmp_path):
    install_agent_guidance(tmp_path)
    instructions = tmp_path / ".config" / "AGENTS" / "instructions.md"
    instructions.write_text("local override\n", encoding="utf-8")

    result = install_agent_guidance(tmp_path, force=True)

    assert instructions in result.written
    assert "IoP Application Guidance" in instructions.read_text(encoding="utf-8")


def test_packaged_skills_follow_common_agent_skill_frontmatter():
    skills = files("iop.ai").joinpath("skills")
    for skill_name in ("build-iop-app", "validate-iop-app"):
        content = skills.joinpath(skill_name, "SKILL.md").read_text(encoding="utf-8")
        assert content.startswith("---\n")
        frontmatter = content.split("---\n", 2)[1]
        assert f"name: {skill_name}\n" in frontmatter
        assert "description: " in frontmatter


def test_documentation_pages_include_packaged_ai_references():
    root = Path(__file__).resolve().parents[3]
    references = (
        root
        / "src"
        / "iop"
        / "ai"
        / "skills"
        / "build-iop-app"
        / "references"
    )
    includes = {
        root / "docs" / "cookbooks" / cookbook.name: cookbook
        for cookbook in (references / "cookbooks").glob("*.md")
    }
    includes.update(
        {
            root / "docs" / "healthcare-ai-coding.md": references
            / "healthcare-ai-coding.md",
            root / "docs" / "production-change-workflow.md": references
            / "production-change-workflow.md",
            root / "docs" / "agent-guidance.md": references / "agent-guidance.md",
            root / "docs" / "getting-started" / "register-component.md": references
            / "getting-started"
            / "register-component.md",
        }
    )

    for documentation, packaged in includes.items():
        relative = packaged.relative_to(root).as_posix()
        assert documentation.read_text(encoding="utf-8") == f'--8<-- "{relative}"\n'
