from grongier.pex import BusinessOperation
from msg import MyMessage

import time

class MyBO(BusinessOperation):
    def on_message(self, request):
        print(f"Received message: {request.message}")
        time.sleep(1)
        return MyMessage(message=f"Hello, {request.message}")

        