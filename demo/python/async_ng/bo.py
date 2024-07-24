from iop import BusinessOperation
from msg import MyMessage

import time

class MyAsyncNGBO(BusinessOperation):
    def on_message(self, request):
        print(f"Received message: {request.message}")
        time.sleep(1)
        return MyMessage(message=f"Hello, {request.message}")

        