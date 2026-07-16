# Cookbook: Remote Migration

## When To Use This

Use this cookbook when migration should run against a remote IRIS or Health
Connect instance through IoP remote mode.

## Files You Will Touch

- `settings.py` if the project stores non-secret remote settings there
- environment variables, `.env.example`, or deployment documentation
- CI or local scripts when migration is automated

## Prompt To Give Your Agent

```text
Prepare this IoP production for remote migration.

Remote IRIS settings:
- URL: <remote URL>
- Namespace: <namespace>
- Authentication source: <environment variables or settings.py>

Implementation requirements:
- Prefer environment variables for credentials when possible.
- If settings.py must contain REMOTE_SETTINGS, include url and namespace but do
  not hard-code real passwords in committed examples.
- Keep the Production graph in PRODUCTIONS.
- Show commands for dry-run migration, real migration, and forcing local mode.
- Mention IOP_VERIFY_SSL only if HTTPS certificate verification is relevant.
```

## Expected Implementation

Prefer environment variables for secrets:

```bash
export IOP_URL="http://localhost:52773"
export IOP_USERNAME="SuperUser"
export IOP_PASSWORD="SYS"
export IOP_NAMESPACE="IRISAPP"
```

If the project uses `REMOTE_SETTINGS`, keep examples non-secret:

```python
REMOTE_SETTINGS = {
    "url": "http://localhost:52773",
    "namespace": "IRISAPP",
}
```

## Migration Command

```bash
iop --migrate settings.py --dry-run
iop --migrate settings.py
iop --migrate settings.py --force-local
```

## Verification

- Dry-run migration connects to the intended namespace.
- The output identifies remote mode and the target namespace.
- Forced local mode ignores `REMOTE_SETTINGS` and `IOP_URL`.

## Common Mistakes

- Committing passwords in `settings.py`.
- Confusing the IRIS web server URL with an application endpoint.
- Forgetting that `--force-local` disables remote mode for the command.

