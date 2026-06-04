from dataclasses import dataclass

from iop import (
    BusinessOperation,
    Category,
    Message,
    PollingBusinessService,
    Production,
    setting,
    target,
)


@dataclass
class OrderRequest(Message):
    order_id: str = ""


class OrderService(PollingBusinessService):
    BatchSize = setting(
        10,
        category=Category.BASIC,
        description="Maximum number of orders to poll in one cycle.",
    )
    Output = target(description="Operation that receives polled orders.")

    def on_poll(self):
        self.send_request_async(self.Output, OrderRequest(order_id="1001"))


class OrderOperation(BusinessOperation):
    ArchivePath = setting(
        "/tmp/iop-orders",
        category=Category.CONNECTION,
        description="Directory used by the example operation.",
    )

    def on_message(self, request):
        self.log_info(f"Received order {request.order_id}")
        return request


prod = Production("Demo.ChangeWorkflowProduction", testing_enabled=True)
service = prod.service(
    "OrderService",
    OrderService,
    enabled=False,
    settings={"BatchSize": 10},
)
operation = prod.operation(
    "OrderOperation",
    OrderOperation,
    settings={"ArchivePath": "/tmp/orders"},
)

prod.connect(service.Output, operation)

PRODUCTIONS = [prod]

