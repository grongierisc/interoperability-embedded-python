from iop._business_process import _BusinessProcess
from iop._business_host import _BusinessHost

class _PrivateSessionProcess(_BusinessProcess):
    
    @_BusinessHost.input_deserialzer
    @_BusinessHost.output_serialzer
    def _dispatch_on_document(self, host_object,source_config_name, request):
        """ For internal use only. """
        self._restore_persistent_properties(host_object)
        return_object = self.on_document(source_config_name,request)
        self._save_persistent_properties(host_object)
        return return_object

    def on_document(source_config_name,request):
        pass


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