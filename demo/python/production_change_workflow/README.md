# Production Change Workflow Example

This example demonstrates the conservative plan, review, apply, verify, and
rollback workflow.

The desired production is defined in `settings.py`. The service starts disabled
so the first safe apply can add or update configuration without immediately
starting the polling loop.

## CLI

Build and review a plan:

```bash
iop --plan demo/python/production_change_workflow/settings.py \
    --production Demo.ChangeWorkflowProduction \
    --out plan.json

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

Rollback from the backup directory printed by apply:

```bash
iop --rollback-backup .iop/backups/<backup-id> --allow-destructive
```

## Python

The guarded `workflow.py` script exposes the same steps:

```bash
python demo/python/production_change_workflow/workflow.py plan
python demo/python/production_change_workflow/workflow.py review
python demo/python/production_change_workflow/workflow.py apply
python demo/python/production_change_workflow/workflow.py verify
python demo/python/production_change_workflow/workflow.py rollback \
    --backup .iop/backups/<backup-id> \
    --allow-destructive
```

Apply and rollback require local IRIS access in v1. Planning and verification
can use existing export/inspection paths.

