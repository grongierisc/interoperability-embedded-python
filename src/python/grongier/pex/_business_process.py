from grongier.pex._business_host import _BusinessHost

class _BusinessProcess(_BusinessHost):
    """ Typically contains most of the logic in a production.
    A business process can receive messages from a business service, another business process, or a business operation.
    It can modify the message, convert it to a different format, or route it based on the message contents.
    The business process can route a message to a business operation or another business process.
    """

    PERSISTENT_PROPERTY_LIST=None
    """ A list of the variable names of persistent properties."""

    def __init__(self):
        super().__init__()
    
    def OnConnected(self):
        """ The OnConnected() method is called when the component is connected or reconnected after being disconnected.
        Use the OnConnected() method to initialize any structures needed by the component."""
        pass

    def OnInit(self):
        """ The OnInit() method is called when the component is started.
        Use the OnInit() method to initialize any structures needed by the component."""
        pass

    def OnTearDown(self):
        """ Called before the component is terminated."""
        pass

    def OnRequest(self, request):
        """ Handles requests sent to the business process. A production calls this method whenever an initial request 
        for a specific business process arrives on the appropriate queue and is assigned a job in which to execute.

        Parameters:
        request: An instance of IRISObject or subclass of Message that contains the request message sent to the business process.
        
        Returns:
        An instance of IRISObject or subclass of Message that contains the response message that this business process can return
            to the production component that sent the initial message.
        """
        pass

    def OnResponse(self, request, response, callRequest, callResponse, completionKey):
        """ Handles responses sent to the business process in response to messages that it sent to the target.
        A production calls this method whenever a response for a specific business process arrives on the appropriate queue and is assigned a job in which to execute.
        Typically this is a response to an asynchronous request made by the business process where the responseRequired parameter has a true value.

        Parameters:
        request: An instance of IRISObject or subclass of Message that contains the initial request message sent to the business process.
        response: An instance of IRISObject or subclass of Message that contains the response message that this business process can return
            to the production component that sent the initial message.
        callRequest: An instance of IRISObject or subclass of Message that contains the request that the business process sent to its target.
        callResponse: An instance of IRISObject or subclass of Message that contains the incoming response.
        completionKey: A string that contains the completionKey specified in the completionKey parameter of the outgoing SendAsync() method.

        Returns:
        An instance of IRISObject or subclass of Message that contains the response message that this business process can return
            to the production component that sent the initial message.
        """
        pass

    def OnComplete(self, request, response):
        """ Called after the business process has received and handled all responses to requests it has sent to targets.

        Parameters: 
        request: An instance of IRISObject or subclass of Message that contains the initial request message sent to the business process.
        response: An instance of IRISObject or subclass of Message that contains the response message that this business process can return
            to the production component that sent the initial message.

        Returns:
        An instance of IRISObject or subclass of Message that contains the response message that this business process can return
            to the production component that sent the initial message.
        """
        pass

    def _set_iris_handles(self, handleCurrent, handlePartner):
        """ For internal use only. """
        self.irisHandle = handleCurrent
        return

    def _savePersistentProperties(self, hostObject):
        """ For internal use only. """
        if self.PERSISTENT_PROPERTY_LIST == None:
            return
        for prop in self.PERSISTENT_PROPERTY_LIST:
            val = getattr(self, prop, None)
            typ = val.__class__.__name__
            if (typ in ["str","int","float","bool","bytes"]):
                try:
                    hostObject.setPersistentProperty(prop, val)
                except:
                    pass
        return

    def _restorePersistentProperties(self, hostObject):
        """ For internal use only. """
        if self.PERSISTENT_PROPERTY_LIST == None:
            return
        for prop in self.PERSISTENT_PROPERTY_LIST:
            try:
                val = hostObject.getPersistentProperty(prop)
                setattr(self, prop, val)
            except:
                pass
        return

    def _dispatch_on_connected(self, hostObject):
        """ For internal use only. """
        self.OnConnected()
        self._savePersistentProperties(hostObject)
        return

    def _dispatch_on_init(self, hostObject):
        """ For internal use only. """
        self._restorePersistentProperties(hostObject)
        self.OnInit()
        self._savePersistentProperties(hostObject)
        return

    def _dispatch_on_tear_down(self, hostObject):
        """ For internal use only. """
        self._restorePersistentProperties(hostObject)
        self.OnTearDown()
        self._savePersistentProperties(hostObject)
        return

    def _dispatch_on_request(self, hostObject, request):
        """ For internal use only. """
        self._restorePersistentProperties(hostObject)
        if isinstance(request, str):
            request = self._deserialize(request)
        returnObject = self.OnRequest(request)
        if self._is_message_instance(returnObject):
            returnObject = self._serialize(returnObject)
        self._savePersistentProperties(hostObject)
        return returnObject
    
    def _dispatch_on_response(self, hostObject, request, response, callRequest, callResponse, completionKey):
        """ For internal use only. """
        self._restorePersistentProperties(hostObject)
        if isinstance(request, str):
            request = self._deserialize(request)
        if isinstance(response, str):
            response = self._deserialize(response)
        if isinstance(callRequest, str):
            callRequest = self._deserialize(callRequest)
        if isinstance(callResponse, str):
            callResponse = self._deserialize(callResponse)
        returnObject = self.OnResponse(request, response, callRequest, callResponse, completionKey)
        if self._is_message_instance(returnObject):
            returnObject = self._serialize(returnObject)
        self._savePersistentProperties(hostObject)
        return returnObject

    def _dispatch_on_complete(self, hostObject, request, response):
        """ For internal use only. """
        self._restorePersistentProperties(hostObject)
        if isinstance(request, str):
            request = self._deserialize(request)
        if isinstance(response, str):
            response = self._deserialize(response)
        returnObject = self.OnComplete(request, response)
        if self._is_message_instance(returnObject):
            returnObject = self._serialize(returnObject)
        self._savePersistentProperties(hostObject)
        return returnObject

    def Reply(self, response):
        """ Send the specified response to the production component that sent the initial request to the business process.

        Parameters:
        response: An instance of IRISObject or subclass of Message that contains the response message.
        """
        if self._is_message_instance(response):
            response = self._serialize(response)
        self.irisHandle.dispatchReply(response)
        return

    def SetTimer(self, timeout, completionKey=None):
        """ Specifies the maximum time the business process will wait for responses.

        Parameters:
        timeout: an integer that specifies a number of seconds, or a string that specifies a time period such as"PT15s", 
            which represents 15 seconds of processor time.
        completionKey: a string that will be returned with the response if the maximum time is exceeded.
        """
        self.irisHandle.dispatchSetTimer(timeout, completionKey)
        return