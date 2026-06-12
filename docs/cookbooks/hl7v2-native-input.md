# Cookbook: HL7v2 Native Input

## When To Use This

Use this cookbook when a healthcare production receives HL7v2 by file drop,
MLLP/TCP, or HTTP. Prefer native IRIS and Health Connect HL7v2 components for
transport, virtual documents, routing, and Message Viewer support.

## Files You Will Touch

- `settings.py` or production configuration
- sample HL7v2 messages under `data/` or `samples/`
- Python process or operation code only after the native HL7v2 boundary

## Prompt To Give Your Agent

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

## Expected Implementation

The production should look like this:

```text
EnsLib.HL7.Service.FileService or EnsLib.HL7.Service.TCPService
  -> Python BusinessProcess or native routing rule
  -> Python BusinessOperation or downstream native operation
```

Keep HL7v2 as `EnsLib.HL7.Message` until custom Python logic needs a derived
payload. Let IRIS handle MLLP framing, message structure, schema category,
archive behavior, and Message Viewer inspection.

## Migration Command

```bash
iop --migrate settings.py --dry-run
iop --migrate settings.py
```

## Verification

- Send or drop a sample HL7v2 message.
- Confirm the native service accepts the message.
- Inspect the message in Message Viewer.
- Confirm the message reaches the target Python process or operation.

## Common Mistakes

- Reimplementing MLLP framing in Python.
- Parsing HL7v2 with string splitting in the production path.
- Losing Message Viewer traceability by converting too early.
- Forgetting native service settings such as schema category, file path, TCP
  port, target config name, and archive path.

