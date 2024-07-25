from iop import BusinessProcess
from msg import MyMessage


class MyMultiBP(BusinessProcess):

    def on_message(self, request):
        msg_one = MyMessage(message="Message1")
        msg_two = MyMessage(message="Message2")

        tuple_responses = self.send_multi_request_sync([("Python.MyMultiBO", msg_one),
                                                        ("Python.MyMultiBO", msg_two)])

        self.log_info("All requests have been processed")
        for target,request,response,status in tuple_responses:
            self.log_info(f"Received response: {response.message}")



