# Cookbook: Add A BusinessOperation

## When To Use This

Use this cookbook when a production needs an outbound side-effect boundary:
calling an API, writing a file, submitting FHIR, storing data, or wrapping a
technical operation behind a production message.

## Files You Will Touch

- the operation module, such as `bo.py` or `operations.py`
- the message module, such as `msg.py` or `messages.py`
- `settings.py`
- the fastest relevant test or sample payload

## Prompt To Give Your Agent

```text
Add a new IoP BusinessOperation to this project.

Business goal:
<describe what the operation receives, validates, logs, transforms, or sends>

Implementation requirements:
- Reuse existing message classes if they already fit.
- If a new message is needed, define it as a Message dataclass unless there is
  a specific need for PersistentMessage.
- Implement a fallback on_message(self, request) for simple operations, or route
  by message type with typed one-argument methods or the @handler decorator.
- Return a response message or the original request when that matches the flow.
- Use self.log_info(), self.log_warning(), or self.log_error() for component
  logging.
- Do not add startup work to __init__(); use on_init() only if startup work is
  required.
- Update settings.py so the operation is added to the Production graph.
- Add or update the fastest relevant test.
- Show the exact verification command.
```

## Expected Implementation

A simple operation can use `on_message()`:

```python
from iop import BusinessOperation

from messages import OrderRequest, OrderResponse


class OrderOperation(BusinessOperation):
    def on_message(self, request: OrderRequest) -> OrderResponse:
        self.log_info(f"Processing order {request.order_id}")
        return OrderResponse(order_id=request.order_id, status="accepted")
```

When one operation handles multiple message types, prefer typed one-argument
methods or the `@handler` decorator:

```python
from iop import BusinessOperation, handler

from messages import CancelOrder, OrderRequest, OrderResponse


class OrderOperation(BusinessOperation):
    def on_message(self, request):
        self.log_warning(f"Unhandled message {type(request).__name__}")
        return request

    def submit_order(self, request: OrderRequest) -> OrderResponse:
        self.log_info(f"Submitting order {request.order_id}")
        return OrderResponse(order_id=request.order_id, status="accepted")

    @handler(CancelOrder)
    def cancel_order(self, request):
        self.log_info(f"Cancelling order {request.order_id}")
        return request
```

IoP dispatches to:

- a method decorated with `@handler(MessageType)` first
- a typed one-argument method such as `submit_order(self, request: OrderRequest)`
- `on_message(self, request)` as the fallback

The production graph should register the operation:

```python
operation = prod.operation("OrderOperation", OrderOperation)
```

If another component sends to the operation, declare a `target()` setting on the
sender and connect it:

```python
prod.connect(process.Orders, operation)
```

## Migration Command

```bash
iop --migrate settings.py --dry-run
iop --migrate settings.py
```

## Verification

Use the fastest local test first:

```bash
python -m pytest
```

If there is no existing test suite, ask the agent to add a small test for the
pure Python transformation or validation logic.

## Common Mistakes

- Creating an operation but not adding it to `settings.py`.
- Calling another production component as a normal Python object.
- Hiding connection names in strings instead of using `target()` and
  `prod.connect(...)`.
- Using `PersistentMessage` when a regular `Message` dataclass is enough.
- Adding multiple handlers for the same message type without making the
  intended precedence explicit.
