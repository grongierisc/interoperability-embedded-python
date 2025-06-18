from typing import Any, Optional, Union

from . import _iris
from ._message import _GeneratorMessage


class _GeneratorRequest:
    """Generator class to interetate over responses from a request.
    This class is used to handle the responses from a request in a generator-like manner."""

    def __init__(self, host: Any, target: str, request: Union[_GeneratorMessage, Any], 
                 timeout: int = -1, description: Optional[str] = None) -> None:
        self.host = host
        self.target = target
        self.request = request
        self.timeout = timeout
        self.description = description
        self._response = None

        # if not isinstance(self.request, _GeneratorMessage):
        #     raise TypeError("request must be of type Message or _GeneratorMessage")
        
        ack_rsponse = self.host.send_request_sync(self.target, self.request)
        
        if ack_rsponse is None:
            raise RuntimeError("Failed to send request, no acknowledgment received.")

    def __iter__(self):
        return self

    def __next__(self):
        poll = _iris.get_iris().IOP.PrivateSession.Message.Poll._New()
        rsp = self.host.send_request_sync(self.target, poll)
        if rsp is None:
            raise StopIteration("No more responses available.")
        return rsp