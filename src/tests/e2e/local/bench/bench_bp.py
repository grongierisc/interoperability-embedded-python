from iop import BusinessProcess, target as iop_target

class BenchIoPProcess(BusinessProcess):
    target = iop_target("operation")

    def on_init(self):
        if not hasattr(self, 'size'):
            self.size = 100
        if not hasattr(self, 'target'):
            self.target = 'Python.BenchIoPOperation'

    def on_message(self, request):
        for _ in range(self.size):
            rsp = self.send_request_sync(self.target,request)
