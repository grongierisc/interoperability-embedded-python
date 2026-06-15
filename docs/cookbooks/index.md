# IoP Cookbooks

These cookbooks are task-oriented prompts and checklists for building IoP
applications with an AI coding assistant.

Before using a cookbook, give the assistant this context:

```text
You are helping me build an IoP application.
Read AGENTS.md, settings.py, and the relevant cookbook before changing code.
Use the Python Production graph workflow for new applications.
Do not put component startup logic in __init__(); use on_init().
Show the migration and verification commands.
```

## General Workflows

- [Code index for agents](code-index.md)
- [Hello-world production](hello-world-production.md)
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
