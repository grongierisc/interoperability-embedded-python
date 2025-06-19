from typing import Any, Optional, Union

from . import _iris
from ._dispatch import dispatch_serializer

class _GeneratorRequest:
    """Generator class to interetate over responses from a request.
    This class is used to handle the responses from a request in a generator-like manner."""

    def __init__(self, host: Any, target: str, request: Any, 
                 timeout: int = -1, description: Optional[str] = None) -> None:
        self.host = host
        self.target = target
        self.request = request

        ack_response = self.host.send_request_sync(self.target, dispatch_serializer(self.request, is_generator=True),
                                                  timeout=timeout, description=description)
        
        if ack_response is None or not ack_response._IsA("IOP.Generator.Message.Ack"):
            raise RuntimeError("Failed to send request, no acknowledgment received.")

    def __iter__(self):
        return self

    def __next__(self):
        poll = _iris.get_iris().IOP.Generator.Message.Poll._New()
        rsp = self.host.send_request_sync(self.target, poll)
        if rsp is None or (hasattr(rsp, '_IsA') and rsp._IsA("IOP.Generator.Message.Stop")):
            raise StopIteration("No more responses available.")
        return rsp