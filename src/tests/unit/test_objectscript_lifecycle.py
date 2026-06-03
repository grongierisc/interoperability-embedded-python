import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TEARDOWN_DISPATCH = re.compile(r'_dispatch_on_tear_down"\(([^)]*)\)')


def _teardown_dispatch_args(path: str) -> list[str]:
    text = (ROOT / path).read_text(encoding="utf-8")
    return [match.group(1).strip() for match in TEARDOWN_DISPATCH.finditer(text)]


def test_objectscript_teardown_dispatch_passes_host_object():
    call_sites = {
        "src/iop/cls/IOP/Common.cls": _teardown_dispatch_args(
            "src/iop/cls/IOP/Common.cls"
        ),
        "src/iop/cls/IOP/PrivateSession/Duplex.cls": _teardown_dispatch_args(
            "src/iop/cls/IOP/PrivateSession/Duplex.cls"
        ),
    }

    assert call_sites == {
        "src/iop/cls/IOP/Common.cls": ["$this"],
        "src/iop/cls/IOP/PrivateSession/Duplex.cls": ["$this"],
    }
