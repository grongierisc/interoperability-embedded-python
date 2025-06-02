from iop import BusinessOperation

class BenchIoPOperation(BusinessOperation):

    my_param = "BenchIoPOperation"

    def on_message(self, request):
        self.log_info("BenchIoPOperation received message")
        # raise NotImplementedError("BenchIoPOperation is not implemented yet")
        return request
