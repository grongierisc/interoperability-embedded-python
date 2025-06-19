from typing import Any
from iop import BusinessProcess

from msg import MyGenerator 

class MyGeneratorProcess(BusinessProcess):

    def on_request(self, request: Any) -> Any:
        gen = self.send_generator_request(
            target="User.MyGeneratorOperation",
            request=MyGenerator(my_string="Hello, World!"),
            timeout=10,
            description="My generator request")
        
        for response in gen:
            self.log_info(f"Received response: {response}")