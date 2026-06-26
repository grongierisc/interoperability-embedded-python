# Cookbook: Hello-World Production

## When To Use This

Use this cookbook when starting a new IoP application or when testing that a
development environment can migrate and run a Python-authored production.

## Files You Will Touch

- `hello_world/components.py`
- `hello_world/__init__.py`
- `settings.py`

## Prompt To Give Your Agent

```text
Create a minimal IoP hello-world production.

Requirements:
- Define one Message dataclass named HelloRequest with a text field.
- Define one PollingBusinessService named HelloService.
- Define one BusinessOperation named HelloOperation.
- HelloService must declare Output = target() and send HelloRequest to Output
  from on_poll().
- HelloOperation must log request.text and return the request.
- Create settings.py with Production("HelloWorld.Production", testing_enabled=True).
- Add the service and operation to the production and connect service.Output to
  the operation.
- Export PRODUCTIONS = [prod].
- Do not use __init__() for component startup.
- Do not use iop --test to test HelloService; use the runtime director or
  production runtime API for service tests.
- Show the migration dry-run command and the command to run the production
  migration.
```

## Expected Implementation

The component module should contain the message, service, and operation:

```python
from dataclasses import dataclass

from iop import BusinessOperation, Message, PollingBusinessService, target


@dataclass
class HelloRequest(Message):
    text: str = "Hello World"


class HelloService(PollingBusinessService):
    Output = target()

    def on_poll(self):
        self.send_request_async(self.Output, HelloRequest())


class HelloOperation(BusinessOperation):
    def on_message(self, request: HelloRequest):
        self.log_info(request.text)
        return request
```

The migration entrypoint should define the production graph:

```python
from iop import Production

from hello_world.components import HelloOperation, HelloService


prod = Production("HelloWorld.Production", testing_enabled=True)

service = prod.service("HelloService", HelloService)
operation = prod.operation("HelloOperation", HelloOperation)
service.connect(HelloService.Output, operation)

PRODUCTIONS = [prod]
```

## Migration Command

```bash
iop --migrate settings.py --dry-run
iop --migrate settings.py
```

## Verification

- The dry run shows one production with one service and one operation.
- Migration succeeds without a raw `CLASSES` section.
- The production graph contains one edge from `HelloService.Output` to
  `HelloOperation`.

## Common Mistakes

- Putting startup logic in `__init__()` instead of `on_init()`.
- Forgetting `Output = target()` on the service.
- Adding raw `CLASSES` entries for components already declared in the
  `Production` graph.
- Calling `HelloOperation` directly from `HelloService` instead of sending a
  message through the production target.
