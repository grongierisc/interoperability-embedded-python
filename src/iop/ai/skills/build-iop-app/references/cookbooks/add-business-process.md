# Cookbook: Add A BusinessProcess

## When To Use This

Use this cookbook when a production needs routing, orchestration, decision
logic, enrichment, or coordination between services and operations.

Business Processes should not own external side effects directly when a
Business Operation is the better boundary. Keep the process focused on deciding
what happens next and sending messages to downstream targets.

## Files You Will Touch

- the process module, such as `bp.py` or `processes.py`
- the message module, such as `msg.py` or `messages.py`
- operation modules only when downstream behavior is missing
- `settings.py`
- tests or sample payloads for routing decisions

## Prompt To Give Your Agent

```text
Add a new IoP BusinessProcess to this project.

Business goal:
<describe the routing, orchestration, enrichment, or decision logic>

Implementation requirements:
- Reuse existing message classes if they already fit.
- Declare outbound routes with target() attributes on the process class.
- Route messages with send_request_sync(), send_request_async(), or direct
  response behavior according to the existing project pattern.
- Use on_message(self, request) for simple processes, or route by message type
  with typed one-argument methods or the @handler decorator.
- Keep external API calls, database writes, file writes, and FHIR submission in
  BusinessOperation classes.
- Do not add startup work to __init__(); use on_init() only if startup work is
  required.
- Update settings.py so the process is added to the Production graph and its
  targets are connected.
- Add or update tests for routing decisions.
- Show the exact migration and verification commands.
```

## Expected Implementation

A process declares outbound targets and sends messages to them:

```python
from iop import BusinessProcess, Message, handler, target

from messages import OrderRequest, OrderResponse, RejectedOrder


class OrderProcess(BusinessProcess):
    Accepted = target()
    Rejected = target()

    def on_message(self, request):
        self.log_warning(f"Unhandled message {type(request).__name__}")
        return request

    def route_order(self, request: OrderRequest):
        if not request.order_id:
            return self.send_request_sync(self.Rejected, RejectedOrder(reason="missing id"))

        return self.send_request_sync(self.Accepted, request)

    @handler(RejectedOrder)
    def route_rejected(self, request):
        self.log_info(request.reason)
        return request
```

IoP dispatches to:

- a method decorated with `@handler(MessageType)` first
- a typed one-argument method such as `route_order(self, request: OrderRequest)`
- `on_message(self, request)` as the fallback

Wire the process in `settings.py`:

```python
process = prod.process("OrderProcess", OrderProcess)
accepted = prod.operation("AcceptedOperation", AcceptedOperation)
rejected = prod.operation("RejectedOperation", RejectedOperation)

process.connect(OrderProcess.Accepted, accepted)
process.connect(OrderProcess.Rejected, rejected)
```

## Migration Command

```bash
iop --migrate settings.py --dry-run
iop --migrate settings.py
```

## Verification

- Unit-test the routing decision with representative messages.
- Dry-run migration shows the process and all target settings.
- The production graph contains every expected process edge.
- Runtime trace shows messages passing from service to process to operation.

## Common Mistakes

- Putting external API calls or database writes directly in the process.
- Forgetting `target()` declarations for outbound routes.
- Returning raw dictionaries instead of message objects when the downstream
  component expects IoP messages.
- Adding multiple handlers for the same message type without making the
  intended precedence explicit.
- Calling a downstream component directly instead of sending a production
  message through a target.
