---
name: validate-iop-app
description: Validate an IoP application with unit tests, strict migration dry-run, and container-backed IRIS runtime checks when available. Use after changing messages, components, production topology, settings, migration files, container lifecycle, or runtime behavior.
---

# Validate An IoP Application

Read `references/testing.md` and inspect the repository for its actual test,
migration, Docker or Compose, and production lifecycle entrypoints.

## Workflow

1. Run the project's focused Python tests, normally `python -m pytest`.
2. Run strict non-mutating migration validation:

   ```bash
   iop --migrate settings.py --dry-run --strict-production-validation
   ```

3. Fix failures at the smallest boundary: Python logic, imports, production
   graph, migration validation, container lifecycle, IRIS runtime, external
   dependency, or test data.
4. When the repository provides a disposable local Docker or Compose
   environment, rebuild and start it for complete-production changes. Confirm
   its existing initialization path installs IoP support, migrates the current
   settings file, and starts the intended production. Do not replace lifecycle
   steps with a keep-alive loop.
5. Prefer repository scripts and `iop` commands for migration, start, status,
   logs, and queues. Automated validation commands must return control: use
   `iop --start <production-name> --detach` and a finite log snapshot such as
   `iop --log 50`. Bare `iop --start` streams logs; bare `iop --log` follows
   logs until interrupted. Do not use an ObjectScript terminal for an operation
   the IoP CLI supports. Use ObjectScript only when no public IoP path exists
   and report why it was necessary.
6. Verify both production status and an observable end-to-end effect: trigger or
   wait for the Business Service through the runtime, trace a message across the
   expected graph, and inspect the output, persisted row, API effect, or FHIR
   resource. Container health alone is not production health.
7. Only mutate a shared, remote, or otherwise non-disposable IRIS environment
   when the user requests it and the target is identified.
8. Report exact commands, results, skipped runtime checks, and residual risk.

Do not use `iop --test` as the normal Business Service test path. Use the
production runtime or director so deployed settings and targets are active.
