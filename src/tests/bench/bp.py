from iop import BusinessProcess

class BenchIoPProcess(BusinessProcess):
    def on_init(self):
        if not hasattr(self, 'size'):
            self.size = 100

    def on_message(self, request):
        for _ in range(self.size):
            _ = self.send_request_sync("Python.BenchIoPOperation",request)