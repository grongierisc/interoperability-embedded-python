from grongier.pex._business_host import _BusinessHost

class _PrivateSesssionDuplex(_BusinessHost):
    
    @_BusinessHost.input_serialzer
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
    def _dispatch_on_private_session_started(self, host_object, source_config_name,self_generated):
        """ For internal use only. """
        self._restore_persistent_properties(host_object)
        return_object = self.on_private_session_started(source_config_name,self_generated)
        self._save_persistent_properties(host_object)
        return return_object

    def on_private_session_started(self,source_config_name,self_generated):
        pass

    @_BusinessHost.input_deserialzer
    @_BusinessHost.output_serialzer
    def _dispatch_on_private_session_stopped(self, host_object, source_config_name,self_generated,message):
        """ For internal use only. """
        self._restore_persistent_properties(host_object)
        return_object = self.on_private_session_stopped(source_config_name,self_generated,message)
        self._save_persistent_properties(host_object)
        return return_object

    def on_private_session_stopped(self,source_config_name,self_generated,message):
        pass