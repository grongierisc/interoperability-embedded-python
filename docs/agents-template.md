# Reusable AGENTS.md For IoP Projects

Copy this template into the root of an application repository as `AGENTS.md`.
Adjust the project name, commands, component names, and healthcare-specific
rules to match the application.

````md
# Agent Guide

This project is an IoP application. IoP means Interoperability On Python: a
Python-first way to build InterSystems IRIS and Health Connect interoperability
productions.

## Project Goal

Describe the production in one or two sentences:

- What systems send data into this production?
- What systems receive data from this production?
- Which standards are involved, such as HL7v2, FHIR, JSON, CSV, TCP, HTTP, or
  files?

## Read First

Before changing code, read:

- `README.md` for setup and project-specific workflow.
- `settings.py` for the IoP `Production` graph.
- the relevant cookbook in this project's documentation, if present.
- The modules that define components and messages.
- Existing tests or sample messages before changing behavior.

## Project Map

Update this list for the local project:

- `settings.py`: migration entrypoint with `PRODUCTIONS = [prod]`.
- `production.py` or `prod.py`: Python production graph definition.
- `messages.py` or `msg.py`: Python message classes.
- `bs.py` or `services.py`: Python Business Services.
- `bp.py` or `processes.py`: Python Business Processes.
- `bo.py` or `operations.py`: Python Business Operations.
- `tests/`: local test suite.
- `data/` or `samples/`: example payloads.

## IoP Rules

- Prefer a Python `Production` object exported through `PRODUCTIONS`.
- Use `prod.service(...)`, `prod.process(...)`, `prod.operation(...)`, and
  `prod.connect(...)` to declare topology.
- Use `target()` on component classes for configurable outbound targets.
- Do not put component startup logic in `__init__()`. Use `on_init()`.
- Use `on_tear_down()` for cleanup when a component becomes inactive.
- Use regular `Message` or `PydanticMessage` classes for Python-only messages.
- Use `PersistentMessage` only when IRIS needs a native persistent message body.
- Avoid raw `CLASSES` entries for components already declared in the production
  graph.
- Keep executable sample code behind `if __name__ == "__main__":` when it lives
  in a migration file.
- If this project has IoP cookbook documentation, use the relevant cookbook
  before writing code.

## Production Design Rules

- A production is a message graph.
- Business Services are inbound entry points or triggers. They may be Python IoP
  services or native IRIS services.
- Business Processes orchestrate routing, decisions, transformations, and calls
  to downstream components.
- Business Operations isolate outbound side effects such as external APIs,
  database writes, files, TCP, HTTP, or FHIR endpoints.
- Components communicate through production messages and targets. Do not
  instantiate another production component or call its methods directly.

## Healthcare Rules

Keep this section only for healthcare projects:

- Prefer native IRIS or Health Connect components for healthcare transports,
  parsing, validation, and routing when they exist.
- Use native FHIR production facade/proxy adapters only when that requirement is
  explicit.
- For HL7v2 file or MLLP/TCP input, prefer native HL7 business services such as
  `EnsLib.HL7.Service.FileService` or `EnsLib.HL7.Service.TCPService`.
- Keep HL7v2 as `EnsLib.HL7.Message` while using IRIS virtual document routing,
  schemas, transformations, and Message Viewer.
- Use Python for project-specific enrichment, mapping, policy checks, and calls
  that are not covered by native components.
- Use Python best practices for FHIR resource shaping, validation helpers,
  mapping code, and fixture-based tests.
- For non-trivial HL7v2-to-FHIR conversion, prefer
  `grongierisc/fhir-converter`.
- Handcraft HL7v2-to-FHIR mapping only for small, explicit flows with a narrow
  field set and one or two target resources.
- For ordinary FHIR submission, use Python HTTP/FHIR client code with
  fixture-based tests.
- Use `HS.FHIRServer.Interop.HTTPOperation` only when the project explicitly
  implements a FHIR facade or proxy production.
- Do not hand-roll healthcare protocol framing, HL7v2 parsing, or FHIR server
  plumbing unless the project explicitly requires custom behavior.

## Verification

Use the fastest relevant command first:

```bash
python -m pytest
iop --migrate settings.py --dry-run
iop --migrate settings.py
```

If this repository uses Docker or Compose, add the exact command here:

```bash
docker compose up --build
```

## Expected AI Output

When adding or changing behavior, generated output should include:

- Updated component and message code.
- Updated `settings.py` production graph when topology changes.
- Tests or sample payloads when behavior changes.
- The exact migration and verification commands.
- A short explanation of which native IRIS components are used and why.
````
