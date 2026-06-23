# Cookbook: Add A PollingBusinessService

## When To Use This

Use this cookbook when a production needs a Python-triggered polling entry
point. For healthcare HL7v2 file or TCP input, prefer native IRIS HL7v2 services
instead of a Python polling service.

## Files You Will Touch

- the service module, such as `bs.py` or `services.py`
- the message module, such as `msg.py` or `messages.py`
- `settings.py`
- tests or sample payloads when behavior changes

## Prompt To Give Your Agent

```text
Add a new IoP PollingBusinessService to this project.

Business goal:
<describe where the service polls from and what message it should emit>

Implementation requirements:
- Define the outbound route as Output = target().
- Implement on_poll(self).
- Create a request Message dataclass if needed.
- Send the request with self.send_request_async(self.Output, request).
- Keep configuration as component settings or class attributes, following the
  existing project pattern.
- Do not put startup code in __init__(); use on_init() only if required.
- Update settings.py to add the service and connect service.Output to the
  destination component.
- Do not use iop --test to test the service; use the runtime director or
  production runtime API for service tests.
- Include migration dry-run and verification commands.
```

## Expected Implementation

```python
from iop import Message, PollingBusinessService, target


class FilePollService(PollingBusinessService):
    Output = target()

    def on_poll(self):
        request = Message()
        self.send_request_async(self.Output, request)
```

In `settings.py`:

```python
service = prod.service("FilePollService", FilePollService)
operation = prod.operation("TargetOperation", TargetOperation)
prod.connect(service.Output, operation)
```

## Migration Command

```bash
iop --migrate settings.py --dry-run
iop --migrate settings.py
```

## Verification

- Dry-run migration shows the service, target setting, and destination
  component.
- Unit tests cover any pure Python polling decisions or message construction.
- Runtime verification confirms `on_poll()` emits the expected message through
  the deployed production context.

## Common Mistakes

- Polling healthcare HL7v2 files in Python instead of using native HL7 file
  services.
- Forgetting to connect `service.Output` to the destination.
- Putting long-lived connection setup in `__init__()` instead of `on_init()`.
