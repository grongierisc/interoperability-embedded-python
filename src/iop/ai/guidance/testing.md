# Testing IoP Applications

Run the fastest relevant checks first from the project root.

## Local Checks

1. Run the project's Python tests:

   ```bash
   python -m pytest
   ```

2. Validate the migration without writing to IRIS:

   ```bash
   iop --migrate settings.py --dry-run --strict-production-validation
   ```

Resolve import errors through package layout and imports, not `PYTHONPATH`
changes in application code.

## Runtime Checks

Use a repository-owned disposable Docker or Compose environment for runtime
verification when it is available. Only mutate a shared, remote, or otherwise
non-disposable IRIS environment when the user requests it and the target is
known. Verify at least one observable result:

- production and component status;
- expected output file, API request, database write, or FHIR resource;
- production logs without blocking errors;
- Message Viewer flow or queue state.

Container health is not production health. Confirm initialization and migration
completed, use `iop --status` to verify the intended production is running, then
trigger or wait for a Business Service and inspect an actual destination effect.
Prefer `iop` commands for migration, start, status, logs, and queues. Do not use
an ObjectScript terminal when the IoP CLI supports the operation.

Do not use `iop --test` as the normal way to test a Business Service. Use the
production runtime or director path so deployed settings, targets, and runtime
context are active.

For shared or brownfield productions, use a reviewed production change plan and
backup rather than full registration by default.
