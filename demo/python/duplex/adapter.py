from iop import InboundAdapter

class OperationAdapter(InboundAdapter):

    def on_task(self):
        self.log_info('on_task')
        if self.business_host_python is not None:
            self.business_host_python.on_process_input(None)
        else:
            self.business_host.ProcessInput()
