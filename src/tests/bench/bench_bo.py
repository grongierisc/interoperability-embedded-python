from iop import BusinessOperation

class BenchIoPOperation(BusinessOperation):

    def on_init(self):
        self.log_info("BenchIoPOperation initialized")

    def on_message(self, request):

        return request
