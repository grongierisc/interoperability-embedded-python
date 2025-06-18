from iop import BusinessOperation
import time

class BenchIoPOperation(BusinessOperation):

    my_param = "BenchIoPOperation"

    def on_message(self, request):
        time.sleep(0.001)  # Simulate some processing delay
        return request
