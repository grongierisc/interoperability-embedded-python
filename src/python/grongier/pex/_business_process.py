from grongier.pex._business_host import _BusinessHost

class _BusinessProcess(_BusinessHost):
    """ Typically contains most of the logic in a production.
    A business process can receive messages from a business service, another business process, or a business operation.
    It can modify the message, convert it to a different format, or route it based on the message contents.
    The business process can route a message to a business operation or another business process.
    """

    DISPATCH = []

    PERSISTENT_PROPERTY_LIST=None
    """ A list of the variable names of persistent properties."""        

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
        return self.on_request(request)

    def on_request(self, request):
        """ Handles requests sent to the business process. A production calls this method whenever an initial request 
        for a specific business process arrives on the appropriate queue and is assigned a job in which to execute.
        Parameters:
        request: An instance of IRISObject or subclass of Message that contains the request message sent to the business process.
        
        Returns:
        An instance of IRISObject or subclass of Message that contains the response message that this business process can return
            to the production component that sent the initial message.
        """
        return self.OnRequest(request)

    def on_response(self, request, response, callRequest, callResponse, completionKey):
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
        return self.OnResponse(request, response, callRequest, callResponse, completionKey)

    def on_complete(self, request, response):
        """ Called after the business process has received and handled all responses to requests it has sent to targets.
        Parameters: 
        request: An instance of IRISObject or subclass of Message that contains the initial request message sent to the business process.
        response: An instance of IRISObject or subclass of Message that contains the response message that this business process can return
            to the production component that sent the initial message.
        Returns:
        An instance of IRISObject or subclass of Message that contains the response message that this business process can return
            to the production component that sent the initial message.
        """
        return self.OnComplete(request, response)

    @_BusinessHost.input_serialzer
    def reply(self, response):
        """ Send the specified response to the production component that sent the initial request to the business process.

        Parameters:
        response: An instance of IRISObject or subclass of Message that contains the response message.
        """

        return self.iris_handle.dispatchReply(response)

    def set_timer(self, timeout, completionKey=None):
        """ Specifies the maximum time the business process will wait for responses.

        Parameters:
        timeout: an integer that specifies a number of seconds, or a string that specifies a time period such as"PT15s", 
            which represents 15 seconds of processor time.
        completionKey: a string that will be returned with the response if the maximum time is exceeded.
        """
        self.iris_handle.dispatchSetTimer(timeout, completionKey)
        return

    def _set_iris_handles(self, handle_current, handle_partner):
        """ For internal use only. """
        self.iris_handle = handle_current
        return

    def _save_persistent_properties(self, host_object):
        """ For internal use only. """
        if self.PERSISTENT_PROPERTY_LIST == None:
            return
        for prop in self.PERSISTENT_PROPERTY_LIST:
            val = getattr(self, prop, None)
            typ = val.__class__.__name__
            if (typ in ["str","int","float","bool","bytes"]):
                try:
                    host_object.setPersistentProperty(prop, val)
                except:
                    pass
        return

    def _restore_persistent_properties(self, host_object):
        """ For internal use only. """
        if self.PERSISTENT_PROPERTY_LIST == None:
            return
        for prop in self.PERSISTENT_PROPERTY_LIST:
            try:
                val = host_object.getPersistentProperty(prop)
                setattr(self, prop, val)
            except:
                pass
        return

    def _dispatch_on_connected(self, host_object):
        """ For internal use only. """
        self.on_connected()
        self._save_persistent_properties(host_object)
        return

    def _dispatch_on_init(self, host_object):
        """ For internal use only. """
        self._restore_persistent_properties(host_object)
        self._create_dispatch()
        self.on_init()
        self._save_persistent_properties(host_object)
        return

    def _dispatch_on_tear_down(self, host_object):
        """ For internal use only. """
        self._restore_persistent_properties(host_object)
        self.on_tear_down()
        self._save_persistent_properties(host_object)
        return

    @_BusinessHost.input_deserialzer
    @_BusinessHost.output_serialzer
    def _dispatch_on_request(self, host_object, request):
        """ For internal use only. """
        self._restore_persistent_properties(host_object)
        return_object = self._dispach_message(request)
        self._save_persistent_properties(host_object)
        return return_object
    
    @_BusinessHost.input_deserialzer
    @_BusinessHost.output_serialzer
    def _dispatch_on_response(self, host_object, request, response, callRequest, callResponse, completionKey):
        """ For internal use only. """
        self._restore_persistent_properties(host_object)
        return_object = self.on_response(request, response, callRequest, callResponse, completionKey)
        self._save_persistent_properties(host_object)
        return return_object

    @_BusinessHost.input_deserialzer
    @_BusinessHost.output_serialzer
    def _dispatch_on_complete(self, host_object, request, response):
        """ For internal use only. """
        self._restore_persistent_properties(host_object)
        return_object = self.on_complete(request, response)
        self._save_persistent_properties(host_object)
        return return_object

    def OnRequest(self, request):
        """ 
        DEPRECATED : use on_request
        Handles requests sent to the business process. A production calls this method whenever an initial request 
        for a specific business process arrives on the appropriate queue and is assigned a job in which to execute.
        Parameters:
        request: An instance of IRISObject or subclass of Message that contains the request message sent to the business process.
        
        Returns:
        An instance of IRISObject or subclass of Message that contains the response message that this business process can return
            to the production component that sent the initial message.
        """
        return 

    def OnResponse(self, request, response, callRequest, callResponse, completionKey):
        """ 
        DEPRECATED : use on_response
        Handles responses sent to the business process in response to messages that it sent to the target.
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
        return response

    def OnComplete(self, request, response):
        """ 
        DEPRECATED : use on_complete
        Called after the business process has received and handled all responses to requests it has sent to targets.
        Parameters: 
        request: An instance of IRISObject or subclass of Message that contains the initial request message sent to the business process.
        response: An instance of IRISObject or subclass of Message that contains the response message that this business process can return
            to the production component that sent the initial message.
        Returns:
        An instance of IRISObject or subclass of Message that contains the response message that this business process can return
            to the production component that sent the initial message.
        """
        return response