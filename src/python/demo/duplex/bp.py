from grongier.pex import PrivateSessionProcess

class Process(PrivateSessionProcess):

    def on_document(self,request):
        self.log_info('In on_document')
        return

    def on_private_session_started(self,source_config_name,self_generated):
        self.log_info('In on_private_session_started')
        return

    def on_private_session_stopped(self,source_config_name,self_generated,message):
        self.log_info('In on_private_session_started')
        return
