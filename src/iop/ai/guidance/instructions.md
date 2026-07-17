# IoP Application Guidance

This repository contains an IoP application. IoP means Interoperability On
Python: a Python-first framework for building InterSystems IRIS and Health
Connect interoperability productions.

## Start With The Application

Before a major change, establish the business goal, inbound and outbound
systems, protocols or standards, routing and transformation behavior, runtime
constraints, and acceptance criteria. Infer facts from the repository before
asking the user.

Read the project README, `settings.py`, the production graph, message and
component modules, tests, fixtures, sample payloads, dependency files, and
available Docker or Compose lifecycle. Use the bundled `build-iop-app` skill
for implementation workflows and `validate-iop-app` for verification.

## IoP Rules

- Prefer a Python `Production` exported through `PRODUCTIONS`.
- Declare topology with `prod.service(...)`, `prod.process(...)`,
  `prod.operation(...)`, and graph connections.
- Declare configurable outbound routes with `target()` and connect them through
  the production graph.
- Communicate between production components through messages and configured
  targets. Do not instantiate another production component directly.
- Use `on_init()` for startup and `on_tear_down()` for cleanup. Do not put
  component startup logic in `__init__()`.
- Use `@dataclass` on regular `Message` classes. Do not add `@dataclass` to
  `PydanticMessage` classes.
- Use `PersistentMessage` only when IRIS requires a native persistent message
  body.
- Prefer typed one-argument handlers or `@handler(MessageType)`. Use
  `on_message(self, request)` as a simple fallback.
- Avoid raw `CLASSES` entries for components already declared in a production
  graph. Keep them for standalone bindings and legacy migrations.
- Keep executable migration examples behind `if __name__ == "__main__":` so
  `PRODUCTIONS` can be imported safely.

## Project Imports

Treat the directory containing `settings.py` as the project import root. Use
modules reachable relative to that file. Fix package layout or imports instead
of modifying `PYTHONPATH`, `os.environ["PYTHONPATH"]`, or global `sys.path` in
application code.

## Production Design

- Business Services are inbound entry points and triggers. A polling service
  owns acquisition from the source it polls, including an HTTP, file, or
  database read, and emits a data-bearing message.
- Business Processes own routing, decisions, transformations, and orchestration.
- Business Operations isolate destination side effects such as persistence,
  file writes, submissions, and API calls made after processing. An API lookup
  requested by a process is also an operation; acquisition by a polling service
  from its configured source remains service work.
- Model a complete source-to-destination ingestion flow as `service -> process
  -> operation` by default. Omit the process only for a genuinely trivial
  pass-through and state why no orchestration boundary is needed.
- Prefer native IRIS or Health Connect components for established healthcare
  standards and transports, then use Python for application-specific logic.

For an existing or shared IRIS production, inspect and plan changes before
mutation. Use the conservative plan, review, apply, verify, and backup workflow;
do not treat an imported graph as a lossless reconstruction of deployed intent.

## Completion

Add or update focused tests, declare direct dependencies, and preserve working
project lifecycle automation when behavior changes. Run the `validate-iop-app`
skill and report commands, results, and remaining runtime verification clearly.
