import importlib
from typing import Any, List, Optional, Union, Tuple

from ._business_host import _BusinessHost
from ._decorators import input_deserializer, output_serializer, input_serializer, output_deserializer
from ._dispatch import create_dispatch, dispach_message

class _BusinessOperation(_BusinessHost):
    """Business operation component that handles outbound communication.
    
    Responsible for sending messages to external systems. Can optionally use an 
    adapter to handle the outbound messaging protocol.
    """

    DISPATCH: List[Tuple[str, str]] = []
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
        return self.OnMessage(request)

    def on_keepalive(self) -> None:
        """
        Called when the server sends a keepalive message.
        """
        return

    def _set_iris_handles(self, handle_current: Any, handle_partner: Any) -> None:
        """For internal use only."""
        self.iris_handle = handle_current
        if type(handle_partner).__module__.find('iris') == 0:
            if handle_partner._IsA("Grongier.PEX.OutboundAdapter") or handle_partner._IsA("IOP.OutboundAdapter"):
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
        return dispach_message(self,request)

    def OnMessage(self, request: Any) -> Any:
        """DEPRECATED : use on_message
        Called when the business operation receives a message from another production component.
        Typically, the operation will either send the message to the external system or forward it to a business process or another business operation.
        If the operation has an adapter, it uses the Adapter.invoke() method to call the method on the adapter that sends the message to the external system.
        If the operation is forwarding the message to another production component, it uses the SendRequestAsync() or the SendRequestSync() method

        Parameters:
        request: An instance of either a subclass of Message or of IRISObject containing the incoming message for the business operation.

        Returns:
        The response object
        """
        return
    
