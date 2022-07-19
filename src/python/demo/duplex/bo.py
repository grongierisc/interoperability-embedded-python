from grongier.pex import PrivateSessionDuplex

class Duplex(PrivateSessionDuplex):
    

    def on_private_session_started(self,source_config_name,self_generated):
        self.log_info('In on_private_session_started')
        return

    def on_private_session_stopped(self,source_config_name,self_generated,message):
        self.log_info('In on_private_session_stopped')
        return