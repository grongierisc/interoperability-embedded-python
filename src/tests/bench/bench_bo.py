from iop import BusinessOperation

class BenchIoPOperation(BusinessOperation):

    def on_message(self, request):
        self.log_info("BenchIoPOperation received message")
        return request
