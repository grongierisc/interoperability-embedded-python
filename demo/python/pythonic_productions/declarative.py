from dataclasses import dataclass

from iop import (
    BusinessOperation,
    Message,
    OperationItem,
    PollingBusinessService,
    Production,
    Route,
    ServiceItem,
    target,
)


@dataclass
class OrderRequest(Message):
    order_id: str = ""


class FileService(PollingBusinessService):
    Output = target("orders")

    def on_poll(self):
        self.send_request_sync(self.Output, OrderRequest(order_id="777"))


class OrderOperation(BusinessOperation):
    def on_message(self, request):
        print(f"Received order request: {request}")
        return request


ORDER_OPERATION = OperationItem("OrderOperation", OrderOperation)


class DeclarativeProduction(Production):
    name = "Demo.DeclarativeProduction"
    testing_enabled = True

    services = (
        ServiceItem(
            "FileInput",
            FileService,
            routes=(Route(FileService.Output, ORDER_OPERATION),),
        ),
    )
    operations = (ORDER_OPERATION,)


prod = DeclarativeProduction()

# print(prod.graph())

PRODUCTIONS = [prod]
