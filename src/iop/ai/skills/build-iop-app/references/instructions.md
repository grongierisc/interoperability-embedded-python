# IoP Application Rules

Use a Python `Production` exported through `PRODUCTIONS`. Declare services,
processes, operations, targets, and connections as a message graph. Components
communicate through messages and configured targets, never direct component
instantiation.

Use `on_init()` and `on_tear_down()` for lifecycle work. Use dataclasses with
regular `Message` classes but not `PydanticMessage`. Reserve
`PersistentMessage` for native persistent IRIS bodies. Prefer typed handlers or
`@handler`, with `on_message` as a fallback.

Treat the directory containing `settings.py` as the import root. Fix imports or
layout instead of mutating `PYTHONPATH` or global `sys.path`.

Prefer native IRIS and Health Connect healthcare standards and transports, then
use Python for project-specific orchestration and outbound integrations.
