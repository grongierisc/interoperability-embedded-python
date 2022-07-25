from grongier.pex import DuplexOperation
import iris

class Operation(DuplexOperation):
    
    def get_adapter_type():
        """
        Name of the registred Adapter
        """
        return "Duplex.adapter.OperationAdapter"

    def on_process_input(self,input):
        self.send_document_to_process(iris.cls('Ens.Request')._New())

    def on_message(self,input):
        self.log_info('On message')

    def on_private_session_started(self,source_config_name,self_generated):
        self.log_info('In on_private_session_started')
        return

    def on_private_session_stopped(self,source_config_name,self_generated,message):
        self.log_info('In on_private_session_stopped')
        return

if __name__ == '__main__':
    d = Operation()
    print('hello')
    print(d._get_info())
    print('hello')