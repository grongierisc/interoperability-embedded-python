from pathlib import Path


def test_all_objectscript_sources_are_declared_as_package_data():
    root = Path(__file__).resolve().parents[3]
    sources = list((root / "src" / "iop" / "cls").rglob("*.cls"))

    assert sources
    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    assert '"iop" = ["py.typed"]' in pyproject
    assert '"*" = ["*.cls", "cls/**/*.cls"]' in pyproject
