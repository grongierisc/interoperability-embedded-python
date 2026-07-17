# IoP Cookbooks

These cookbooks are task-oriented prompts and checklists for building IoP
applications with an AI coding assistant.

Install version-matched offline copies together with the IoP application skills:

```bash
iop --install-agent-guidance
```

The `build-iop-app` skill selects and loads every installed cookbook implicated
by a requested flow. See [IoP Agent Guidance And Skills](../agent-guidance.md)
for other projects and agent-specific installation.

The current Skills CLI requires Node.js 22.20.0 or newer. Check the active
version before installing:

```bash
node --version
```

To install only the portable skills in the current project, run:

```bash
npx skills add \
  https://github.com/grongierisc/interoperability-embedded-python/tree/master/src/iop/ai/skills \
  --skill build-iop-app \
  --skill validate-iop-app
```

Add `--global` to make the skills available to supported agents across all
projects:

```bash
npx skills add \
  https://github.com/grongierisc/interoperability-embedded-python/tree/master/src/iop/ai/skills \
  --skill build-iop-app \
  --skill validate-iop-app \
  --global
```

Prefer the project-local installation when its skills must remain aligned with
that project's IoP version. Global installation is convenient when working
across many IoP repositories. Neither direct Skills CLI installation adds the
always-on project guides installed by `iop --install-agent-guidance`.

Before using a cookbook, give the assistant this context:

```text
You are helping me build an IoP application.
Read local AGENTS.md if this application has one, settings.py, and every
applicable cookbook before changing code.
Use the Python Production graph workflow for new applications.
Do not put component startup logic in __init__(); use on_init().
Treat the directory containing settings.py as the project import root.
Import production modules relative to settings.py; do not modify PYTHONPATH.
Do not use iop --test to test Business Services; use the runtime director.
Show the migration and verification commands.
```

## General Workflows

- [Code index for agents](code-index.md)
- [Hello-world production](hello-world-production.md)
- [Build a source-to-destination ingestion pipeline](ingestion-pipeline.md)
- [Add a BusinessOperation](add-business-operation.md)
- [Add a BusinessProcess](add-business-process.md)
- [Add a PollingBusinessService](add-polling-service.md)
- [Production settings and targets](production-settings-and-targets.md)
- [Remote migration](remote-migration.md)

## Healthcare Workflows

- [HL7v2 native input](hl7v2-native-input.md)
- [HL7v2 to FHIR with fhir-converter](hl7v2-to-fhir-with-fhir-converter.md)
- [FHIR submission with a Python client](fhir-submission-python-client.md)

## Expected Output

Generated code should usually include:

- component and message code with clear names
- a `settings.py` file with a `Production` object
- `PRODUCTIONS = [prod]`
- `target()` settings for configurable outbound routing
- `prod.connect(...)` calls for graph edges
- sample payloads or tests when behavior changes
- migration and verification commands
