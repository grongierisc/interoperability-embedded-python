from grongier.pex import PrivateSessionDuplex
import iris

class Duplex(PrivateSessionDuplex):
    
    def get_adapter_type():
        """
        Name of the registred Adapter
        """
        return "EnsLib.TCP.DuplexAdapter"

    def on_process_input(self,input):
        self.send_document_to_process(iris.cls('Ens.Request')._New())

    def on_private_session_started(self,source_config_name,self_generated):
        self.log_info('In on_private_session_started')
        return

    def on_private_session_stopped(self,source_config_name,self_generated,message):
        self.log_info('In on_private_session_stopped')
        return