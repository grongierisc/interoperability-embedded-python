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
        """Handle incoming messages.

        Process messages received from other production components and either
        send to external system or forward to another component.

        Args:
            request: The incoming message

        Returns:
            Response message
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
        create_dispatch(self)
        self.on_init()
        return

    @input_deserializer
    @output_serializer
    def _dispatch_on_message(self, request: Any) -> Any:
        """For internal use only."""
        return dispatch_message(self, request)
