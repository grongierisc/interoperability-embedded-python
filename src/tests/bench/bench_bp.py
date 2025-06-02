from iop import BusinessProcess

class BenchIoPProcess(BusinessProcess):
    def on_init(self):
        if not hasattr(self, 'size'):
            self.size = 100
        if not hasattr(self, 'target'):
            self.target = 'Python.BenchIoPOperation'

    def on_message(self, request):
        for _ in range(self.size):
            _ = self.send_request_sync(self.target,request)