from iop import BusinessProcess
from iop import target as iop_target


class BenchIoPProcess(BusinessProcess):
    target = iop_target()

    def on_init(self):
        if not hasattr(self, 'size'):
            self.size = 100
        if not hasattr(self, 'target'):
            self.target = 'Python.BenchIoPOperation'

    def on_message(self, request):
        for _ in range(self.size):
            self.send_request_sync(self.target, request)
