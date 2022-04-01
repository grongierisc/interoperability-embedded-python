import iris
import grongier.pex
import importlib
from grongier.pex._BusinessHost import _BusinessHost

class _BusinessOperation(_BusinessHost):
    """ This class corresponds to the PEX framework EnsLib.PEX.BusinessOperation class.
    The EnsLib.PEX.BusinessOperation RemoteClassName property identifies the Python class with the business operation implementation.
    The business operation can optionally use an adapter to handle the outgoing message. Specify the adapter in the OutboundAdapter property.
    If the business operation has an adapter, it uses the adapter to send the message to the external system.
    The adapter can either be a PEX adapter or an ObjectScript adapter.
    """

    def __init__(self):
        """ The adapter variable provides access to the outbound adapter associated with the business operation."""
        super().__init__()
        self.Adapter = None
    
    def OnConnected(self):
        """ The OnConnected() method is called when the component is connected or reconnected after being disconnected.
        Use the OnConnected() method to initialize any structures needed by the component."""
        pass

    def OnInit(self):
        """ The OnInit() method is called when the component is started.
        Use the OnInit() method to initialize any structures needed by the component."""
        pass

    def OnTearDown(self):
        """ Called before the component is terminated. Use it to freee any structures."""
        pass

    def OnMessage(self, request):
        """ Called when the business operation receives a message from another production component.
        Typically, the operation will either send the message to the external system or forward it to a business process or another business operation.
        If the operation has an adapter, it uses the Adapter.invoke() method to call the method on the adapter that sends the message to the external system.
        If the operation is forwarding the message to another production component, it uses the SendRequestAsync() or the SendRequestSync() method

        Parameters:
        request: An instance of either a subclass of Message or of IRISObject containing the incoming message for the business operation.

        Returns:
        The response object
        """
        pass

    @staticmethod
    def getAdapterType():
        """ The getAdapterType() method is called when registering the business operation in order to instruct the business operation on what outbout adapter to use.
        The return value from this method should be the string name of the outbound adapter class.  This may be an ObjectScript class or a PEX adapter class.
        Return the empty string for adapterless business operations.
        """
        return ""

    def _setIrisHandles(self, handleCurrent, handlePartner):
        """ For internal use only. """
        self.irisHandle = handleCurrent
        if type(handlePartner).__module__.find('iris') == 0:
            if handlePartner._IsA("Grongier.PEX.OutboundAdapter"):
                module = importlib.import_module(handlePartner.GetModule())
                handlePartner = getattr(module, handlePartner.GetClassname())()
            self.Adapter = handlePartner
        return

    def _dispatchOnConnected(self, hostObject):
        """ For internal use only. """
        self.OnConnected()
        return

    def _dispatchOnInit(self, hostObject):
        """ For internal use only. """
        self.OnInit()
        return

    def _dispatchOnTearDown(self, hostObject):
        """ For internal use only. """
        self.OnTearDown()
        return

    def _dispatchOnMessage(self, request):
        """ For internal use only. """
        if isinstance(request, str):
            request = self._deserialize(request)
        returnObject = self.OnMessage(request)
        if self._is_message_instance(returnObject):
            returnObject = self._serialize(returnObject)
        return returnObject
    