from typing import Any
from iop import BusinessOperation

from msg import MyGeneratorResponse, MyGenerator  # Import the generator message class

class MyGeneratorOperation(BusinessOperation):

    def on_other_request(self, request: MyGeneratorResponse) -> Any:
        self.log_info("Received other request")
        return MyGeneratorResponse(my_other_string="Hello, World!")

    def on_private_session_started(self, request: MyGenerator) -> Any:
        self.log_info("Private session started")
        return self.my_generator(request)

    def my_generator(self, request: Any) -> Any:
        self.log_info(f"Processing request: {request}")
        # Simulate some processing and yield responses
        for i in range(5):
            response = f"Response {i} from MyGeneratorOperation"
            self.log_info(response)
            yield MyGeneratorResponse(my_other_string=response)

    