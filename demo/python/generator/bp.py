from typing import Any
from iop import BusinessProcess

from msg import MyGenerator, MyGeneratorResponse 

class MyGeneratorProcess(BusinessProcess):

    def on_request(self, request: Any) -> Any:
        rsp = self.send_request_sync(
            target="User.MyGeneratorOperation",
            request=MyGeneratorResponse(my_other_string="Hello, World!"),
            timeout=10,
            description="My generator request")
        gen = self.send_generator_request(
            target="User.MyGeneratorOperation",
            request=MyGenerator(my_string="Hello, World!"),
            timeout=10,
            description="My generator request")
        for response in gen:
            self.log_info(f"Received response: {response}")