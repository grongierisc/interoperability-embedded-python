# Production Change Workflow

The production change workflow is the conservative path for changing an
existing IRIS production from a Python `Production` definition:

1. Build a change plan.
2. Review the plan.
3. Apply only supported safe operations by default.
4. Verify that applied operations converged.
5. Roll back from the backup export when needed.

This workflow is intended for real IRIS productions where the deployed state
may contain ObjectScript components, BPL, DTL, routing rules, dynamic targets,
custom settings, and runtime-only behavior that cannot be fully reconstructed
from Python.

## Why Use This Instead Of `sync()`

`prod.sync()` remains the explicit full-registration path. It writes the full
Python production definition to local IRIS through the migration machinery.

`prod.apply()` uses a saved `ProductionChangePlan`. It compares the current IRIS
production with the desired Python production and applies granular operations
only when they are supported and allowed by policy.

Use `sync()` for Python-authored productions where the Python definition is the
complete source of truth. Use `plan()` and `apply()` for brownfield or shared
IRIS productions where preserving unmodeled deployed behavior matters.

## Risk Policy

The plan classifies each operation before mutation.

| Risk | Default behavior | Examples |
| --- | --- | --- |
| `safe` | Applied by default | Add item, change production setting, change item scalar field, set Host/Adapter setting, change an explicit route setting |
| `destructive` | Skipped unless `allow_destructive=True` or `--allow-destructive` | Delete item, remove setting, remove route, replace component class |
| `unsupported` | Always skipped | Runtime-only route with no source setting, dynamic route that cannot be mapped to a static setting |

Unknown existing items, settings, and routes are not removed just because the
desired Python production omits them. They appear as blocked operations in the
plan so an operator can review the gap.

## Python API

Create a plan from the desired production:

```python
from pathlib import Path

from settings import prod


plan = prod.plan()
print(plan)
plan.save("plan.json")
```

Apply the safe operations:

```python
from iop import ProductionChangePlan
from settings import prod


plan = ProductionChangePlan.load("plan.json")
result = prod.apply(plan, backup_dir=".iop/backups")
print(result)
```

Verify after apply:

```python
from iop import ProductionChangePlan
from settings import prod


plan = ProductionChangePlan.load("plan.json")
result = prod.verify(plan)
print(result)
```

Allow destructive operations only when the plan has been reviewed:

```python
result = prod.apply(
    plan,
    allow_destructive=True,
    backup_dir=".iop/backups",
)
```

Rollback restores the full production export saved before apply:

```python
from iop import Production


result = Production.rollback_backup(
    ".iop/backups/20260604T120000Z-abc123def456",
    allow_destructive=True,
)
print(result)
```

## CLI Workflow

Build a plan from a `settings.py` file:

```bash
iop --plan demo/python/production_change_workflow/settings.py \
    --production Demo.ChangeWorkflowProduction \
    --out plan.json
```

Review it:

```bash
iop --review-plan plan.json
```

Apply safe operations locally:

```bash
iop --apply-plan plan.json \
    --settings demo/python/production_change_workflow/settings.py \
    --backup-dir .iop/backups
```

Verify:

```bash
iop --verify-plan plan.json
```

Rollback from a backup directory:

```bash
iop --rollback-backup .iop/backups/20260604T120000Z-abc123def456 \
    --allow-destructive
```

`--apply-plan` and `--rollback-backup` require local IRIS access in this v1
workflow. Remote REST apply and rollback are deliberately blocked. Planning and
verification can use the existing export, connections, and queue inspection
paths.

## Backup Files

Before any apply mutation, IoP writes a backup directory containing:

- `production.json`: exported production definition
- `production.xml`: XML representation of the current production
- `connections.json`: runtime connection export
- `queues.json`: queue counter export
- `plan.json`: the plan that was applied
- `metadata.json`: backup id, timestamp, user, host, namespace, production, and
  plan fingerprints

If the plan has no applicable operations, no backup is written because no IRIS
mutation is attempted.

## Brownfield Guidance

Start with inspection:

```bash
iop -e Demo.Production --format graph
iop -e Demo.Production --format python > imported_production.py
```

Review the generated Python before using it as desired state. IRIS export cannot
fully reconstruct Python class objects, original variable names, BPL/DTL/rule
intent, conditional routing, or all dynamic targets.

When working with built-in or ObjectScript components, declare route settings
manually:

```python
from iop import Production


prod = Production("Demo.Production")
file_in = prod.service("FileIn", class_name="EnsLib.File.PassthroughService")
file_out = prod.operation("FileOut", class_name="EnsLib.File.PassthroughOperation")

prod.connect(file_in.target_setting("TargetConfigNames"), file_out)
```

Runtime-only routes that cannot be mapped to a Host setting are reported as
unsupported plan operations and are not mutated.

