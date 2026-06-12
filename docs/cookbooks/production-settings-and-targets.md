# Cookbook: Production Settings And Targets

## When To Use This

Use this cookbook when adding routing, configurable destinations, or production
topology to an IoP application.

## Files You Will Touch

- component modules that need `target()` settings
- `settings.py`
- tests or migration dry-run output

## Prompt To Give Your Agent

```text
Update the IoP production settings for this flow.

Topology:
<describe the service, process, operation, and route names>

Implementation requirements:
- Use a Python Production object.
- Add services with prod.service(...), processes with prod.process(...), and
  operations with prod.operation(...).
- Use target() attributes on component classes for outbound routing.
- Use prod.connect(source.TargetName, destination) for graph edges.
- Keep PRODUCTIONS = [prod] as the migration entrypoint.
- Do not add raw CLASSES entries for components already declared in the
  Production graph.
- Show the migration dry-run command.
```

## Expected Implementation

Declare outbound targets on the component class:

```python
from iop import BusinessProcess, target


class RouteProcess(BusinessProcess):
    Accepted = target()
    Rejected = target()
```

Wire targets in `settings.py`:

```python
process = prod.process("RouteProcess", RouteProcess)
accepted = prod.operation("AcceptedOperation", AcceptedOperation)
rejected = prod.operation("RejectedOperation", RejectedOperation)

prod.connect(process.Accepted, accepted)
prod.connect(process.Rejected, rejected)
```

## Migration Command

```bash
iop --migrate settings.py --dry-run
```

## Verification

- Dry-run migration shows the expected `PRODUCTIONS` section.
- The production graph contains every expected edge.
- No component already in the graph is duplicated in raw `CLASSES`.

## Common Mistakes

- Using string component names inside business logic instead of configurable
  `target()` settings.
- Adding a component to `settings.py` but forgetting its graph edge.
- Using raw production dictionaries for new Python-authored topology.

