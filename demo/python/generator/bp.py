from typing import Any
from iop import BusinessProcess
import iris

from msg import MyGenerator, MyOtherGeneratorCall

class MyGeneratorProcess(BusinessProcess):

    def on_ens_request(self, request: iris.Ens.Request):
        gen = self.send_generator_request(
            target="User.MyGeneratorOperation",
            request=MyGenerator(my_string="Hello, World!"),
            timeout=10,
            description="My generator request")
        
        for response in gen:
            self.log_info(f"Received response: {response}")

    def on_string_request(self, request: 'iris.Ens.StringRequest'):
        gen = self.send_generator_request(
            target="User.MyGeneratorOperation",
            request=MyOtherGeneratorCall(StringValue=request.StringValue)
        )
        for response in gen:
            self.log_info(f"Received response: {response}")