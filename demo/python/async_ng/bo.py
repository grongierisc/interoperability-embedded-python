from iop import BusinessOperation
from msg import MyMessage

import time
import random

class MyAsyncNGBO(BusinessOperation):
    def on_message(self, request):
        print(f"Received message: {request.message}")
        rand = random.randint(1, 10)
        time.sleep(rand)
        return MyMessage(message=f"Hello, {request.message} after {rand} seconds")

        