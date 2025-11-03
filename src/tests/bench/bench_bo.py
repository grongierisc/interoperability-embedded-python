from iop import BusinessOperation
import time

class BenchIoPOperation(BusinessOperation):

    my_param = "BenchIoPOperation"

    def on_message(self, request):
        time.sleep(0.001)  # Simulate some processing delay
        return request

if __name__ == "__main__":
    # This block is for testing the operation directly
    operation = BenchIoPOperation()
    test_request = {"data": "test"}
    response = operation.on_message(test_request)
    print("Response:", response)