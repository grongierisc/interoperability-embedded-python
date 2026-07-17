# IoP Application Rules

Use a Python `Production` exported through `PRODUCTIONS`. Declare services,
processes, operations, targets, and connections as a message graph. Components
communicate through messages and configured targets, never direct component
instantiation.

A polling service owns acquisition from the source it polls and emits a
data-bearing message. A process owns validation, transformation, routing, and
orchestration. An operation owns destination effects such as persistence or
submission. Model complete ingestion flows as `service -> process -> operation`
unless a genuinely trivial pass-through is explicitly justified.

Use `on_init()` and `on_tear_down()` for lifecycle work. Use dataclasses with
regular `Message` classes but not `PydanticMessage`. Reserve
`PersistentMessage` for native persistent IRIS bodies. Prefer typed handlers or
`@handler`, with `on_message` as a fallback.

Treat the directory containing `settings.py` as the import root. Fix imports or
layout instead of mutating `PYTHONPATH` or global `sys.path`.

Inspect dependency manifests and Docker or Compose lifecycle files before
editing them. Declare direct dependencies and preserve working initialization,
migration, and production startup automation.

Prefer native IRIS and Health Connect healthcare standards and transports, then
use Python for project-specific orchestration and outbound integrations.
