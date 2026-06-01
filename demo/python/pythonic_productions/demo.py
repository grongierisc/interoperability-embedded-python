from dataclasses import dataclass

from iop import BusinessOperation, PollingBusinessService, Message, Production, target


@dataclass
class OrderRequest(Message):
    order_id: str = ""


class FileService(PollingBusinessService):
    Output = target("orders")

    def on_process_input(self, message_input):
        self.send_request_sync(self.Output, OrderRequest(order_id="777"))


class OrderOperation(BusinessOperation):
    def on_message(self, message_input):
        print(f"Received order request: {message_input}")
        return message_input


prod = Production("Demo.Production", testing_enabled=True)
file = prod.service("FileInput", FileService)
orders = prod.operation(OrderOperation)  # auto item name: OrderOperation

prod.connect(file.Output, orders)

prod.graph()

PRODUCTIONS = [prod]

