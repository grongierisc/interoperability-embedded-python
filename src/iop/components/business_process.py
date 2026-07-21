from typing import Any

from ..messages.decorators import (
    input_deserializer,
    input_serializer_param,
    output_serializer,
)
from ..messages.dispatch import create_dispatch, dispatch_message
from ..production import TargetSettingRef, resolve_target
from .business_host import _BusinessHost


class _BusinessProcess(_BusinessHost):
    """Business process component that contains routing and transformation logic.

    A business process can receive messages from services, other processes, or operations.
    It can modify messages, transform formats, and route based on content.
    """

    DISPATCH: list[tuple] = []
    PERSISTENT_PROPERTY_LIST: list[str] | None = None

    def on_message(self, request: Any) -> Any:
        """Purpose:
            Handle an incoming message sent to a BusinessProcess.

        Use when:
            The process owns routing, orchestration, transformation, or
            decisions for a request.

        Lifecycle:
            IRIS invokes this hook for process requests unless dispatch routes
            the message to a @handler or typed one-argument method first. The
            default implementation delegates to on_request(request).

        Best practices:
            Declare outbound routes with target() and call
            send_request_sync(...) or send_request_async(...).

        Common mistakes:
            Do not hide routing in raw strings when target() can make routes
            configurable in the production graph.

        Minimal example:
            def on_message(self, request):
                return self.send_request_sync(self.Output, request)

        Related:
            docs/cookbooks/add-business-process.md
        """
        return self.on_request(request)

    def on_request(self, request: Any) -> Any:
        """Process initial requests sent to this component.

        Args:
            request: The incoming request message

        Returns:
            Response message
        """
        return None

    def on_response(
        self,
        request: Any,
        response: Any,
        call_request: Any,
        call_response: Any,
        completion_key: str,
    ) -> Any:
        """Purpose:
            Handle one async response received by a BusinessProcess.

        Use when:
            The process sends async requests and needs to merge, inspect, or
            transform each returned response.

        Lifecycle:
            IRIS calls on_response(...) after an async target response arrives.
            on_complete(...) can run after all expected responses complete.

        Best practices:
            Use completion_key to identify which async call returned. Return
            the accumulated or transformed response state.

        Common mistakes:
            Do not assume responses arrive in request order.

        Minimal example:
            def on_response(self, request, response, call_request, call_response, completion_key):
                return call_response

        Related:
            docs/cookbooks/add-business-process.md
        """
        return response

    def on_complete(self, request: Any, response: Any) -> Any:
        """Purpose:
            Finish async request orchestration for a BusinessProcess.

        Use when:
            The process must return or finalize an aggregate response after
            async sends, timers, or response handling.

        Lifecycle:
            IRIS calls on_complete(request, response) after expected async
            responses have been handled or the completion path is reached.

        Best practices:
            Return the final response message expected by the original caller.

        Common mistakes:
            Do not put per-response logic here; use on_response(...) for each
            individual async response.

        Minimal example:
            def on_complete(self, request, response):
                return response

        Related:
            docs/cookbooks/add-business-process.md
        """
        return response

    @input_serializer_param(0, "response")
    def reply(self, response: Any) -> None:
        """Send the specified response to the production component that sent the initial request.

        Args:
            response: The response message
        """
        return self.iris_handle.dispatchReply(response)

    @input_serializer_param(1, "request")
    def send_request_async(
        self,
        target: str | TargetSettingRef,
        request: Any,
        description: str | None = None,
        completion_key: str | None = None,
        response_required: bool = True,
    ) -> None:
        """Purpose:
            Send a message asynchronously from a BusinessProcess.

        Use when:
            The process should continue without blocking for a target response,
            or when responses will be handled later by on_response(...).

        Lifecycle:
            IoP serializes request before dispatching to IRIS. IRIS can call
            on_response(...) and on_complete(...) when response_required is true.

        Best practices:
            Pass a target() attribute such as self.Output. Use completion_key
            for fan-out or multiple async calls.

        Common mistakes:
            Do not pass an unresolved component instance or a hard-coded route
            when the route should be configurable.

        Minimal example:
            self.send_request_async(self.Output, request, completion_key="out")

        Related:
            docs/cookbooks/add-business-process.md,
            docs/cookbooks/production-settings-and-targets.md
        """
        # Convert boolean to int for Iris API
        if response_required:
            response_required = 1  # type: ignore
        else:
            response_required = 0  # type: ignore
        target = resolve_target(target)
        if description is None:
            description = f"{self.__class__.__name__} -> {target}"
        return self.iris_handle.dispatchSendRequestAsync(
            target, request, response_required, completion_key, description
        )

    def set_timer(
        self, timeout: int | str, completion_key: str | None = None
    ) -> None:
        """Specify the maximum time the business process will wait for responses.

        Args:
            timeout: The maximum time to wait for responses
            completion_key: A string that will be returned with the response if the maximum time is exceeded
        """
        self.iris_handle.dispatchSetTimer(timeout, completion_key)
        return

    def _set_iris_handles(self, handle_current: Any, handle_partner: Any) -> None:
        """For internal use only."""
        self.iris_handle = handle_current
        return

    def _save_persistent_properties(self, host_object: Any) -> None:
        """For internal use only."""
        if self.PERSISTENT_PROPERTY_LIST is None:
            return
        for prop in self.PERSISTENT_PROPERTY_LIST:
            val = getattr(self, prop, None)
            typ = val.__class__.__name__
            if typ in ["str", "int", "float", "bool", "bytes"]:
                try:
                    host_object.setPersistentProperty(prop, val)
                except Exception:
                    pass
        return

    def _restore_persistent_properties(self, host_object: Any) -> None:
        """For internal use only."""
        if self.PERSISTENT_PROPERTY_LIST is None:
            return
        for prop in self.PERSISTENT_PROPERTY_LIST:
            try:
                val = host_object.getPersistentProperty(prop)
                setattr(self, prop, val)
            except Exception:
                pass
        return

    def _dispatch_on_connected(self, host_object: Any) -> None:
        """For internal use only."""
        self.on_connected()
        self._save_persistent_properties(host_object)
        return

    def _dispatch_on_init(self, host_object: Any) -> None:
        """For internal use only."""
        self._log_custom_init_warning()
        self._restore_persistent_properties(host_object)
        create_dispatch(self)
        self.on_init()
        self._save_persistent_properties(host_object)
        return

    def _dispatch_on_tear_down(self, host_object: Any) -> None:
        """For internal use only."""
        self._restore_persistent_properties(host_object)
        self.on_tear_down()
        self._save_persistent_properties(host_object)
        return

    @input_deserializer
    @output_serializer
    def _dispatch_on_request(self, host_object: Any, request: Any) -> Any:
        """For internal use only."""
        self._restore_persistent_properties(host_object)
        return_object = dispatch_message(self, request)
        self._save_persistent_properties(host_object)
        return return_object

    @input_deserializer
    @output_serializer
    def _dispatch_on_response(
        self,
        host_object: Any,
        request: Any,
        response: Any,
        call_request: Any,
        call_response: Any,
        completion_key: str,
    ) -> Any:
        """For internal use only."""
        self._restore_persistent_properties(host_object)
        return_object = self.on_response(
            request, response, call_request, call_response, completion_key
        )
        self._save_persistent_properties(host_object)
        return return_object

    @input_deserializer
    @output_serializer
    def _dispatch_on_complete(
        self, host_object: Any, request: Any, response: Any
    ) -> Any:
        """For internal use only."""
        self._restore_persistent_properties(host_object)
        return_object = self.on_complete(request, response)
        self._save_persistent_properties(host_object)
        return return_object

