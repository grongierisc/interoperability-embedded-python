from grongier.pex import BusinessProcess
from msg import MyMessage


class MyBP(BusinessProcess):

    def on_message(self, request):
        msg_one = MyMessage(message="Message1")
        msg_two = MyMessage(message="Message2")

        self.send_request_async("Python.MyBO", msg_one,completion_key="1")
        self.send_request_async("Python.MyBO", msg_two,completion_key="2")
        self.send_request_async("Python.MyBO", msg_two,completion_key="3", response_required=False)

    def on_response(self, request, response, call_request, call_response, completion_key):
        if completion_key == "1":
            self.response_one = call_response
        elif completion_key == "2":
            self.response_two = call_response

    def on_complete(self, request, response):
        self.log_info(f"Received response one: {self.response_one.message}")
        self.log_info(f"Received response two: {self.response_two.message}")


