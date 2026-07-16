# Cookbook: FHIR Submission With A Python Client

## When To Use This

Use this cookbook when a Python IoP component needs to submit FHIR resources or
Bundles to an internal or external FHIR endpoint. For ordinary app logic, prefer
Python HTTP/FHIR client code that is simple to test.

Use `HS.FHIRServer.Interop.HTTPOperation` only when the project explicitly
implements a FHIR facade or proxy production.

## Files You Will Touch

- Python operation or helper module that submits FHIR
- message classes carrying the FHIR resource or Bundle
- configuration or environment documentation for endpoint and credentials
- fixture tests for representative FHIR payloads

## Prompt To Give Your Agent

```text
Add FHIR submission to this IoP production.

Requirements:
- Use Python best practices for FHIR resource shaping, validation helpers,
  mapping code, and fixture-based tests.
- Use a Python HTTP/FHIR client pattern for ordinary FHIR submission.
- Use HS.FHIRServer.Interop.HTTPOperation only when the project explicitly
  implements a FHIR facade or proxy production.
- Configure the FHIR endpoint through settings or environment variables rather
  than hard-coding URLs in Python.
- Keep credentials and OAuth details out of committed source.
- Include how to test create, update, or transaction Bundle submission.
- Include how to inspect production messages and query the FHIR endpoint.
```

## Expected Implementation

FHIR payload code should stay small and testable:

```python
def validate_resource(resource: dict) -> None:
    if not resource.get("resourceType"):
        raise ValueError("FHIR resource must include resourceType")
```

The operation should read endpoint configuration from settings or environment
variables and keep credentials out of source code.

```python
from iop import BusinessOperation


class FhirSubmitOperation(BusinessOperation):
    def on_message(self, request):
        resource = request.resource
        validate_resource(resource)
        # Submit with the project's configured Python HTTP/FHIR client.
        return request
```

## Migration Command

```bash
iop --migrate settings.py --dry-run
iop --migrate settings.py
```

## Verification

- Unit-test FHIR resource shaping and validation helpers with fixtures.
- Test create, update, or transaction Bundle submission against a development
  endpoint.
- Query the FHIR endpoint for the expected result.
- Inspect production messages to confirm the submitted payload and response.

## Common Mistakes

- Using `HS.FHIRServer.Interop.HTTPOperation` for ordinary Python submission.
- Hard-coding endpoints, credentials, OAuth tokens, or environment-specific IDs.
- Building large FHIR resources inline inside orchestration code.
- Skipping fixture tests for representative resources and Bundles.

