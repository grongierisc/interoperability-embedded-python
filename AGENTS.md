# IoP Agent Guide

This repository contains IoP, Interoperability On Python. IoP lets developers
build InterSystems IRIS and Health Connect interoperability productions with
Python components, messages, and production graphs.

## Read First

Before changing code or examples, read:

- `README.md` for the package overview.
- `docs/ai-coding.md` for AI-assisted coding guidance.
- `docs/cookbooks/index.md` for task-specific app-building workflows.
- `docs/cookbooks/code-index.md` when starting from source code.
- `docs/getting-started/first-steps.md` for the preferred beginner workflow.
- `docs/getting-started/register-component.md` for migration file structure.
- `docs/production-graph.md` for Python-authored production definitions.
- `docs/production-change-workflow.md` before changing existing IRIS
  productions.

## Project Map

- `src/iop/components`: component base classes and component settings helpers.
- `src/iop/messages`: message classes, serialization, validation, and dispatch.
- `src/iop/production`: production graph, validation, rendering, diff, and
  planning.
- `src/iop/cli`: `iop` command-line parser, command dispatch, and formatting.
- `src/iop/migration`: migration file loading, IRIS registration, and
  production import/export utilities.
- `src/iop/cls`: ObjectScript support classes packaged with IoP.
- `demo/python`: runnable examples for common production patterns.
- `src/tests/unit`: fast tests that should not require a live IRIS instance.
- `src/tests/e2e`: IRIS-backed local and remote integration tests.

## Coding Rules

- For new applications, prefer a Python `Production` object exported through
  `PRODUCTIONS` in `settings.py`.
- Use `prod.service(...)`, `prod.process(...)`, `prod.operation(...)`, and
  `prod.connect(...)` to declare topology.
- Use `target()` on component classes for configurable outbound targets, then
  connect those targets in the production graph.
- Use `on_message(self, request)` as a simple fallback handler.
- Use typed one-argument methods or `@handler(MessageType)` to route by message
  type.
- Do not put component startup logic in `__init__()`. IoP/IRIS allocates
  components with `__new__()` and calls `on_init()` as the startup hook.
- Use `on_tear_down()` for cleanup when a component becomes inactive.
- Use regular `Message` or `PydanticMessage` classes for Python messages.
- Use `PersistentMessage` only when a native persistent IRIS message body is
  required.
- Avoid raw `CLASSES` entries for new production components. Use `CLASSES` only
  for standalone bindings or legacy migration files.
- Keep executable sample code behind `if __name__ == "__main__":` when it lives
  in a migration file, so migration can import `PRODUCTIONS` safely.
- For app-building tasks, use the relevant cookbook in `docs/cookbooks/` before
  writing code or examples.

## Verification Commands

Fast local checks:

```bash
python -m pytest src/tests/unit
ruff check src
pyright
```

Validate a migration file without writing to IRIS:

```bash
iop --migrate /path/to/settings.py --dry-run
```

Run the Docker-backed test suite:

```bash
docker build -t pytest-iris -f dockerfile-ci .
docker run -i --rm pytest-iris
```

Build documentation:

```bash
mkdocs build
```

## IoP Production Best Practices

- A production is a message graph.
- Business Services are inbound entry points or triggers. They may be Python IoP
  services or native IRIS services.
- Business Processes orchestrate routing, decisions, transformations, and calls
  to downstream components.
- Business Operations isolate outbound side effects such as external APIs,
  database writes, files, TCP, HTTP, or FHIR endpoints.
- Components communicate through production messages and targets. Do not
  instantiate another production component or call its methods directly.
- For healthcare transports and standards, prefer native IRIS or Health Connect
  components when they exist, then use Python for project-specific logic.
