import importlib
from iop._business_host import _BusinessHost

class _PrivateSessionDuplex(_BusinessHost):
    
    Adapter = adapter = None
    _wait_for_next_call_interval = False
    DISPATCH = []

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
        pass

    @_BusinessHost.input_deserialzer
    @_BusinessHost.output_serialzer
    def _dispatch_on_message(self, request):
        """ For internal use only. """
        return self._dispach_message(request)

    def _set_iris_handles(self, handle_current, handle_partner):
        """ For internal use only. """
        self.iris_handle = handle_current
        if type(handle_partner).__module__.find('iris') == 0:
            if handle_partner._IsA("Grongier.PEX.InboundAdapter") or handle_partner._IsA("Grongier.PEX.OutboundAdapter"):
                module = importlib.import_module(handle_partner.GetModule())
                handle_partner = getattr(module, handle_partner.GetClassname())()
        self.Adapter = self.adapter = handle_partner
        return

    @_BusinessHost.input_deserialzer
    @_BusinessHost.output_serialzer
    def _dispatch_on_process_input(self, request):
        """ For internal use only. """
        return self.on_process_input(request)

    def on_process_input(self, message_input):
        """ Receives the message from the inbond adapter via the PRocessInput method and is responsible for forwarding it to target business processes or operations.
        If the business service does not specify an adapter, then the default adapter calls this method with no message 
        and the business service is responsible for receiving the data from the external system and validating it.

        Parameters:
        message_input: an instance of IRISObject or subclass of Message containing the data that the inbound adapter passes in.
            The message can have any structure agreed upon by the inbound adapter and the business service. 
        """
        return 

    @_BusinessHost.input_serialzer_param(0,'document')
    @_BusinessHost.output_deserialzer
    def send_document_to_process(self, document):
        """ Send the specified message to the target business process or business operation synchronously.
            
        Parameters:
        target: a string that specifies the name of the business process or operation to receive the request. 
            The target is the name of the component as specified in the Item Name property in the production definition, not the class name of the component.
        request: specifies the message to send to the target. The request is either an instance of a class that is a subclass of Message class or of IRISObject class.
            If the target is a build-in ObjectScript component, you should use the IRISObject class. The IRISObject class enables the PEX framework to convert the message to a class supported by the target.
        timeout: an optional integer that specifies the number of seconds to wait before treating the send request as a failure. The default value is -1, which means wait forever.
        description: an optional string parameter that sets a description property in the message header. The default is None.
        Returns:
            the response object from target.
        Raises:
        TypeError: if request is not of type Message or IRISObject.
        """

        return self.iris_handle.dispatchSendDocumentToProcess(document)

    @_BusinessHost.input_deserialzer
    @_BusinessHost.output_serialzer
    def _dispatch_on_private_session_started(self, source_config_name,self_generated):
        """ For internal use only. """

        return_object = self.on_private_session_started(source_config_name,self_generated)

        return return_object

    def on_private_session_started(self,source_config_name,self_generated):
        pass

    @_BusinessHost.input_deserialzer
    @_BusinessHost.output_serialzer
    def _dispatch_on_private_session_stopped(self, source_config_name,self_generated,message):
        """ For internal use only. """

        return_object = self.on_private_session_stopped(source_config_name,self_generated,message)

        return return_object

    def on_private_session_stopped(self,source_config_name,self_generated,message):
        pass