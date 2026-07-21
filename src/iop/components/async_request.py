import asyncio
from typing import Any

from ..messages.base import _Message as Message
from ..messages.dispatch import dispatch_deserializer, dispatch_serializer
from ..runtime import iris as _iris


class AsyncRequest(asyncio.Future):
    _message_header_id: int = 0
    _queue_name: str = ""
    _end_time: int = 0
    _response: Any = None
    _done: bool = False

    def __init__(
        self,
        target: str,
        request: Message | Any,
        timeout: int = -1,
        description: str | None = None,
        host: Any | None = None,
    ) -> None:
        super().__init__()
        self.target = target
        self.request = request
        self.timeout = timeout
        self.description = description
        self.host = host
        if host is None:
            raise ValueError("host parameter cannot be None")
        self._iris_handle = host.iris_handle
        self._message_header_id = 0
        self._queue_name = ""
        self._end_time = 0
        self._response = None
        self._done = False
        self._send_task = asyncio.create_task(self.send())

    async def send(self) -> None:
        try:
            iris = _iris.get_iris()
            message_header_id = iris.ref()
            queue_name = iris.ref()
            end_time = iris.ref()
            request = dispatch_serializer(self.request)

            self._iris_handle.dispatchSendRequestAsyncNG(
                self.target,
                request,
                self.timeout,
                self.description,
                message_header_id,
                queue_name,
                end_time,
            )

            self._message_header_id = message_header_id.value
            self._queue_name = queue_name.value
            self._end_time = end_time.value

            while not self._done:
                await asyncio.sleep(0.1)
                self.is_done()

            if not self.done():
                self.set_result(self._response)
        except asyncio.CancelledError:
            if not self.done():
                self.cancel()
            raise
        except Exception as exc:
            if not self.done():
                self.set_exception(exc)

    def is_done(self) -> None:
        iris = _iris.get_iris()
        response = iris.ref()
        status = self._iris_handle.dispatchIsRequestDone(
            self.timeout,
            self._end_time,
            self._queue_name,
            self._message_header_id,
            response,
        )

        if status == 2:  # message found
            self._response = dispatch_deserializer(response.value)
            self._done = True
        elif status == 1:  # message not found
            pass
        else:
            self._done = True
            self.set_exception(
                RuntimeError(iris.system.Status.GetOneStatusText(status))
            )
