from grongier.pex import DuplexService
import iris

class Service(DuplexService):

    _wait_for_next_call_interval = True

    def on_init(self):
        self._wait_for_next_call_interval = True
        return
    
    def get_adapter_type():
        """
        Name of the registred Adapter
        """
        return "Ens.InboundAdapter"

    def on_process_input(self,input):
        self.send_document_to_process(iris.cls('Ens.Request')._New())

    def on_private_session_started(self,source_config_name,self_generated):
        self.log_info('In on_private_session_started')
        return

    def on_private_session_stopped(self,source_config_name,self_generated,message):
        self.log_info('In on_private_session_stopped')
        return

if __name__ == '__main__':
    d = Service()
    print('hello')
    print(d._get_info())
    print('hello')