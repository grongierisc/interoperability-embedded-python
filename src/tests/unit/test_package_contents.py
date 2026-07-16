from pathlib import Path


def test_all_objectscript_sources_are_declared_as_package_data():
    root = Path(__file__).resolve().parents[3]
    sources = list((root / "src" / "iop" / "cls").rglob("*.cls"))

    assert sources
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert '"iop" = ["py.typed", "ai/**/*.md"]' in pyproject
    assert '"*" = ["*.cls", "cls/**/*.cls"]' in pyproject


def test_ai_guidance_sources_are_declared_as_package_data():
    root = Path(__file__).resolve().parents[3]
    resources = list((root / "src" / "iop" / "ai").rglob("*.md"))

    assert resources
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    manifest = (root / "MANIFEST.in").read_text(encoding="utf-8")
    assert '"iop" = ["py.typed", "ai/**/*.md"]' in pyproject
    assert "recursive-include src/iop/ai *.md" in manifest
