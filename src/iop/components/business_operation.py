import importlib
import warnings
from typing import Any

from ..messages.decorators import input_deserializer, output_serializer
from ..messages.dispatch import create_dispatch, dispatch_message
from .business_host import _BusinessHost


class _BusinessOperation(_BusinessHost):
    """Business operation component that handles outbound communication.

    Responsible for sending messages to external systems. Can optionally use an
    adapter to handle the outbound messaging protocol.
    """

    DISPATCH: list[tuple[str, str]] = []
    Adapter: Any = None
    adapter: Any = None

    def on_message(self, request: Any) -> Any:
        """Purpose:
            Handle an incoming message sent to a BusinessOperation.

        Use when:
            The operation must perform an outbound side effect or submit data to
            an external system.

        Lifecycle:
            IRIS invokes this hook for operation requests unless dispatch routes
            the message to a @handler or typed one-argument method first.

        Best practices:
            Keep side effects isolated here. Return a response message when the
            caller uses send_request_sync(...).

        Common mistakes:
            Do not put routing decisions here when a BusinessProcess should
            orchestrate them.

        Minimal example:
            def on_message(self, request):
                return SubmitResult(ok=True)

        Related:
            docs/cookbooks/add-business-operation.md
        """
        warnings.warn(
            f"{self.__class__.__name__} did not override on_message(); "
            "the incoming operation message was ignored. "
            "This default no-op handler will raise NotImplementedError in v5.0.",
            RuntimeWarning,
            stacklevel=2,
        )
        return None

    def on_keepalive(self) -> None:
        """
        Called when the server sends a keepalive message.
        """
        return

    def _set_iris_handles(self, handle_current: Any, handle_partner: Any) -> None:
        """For internal use only."""
        self.iris_handle = handle_current
        if type(handle_partner).__module__.find("iris") == 0:
            if handle_partner._IsA("IOP.OutboundAdapter"):
                module = importlib.import_module(handle_partner.GetModule())
                handle_partner = getattr(module, handle_partner.GetClassname())()
            self.Adapter = self.adapter = handle_partner
        return

    def _dispatch_on_init(self, host_object: Any) -> None:
        """For internal use only."""
        self._log_custom_init_warning()
        create_dispatch(self)
        self.on_init()
        return

    @input_deserializer
    @output_serializer
    def _dispatch_on_message(self, request: Any) -> Any:
        """For internal use only."""
        return dispatch_message(self, request)
