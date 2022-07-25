from grongier.pex import InboundAdapter

class OperationAdapter(InboundAdapter):

    def on_task(self):
        self.log_info('on_task')
        self.business_host.OnProcessInput()