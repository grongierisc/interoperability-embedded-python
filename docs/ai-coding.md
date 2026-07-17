# AI-Assisted Coding With IoP

Use this guide when you want to vibe code with IoP while still getting
production-shaped, reviewable Python interoperability code.

## Install Project Guidance

IoP can install version-matched guidance, Agent Skills, and offline cookbooks in
any application repository, whether or not it uses the IoP template:

```bash
iop --install-agent-guidance
```

This configures Codex, Claude Code, and Gemini CLI by default. See
[IoP Agent Guidance And Skills](agent-guidance.md) for agent selection, updates,
conflict handling, and direct installation from GitHub.

## Start Here

Ask the tool to read the project guidance before it writes code:

```text
You are helping me build an IoP application.
Read these files first:
- local AGENTS.md, if this application repository has one
- docs/ai-coding.md
- docs/cookbooks/index.md
- docs/cookbooks/code-index.md, when starting from source code
- docs/getting-started/first-steps.md
- docs/getting-started/register-component.md
- docs/production-graph.md

Use the Python Production graph workflow for new applications.
Do not put component startup logic in __init__(); use on_init().
Treat the directory containing settings.py as the project import root.
Import production modules relative to settings.py; do not modify PYTHONPATH.
Do not use iop --test to test Business Services; use the runtime director.
Use every cookbook implicated by the task.
Show the migration and verification commands.
```

The IoP framework repository root `AGENTS.md` is for framework source
development, not application guidance. For your own IoP application repository,
prefer `iop --install-agent-guidance`; the
[reusable AGENTS.md template](agents-template.md) remains available for manual
setup. For healthcare projects, also read
[Healthcare AI-assisted coding](healthcare-ai-coding.md).

## Cookbooks

Use the [IoP cookbooks](cookbooks/index.md) for task-specific prompts and
checklists:

- [Hello-world production](cookbooks/hello-world-production.md)
- [Build a source-to-destination ingestion pipeline](cookbooks/ingestion-pipeline.md)
- [Code index for agents](cookbooks/code-index.md)
- [Add a BusinessOperation](cookbooks/add-business-operation.md)
- [Add a BusinessProcess](cookbooks/add-business-process.md)
- [Add a PollingBusinessService](cookbooks/add-polling-service.md)
- [Production settings and targets](cookbooks/production-settings-and-targets.md)
- [Remote migration](cookbooks/remote-migration.md)
- [HL7v2 native input](cookbooks/hl7v2-native-input.md)
- [HL7v2 to FHIR with fhir-converter](cookbooks/hl7v2-to-fhir-with-fhir-converter.md)
- [FHIR submission with a Python client](cookbooks/fhir-submission-python-client.md)

## Good Output Expectations

For a new IoP application, generated code should include:

- a `settings.py` file with a `Production` object
- `PRODUCTIONS = [prod]`
- clear component names such as `FileService`, `RouteProcess`, or
  `OrderOperation`
- message classes for data exchanged between components
- `target()` settings for configurable outbound routing
- `prod.connect(...)` calls that wire services, processes, and operations
- sample payloads or tests when behavior changes
- migration and verification commands

## Useful Commands

```bash
# Fast pure-Python checks
python -m pytest src/tests/unit

# Validate a migration file without writing to IRIS
iop --migrate settings.py --dry-run

# Migrate a production
iop --migrate settings.py

# Build the documentation
mkdocs build

# Run the Docker-backed suite
docker build -t pytest-iris -f dockerfile-ci .
docker run -i --rm pytest-iris
```
