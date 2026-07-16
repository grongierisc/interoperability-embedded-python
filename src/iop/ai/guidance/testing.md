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

Only perform live migration or runtime mutation when the user requests it and
the target IRIS environment is known. Verify at least one observable result:

- production and component status;
- expected output file, API request, database write, or FHIR resource;
- production logs without blocking errors;
- Message Viewer flow or queue state.

Do not use `iop --test` as the normal way to test a Business Service. Use the
production runtime or director path so deployed settings, targets, and runtime
context are active.

For shared or brownfield productions, use a reviewed production change plan and
backup rather than full registration by default.
