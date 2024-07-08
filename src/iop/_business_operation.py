import importlib
from iop._business_host import _BusinessHost

class _BusinessOperation(_BusinessHost):
    """ This class corresponds to the PEX framework EnsLib.PEX.BusinessOperation class.
    The EnsLib.PEX.BusinessOperation RemoteClassName property identifies the Python class with the business operation implementation.
    The business operation can optionally use an adapter to handle the outgoing message. Specify the adapter in the OutboundAdapter property.
    If the business operation has an adapter, it uses the adapter to send the message to the external system.
    The adapter can either be a PEX adapter or an ObjectScript adapter.
    """

    DISPATCH = []
    Adapter = adapter = None

    def on_message(self, request):
        """ Called when the business operation receives a message from another production component.
        Typically, the operation will either send the message to the external system or forward it to a business process or another business operation.
        If the operation has an adapter, it uses the Adapter.invoke() method to call the method on the adapter that sends the message to the external system.
        If the operation is forwarding the message to another production component, it uses the SendRequestAsync() or the SendRequestSync() method

        Parameters:
        request: An instance of either a subclass of Message or of IRISObject containing the incoming message for the business operation.

        Returns:
        The response object
        """
        return self.OnMessage(request)

    def on_keepalive(self):
        """
        > This function is called when the server sends a keepalive message
        """
        return

    def _set_iris_handles(self, handle_current, handle_partner):
        """ For internal use only. """
        self.iris_handle = handle_current
        if type(handle_partner).__module__.find('iris') == 0:
            if handle_partner._IsA("Grongier.PEX.OutboundAdapter"):
                module = importlib.import_module(handle_partner.GetModule())
                handle_partner = getattr(module, handle_partner.GetClassname())()
            self.Adapter = self.adapter = handle_partner
        return

    def _dispatch_on_init(self, host_object):
        """ For internal use only. """
        self._create_dispatch()
        self.on_init()
        return

    @_BusinessHost.input_deserialzer
    @_BusinessHost.output_serialzer
    def _dispatch_on_message(self, request):
        """ For internal use only. """
        return self._dispach_message(request)

    def OnMessage(self, request):
        """ DEPRECATED : use on_message
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
