---
name: validate-iop-app
description: Validate an IoP application with unit tests, strict migration dry-run, and optional IRIS runtime checks. Use after changing messages, components, production topology, settings, migration files, or runtime behavior.
---

# Validate An IoP Application

Read `references/testing.md` and inspect the repository for its actual test and
migration entrypoints.

## Workflow

1. Run the project's focused Python tests, normally `python -m pytest`.
2. Run strict non-mutating migration validation:

   ```bash
   iop --migrate settings.py --dry-run --strict-production-validation
   ```

3. Fix failures at the smallest boundary: Python logic, imports, production
   graph, migration validation, IRIS runtime, external dependency, or test data.
4. Only perform live migration or production actions when requested and the
   target environment is known.
5. For runtime verification, check status plus an observable message, log,
   queue, output, API effect, database write, or FHIR resource.
6. Report exact commands, results, skipped runtime checks, and residual risk.

Do not use `iop --test` as the normal Business Service test path. Use the
production runtime or director so deployed settings and targets are active.
