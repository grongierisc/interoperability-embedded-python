# Cookbook: HL7v2 To FHIR With fhir-converter

## When To Use This

Use this cookbook for non-trivial HL7v2-to-FHIR conversion. Prefer
`grongierisc/fhir-converter` when the flow has multiple message types, reusable
templates, complex segment navigation, code-system mapping, repeats, or
transaction Bundles.

Handcraft the mapping only for small explicit flows with a narrow field set and
one or two target resources.

## Files You Will Touch

- native HL7v2 production configuration or `settings.py`
- Python conversion operation or helper module
- Liquid templates for `grongierisc/fhir-converter`
- sample HL7v2 messages and expected FHIR fixtures
- Python FHIR submission code

## Prompt To Give Your Agent

```text
Add an HL7v2-to-FHIR flow to this IoP production.

Requirements:
- Receive HL7v2 with native IRIS HL7v2 services.
- Keep HL7v2 payloads as EnsLib.HL7.Message until custom conversion logic is
  needed.
- Put routing, enrichment, and conversion orchestration in a BusinessProcess.
- For non-trivial conversion, use grongierisc/fhir-converter from a Python
  BusinessOperation or helper module.
- Handcraft the mapping only when the flow is small, explicit, and limited to a
  few fields and resources.
- Submit FHIR from Python unless the project explicitly needs a FHIR facade or
  proxy production.
- Do not implement MLLP framing, HL7 schema handling, or FHIR facade/proxy
  plumbing in Python unless explicitly required.
- Include sample HL7v2 input, expected FHIR resource or bundle shape, migration
  commands, and verification steps.
```

## Expected Implementation

The production should follow this shape:

```text
Native HL7v2 service
  -> routing or conversion process
  -> conversion operation using grongierisc/fhir-converter
  -> Python FHIR submission operation or facade/proxy operation when required
  -> FHIR server or external FHIR endpoint
```

The converter code should be isolated behind a helper or operation so it can be
tested with fixtures. Keep Liquid templates and mapping configuration out of the
business orchestration code.

## Migration Command

```bash
iop --migrate settings.py --dry-run
iop --migrate settings.py
```

## Verification

- Run fixture tests that convert representative HL7v2 samples to expected FHIR
  resources or Bundles.
- Send a sample HL7v2 message through the native service.
- Inspect the HL7v2 message and conversion step in Message Viewer.
- Query the target FHIR endpoint for the expected resource or Bundle result.

## Common Mistakes

- Handcrafting large HL7v2-to-FHIR mappings in one Python method.
- Reimplementing HL7v2 transport or parsing instead of using native services.
- Hard-coding endpoint URLs, credentials, patient identifiers, or code-system
  constants in conversion logic.
- Using `HS.FHIRServer.Interop.HTTPOperation` for ordinary submission instead
  of reserving it for explicit facade/proxy implementations.

