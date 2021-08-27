import iris
from pex._BusinessHost import _BusinessHost

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

    @staticmethod
    def useAdapterConnection():
        """ The useAdapterConnection() method is called when registering the business operation in order to instruct the business operation on whether to use the
        the connection information from its adapter.
        Do not return true if this is an adapterless business operation or if the adapter is in a different language.
        """
        return False

    def _setIrisHandles(self, handleCurrent, handlePartner):
        """ For internal use only. """
        self.irisHandle = handleCurrent
        self.Adapter = iris.pex.IRISOutboundAdapter()
        self.Adapter.irisHandle = handlePartner
        return

    def SendRequestAsync(self, target, request, description=None):
        """ Send the specified message to the target business process or business operation asynchronously.

        Parameters:
        target: a string that specifies the name of the business process or operation to receive the request. 
            The target is the name of the component as specified in the Item Name property in the production definition, not the class name of the component.
        request: specifies the message to send to the target. The request is an instance of IRISObject or of a subclass of Message.
            If the target is a built-in ObjectScript component, you should use the IRISObject class. The IRISObject class enables the PEX framework to convert the message to a class supported by the target.
        description: an optional string parameter that sets a description property in the message header. The default is None.
        
        Raises:
        TypeError: if request is not of type Message or IRISObject.
        """
        if self._is_message_instance(request):
            serialized = self._serialize(request)
            self.irisHandle.dispatchSendRequestAsync(target,serialized,description)
        elif isinstance(request, iris.IRISObject):
            self.irisHandle.dispatchSendRequestAsync(target,request,description)
        else:
            raise TypeError
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
    