# Reusable AGENTS.md For IoP Projects

Copy this template into the root of an application repository as `AGENTS.md`.
Keep it generic. Put project-specific details in the project README or in a
short project brief section.

````md
# Agent Guide

This project is an IoP application. IoP means Interoperability On Python: a
Python-first way to build InterSystems IRIS and Health Connect interoperability
productions.

## First Prompt Contract

Before major implementation, make sure the project goal is explicit. If any of
these details are missing, ask for them or infer only when the repository makes
the answer clear:

- Business goal:
- Inbound systems:
- Outbound systems:
- Data standards or protocols:
- Required routing or transformation behavior:
- Runtime constraints:
- Acceptance criteria:

## Read First

Before changing code, read:

- `README.md` for setup and project-specific workflow.
- `settings.py`, `production.py`, or `prod.py` for the IoP `Production` graph.
- the relevant IoP cookbook, if present in this repository.
- message definitions such as `messages.py` or `msg.py`.
- components such as `bs.py`, `bp.py`, `bo.py`, `services.py`, `processes.py`,
  or `operations.py`.
- existing tests, fixtures, and sample payloads.

If this project does not include local cookbooks, use the public IoP cookbooks:
<https://grongierisc.github.io/interoperability-embedded-python/cookbooks/>

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
- Use `@dataclass` on regular `Message` classes. Do not decorate
  `PydanticMessage` classes with `@dataclass`.
- Use `PersistentMessage` only when IRIS needs a native persistent message body.
- Avoid raw `CLASSES` entries for components already declared in the production
  graph.
- Keep executable sample code behind `if __name__ == "__main__":` when it lives
  in a migration file.

## Dispatch Rules

- Use `on_message(self, request)` as a simple fallback handler.
- Use typed one-argument methods to route by message type, for example
  `submit_order(self, request: OrderRequest)`.
- Use `@handler(MessageType)` when the handler should be explicit or the type
  annotation is not enough.
- Avoid duplicate handlers for the same message type unless the intended
  precedence is clear.

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

## Add-ons

Use add-ons only when the project needs them:

- Healthcare standards such as HL7v2 or FHIR:
  <https://grongierisc.github.io/interoperability-embedded-python/healthcare-ai-coding/>
- HL7v2 native input:
  <https://grongierisc.github.io/interoperability-embedded-python/cookbooks/hl7v2-native-input/>
- HL7v2 to FHIR with fhir-converter:
  <https://grongierisc.github.io/interoperability-embedded-python/cookbooks/hl7v2-to-fhir-with-fhir-converter/>
- FHIR submission with a Python client:
  <https://grongierisc.github.io/interoperability-embedded-python/cookbooks/fhir-submission-python-client/>

## Definition Of Done

A change is done when the fastest relevant checks pass and the expected
production behavior is observable. Adapt this list to the local project:

```bash
python -m pytest
iop --migrate settings.py --dry-run
iop --migrate settings.py
```

If this repository uses Docker or Compose, add the exact command here:

```bash
docker compose up --build
```

For production behavior, verify at least one of:

- production starts and reports running status
- expected output file, API call, database write, FHIR resource, or message is
  observable
- logs show service/process/operation execution with no blocking errors
- Message Viewer or queue status shows the expected flow

## Troubleshooting Prompts

When diagnosing a failure, report:

- exact command that failed
- traceback or IRIS error
- files read before changing code
- smallest suspected failure boundary: Python, migration, IRIS runtime,
  external dependency, or test data

## Expected AI Output

For every non-trivial change, include:

- updated files list
- short rationale for behavior change
- exact commands used to verify
- test results summary
- residual risk or follow-up item
````
