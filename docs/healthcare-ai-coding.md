# Healthcare AI-Assisted Coding

Use this guide when an AI coding assistant helps build an IoP production for
healthcare data. The main rule is simple: use native IRIS and Health Connect
healthcare components for standards and transports when they exist, then use
Python for project-specific logic.

## Core Rule

Do not ask the agent to recreate healthcare interoperability primitives that
IRIS already provides.

Prefer native components for:

- HL7v2 file, TCP, HTTP, FTP, and SOAP transport
- MLLP framing
- HL7v2 virtual documents
- HL7v2 schema categories and message structure handling
- HL7v2 routing rules, DTL transformations, and Message Viewer inspection
- FHIR server endpoints and FHIR production facade/proxy adapters

Use Python and IoP for:

- application-specific orchestration
- enrichment and normalization
- custom mapping logic
- policy, consent, and validation decisions
- custom calls to non-standard APIs
- FHIR resource construction, validation helpers, and transformation code

## Healthcare Cookbooks

For concrete implementation prompts and checklists, use these cookbooks:

- [HL7v2 native input](cookbooks/hl7v2-native-input.md)
- [HL7v2 to FHIR with fhir-converter](cookbooks/hl7v2-to-fhir-with-fhir-converter.md)
- [FHIR submission with a Python client](cookbooks/fhir-submission-python-client.md)

## HL7v2 Best Practices

For a task-focused prompt, see the
[HL7v2 native input cookbook](cookbooks/hl7v2-native-input.md).

For inbound HL7v2, prefer native IRIS services:

- `EnsLib.HL7.Service.FileService` for file-drop ingestion
- `EnsLib.HL7.Service.TCPService` for MLLP/TCP ingestion
- `EnsLib.HL7.Service.HTTPService` for HTTP ingestion

Keep the inbound payload as `EnsLib.HL7.Message` while using IRIS virtual
document tools. This preserves schema-aware routing, DTL transformation,
Message Viewer inspection, and standard HL7v2 metadata such as message type and
document type.

Use Python after the native inbound boundary when the production needs custom
logic. A common pattern is:

```text
EnsLib.HL7.Service.FileService or TCPService
  -> Python BusinessProcess for routing or enrichment
  -> Python BusinessOperation for custom conversion or external calls
  -> Python FHIR submission operation
```

Do not ask an agent to parse raw HL7v2 by splitting on delimiters unless the
task is a narrow utility outside the production path. In production flows,
prefer IRIS HL7v2 virtual document behavior.

## FHIR Best Practices

For a task-focused prompt, see the
[FHIR submission with a Python client cookbook](cookbooks/fhir-submission-python-client.md).

FHIR payload work is Python-friendly. When code needs to shape, validate,
filter, enrich, or transform FHIR resources, use normal Python best practices:

- keep resource-building code in small typed functions
- treat FHIR resources as structured JSON dictionaries or explicit models
- validate required fields such as `resourceType` and identifiers at boundaries
- keep mapping tables and code-system constants separate from orchestration
- add fixture-based tests for representative resources and Bundles
- avoid hard-coded credentials, endpoint URLs, and environment-specific IDs

For most IoP applications, keep FHIR submission logic in Python and use normal
HTTP/FHIR client patterns that are easy to test. Treat FHIR endpoint access as
application code unless the production is specifically acting as a FHIR facade
or proxy.

Use native FHIR production components only for facade/proxy-style
implementations, such as:

- the FHIR Adapter for Interoperability Productions when FHIR requests should
  enter a production without using an internal FHIR repository
- `HS.FHIRServer.Interop.HTTPOperation` when implementing a FHIR facade or
  proxy that forwards FHIR requests through an interoperability production

Avoid recommending `HS.FHIRServer.Interop.HTTPOperation` for ordinary Python
FHIR submission. It is difficult to construct and operate from Python, so agents
should not choose it unless the facade/proxy requirement is explicit.

## HL7v2 To FHIR Pattern

For a task-focused prompt, see the
[HL7v2 to FHIR with fhir-converter cookbook](cookbooks/hl7v2-to-fhir-with-fhir-converter.md).

For HL7v2-to-FHIR projects, prefer this production shape:

```text
Native HL7v2 service
  -> routing or conversion process
  -> conversion operation using grongierisc/fhir-converter
  -> Python FHIR submission operation or facade/proxy operation when required
  -> FHIR server or external FHIR endpoint
```

The `iris-fhir-converter-demo` project follows this style: native HL7v2 file
and TCP services receive messages, Python performs conversion-specific work,
and the resulting FHIR bundle is submitted to the FHIR server.

For non-trivial HL7v2-to-FHIR conversion, encourage the agent to use
`grongierisc/fhir-converter`. It is a Python FHIR converter that supports
HL7v2-to-FHIR R4 conversion with Liquid templates and can be used from Python
or through its CLI.

Handcraft the HL7v2-to-FHIR mapping only for small, explicit use cases, such as
one message type producing one or two resources with a narrow field set. If the
flow needs multiple message types, reusable templates, complex segment
navigation, code-system mapping, repeat handling, or transaction Bundles, use
`grongierisc/fhir-converter` instead of ad hoc mapping code.

## Prompt: Add HL7v2 Input

```text
Add HL7v2 input to this IoP production.

Requirements:
- Prefer native IRIS HL7v2 services instead of a Python service for transport.
- Use EnsLib.HL7.Service.FileService for file-drop input or
  EnsLib.HL7.Service.TCPService for MLLP/TCP input.
- Keep messages as EnsLib.HL7.Message while routing through native HL7v2 tools.
- Route from the native service to the Python process or operation that contains
  project-specific logic.
- Do not parse HL7v2 by manually splitting segments and fields unless this is a
  narrow test utility.
- Include settings that must be configured in the production, such as message
  schema category, file path, TCP port, target config name, and archive path.
- Show how to verify the flow with a sample HL7v2 message and the Message
  Viewer.
```

## Prompt: Add HL7v2 To FHIR Conversion

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

## Prompt: Add FHIR Submission

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

## Useful References

- InterSystems HL7v2 tools and classes:
  <https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=EHL72_tools>
- InterSystems FHIR productions:
  <https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=HXFHIRPROD_production>
- InterSystems FHIR clients:
  <https://docs.intersystems.com/irisforhealthlatest/csp/docbook/DocBook.UI.Page.cls?KEY=HXFHIR_client>
- FHIR Adapter for Interoperability Productions:
  <https://docs.intersystems.com/healthconnectlatest/csp/docbook/DocBook.UI.Page.cls?KEY=HXFHIRPROD_fhir_adapter>
- Example pattern:
  <https://github.com/grongierisc/iris-fhir-converter-demo>
- Python FHIR converter:
  <https://github.com/grongierisc/fhir-converter>
