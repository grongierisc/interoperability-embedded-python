"""Source-level contracts for the ObjectScript async response poller."""
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
COMMON_CLASS = ROOT / "src/iop/cls/IOP/Common.cls"


def _dispatch_is_request_done() -> str:
    source = COMMON_CLASS.read_text(encoding="utf-8")
    match = re.search(
        r"Method dispatchIsRequestDone\(.*?\n\}\n\nXData MessageMap",
        source,
        flags=re.DOTALL,
    )
    assert match is not None
    return match.group(0)


def test_async_response_poll_scans_a_bounded_queue_snapshot_without_blocking():
    method = _dispatch_is_request_done()

    assert "GetCount(pQueueName)" in method
    assert "for tQueueIndex=1:1:tQueueCount" in method
    assert "DeQueue(pQueueName,.tResponseHeader,0," in method
    assert "DeQueue($$$queueSyncCallQueueName" not in method


def test_async_response_poll_requeues_unmatched_responses():
    method = _dispatch_is_request_done()

    assert "if 'tFound" in method
    assert "Ens.Queue).EnQueue(tResponseHeader)" in method
