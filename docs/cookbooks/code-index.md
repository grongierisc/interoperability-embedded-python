# Cookbook: Code Index For Agents

Use this page when an AI coding assistant starts from source code instead of
the docs. The source contains short breadcrumbs; this page maps those symbols to
the fuller cookbook workflows.

## Public API Breadcrumbs

| Symbol | What It Means | Cookbook |
|--------|---------------|----------|
| `iop.Production` | Python authoring DSL for production topology | [Hello-world production](hello-world-production.md), [Production settings and targets](production-settings-and-targets.md) |
| `iop.target` | Configurable outbound target setting | [Production settings and targets](production-settings-and-targets.md) |
| `iop.BusinessService` | Inbound production entry point | [HL7v2 native input](hl7v2-native-input.md) for healthcare transport choices |
| `iop.PollingBusinessService` | Scheduled Python inbound service | [Add a PollingBusinessService](add-polling-service.md) |
| `iop.BusinessProcess` | Routing, orchestration, decisions, and transformations | [Add a BusinessProcess](add-business-process.md) |
| `iop.BusinessOperation` | Outbound side-effect boundary | [Add a BusinessOperation](add-business-operation.md) |
| `iop.handler` | Explicit message-type dispatch decorator | [Add a BusinessProcess](add-business-process.md), [Add a BusinessOperation](add-business-operation.md) |
| `send_request_sync`, `send_request_async` | Send messages to configured production targets | [Production settings and targets](production-settings-and-targets.md), [Add a BusinessProcess](add-business-process.md) |
| `iop.setting`, `iop.Setting` | Component settings exposed in the IRIS portal | [Production settings and targets](production-settings-and-targets.md) |
| `iop.Message` | Python-only dataclass message contract | [Add a BusinessOperation](add-business-operation.md), [Add a BusinessProcess](add-business-process.md) |
| `iop.PersistentMessage` | Native persistent IRIS message body | [Register Component](../getting-started/register-component.md) |

## Source Files Agents Usually Read

| File | Why It Matters |
|------|----------------|
| `src/iop/__init__.py` | Public import surface and component class breadcrumbs |
| `src/iop/production/model.py` | `Production`, `service`, `process`, `operation`, graph authoring |
| `src/iop/production/types.py` | `target()` and graph types |
| `src/iop/components/settings.py` | `setting(...)`, `Setting`, and IRIS editor controls |
| `src/iop/messages/base.py` | Python-only message contracts |
| `src/iop/messages/persistent.py` | Native persistent IRIS message contracts |
| `src/iop/messages/dispatch.py` | `@handler`, typed method dispatch, fallback `on_message()` |
| `src/iop/components/business_process.py` | process runtime hooks and request helpers |
| `src/iop/components/business_operation.py` | operation runtime dispatch |
| `src/iop/components/business_service.py` | service `on_message()` and `on_process_input()` hooks |
| `src/iop/components/polling_business_service.py` | polling service `on_poll()` hook |

## Dispatch Quick Reference

For `BusinessProcess` and `BusinessOperation`, IoP dispatches incoming messages
to:

1. a method decorated with `@handler(MessageType)`
2. a typed one-argument method such as `route_order(self, request: OrderRequest)`
3. `on_message(self, request)` as the fallback

Use `@handler(MessageType)` when the handler must be explicit. Use typed
one-argument methods when annotations are enough.

## Message Quick Reference

Use `@dataclass` with regular `Message` classes:

```python
from dataclasses import dataclass
from iop import Message

@dataclass
class OrderRequest(Message):
    order_id: str
```

Use `PydanticMessage` without `@dataclass`. Use `PersistentMessage` only when
IRIS needs a native persistent message body.

## Source-first Rule

When starting from source code, build applications through public imports from
`iop` and a `Production` graph. Do not copy internal runtime classes such as
`_BusinessHost` into application code; use them only to understand behavior.

## settings.py Import Quick Reference

Treat the directory containing `settings.py` as the project import root for
migration. Import the production graph, messages, and components from modules
reachable relative to that file, such as `from production import prod` or
`from myapp.production import prod`.

Do not set `PYTHONPATH`, patch `os.environ["PYTHONPATH"]`, or mutate global
`sys.path` in application code to make migration imports pass. Fix the package
layout or import statements instead.

## Runtime Test Quick Reference

Do not use `iop --test` as the normal way to test Business Services. Test
services through the runtime director or production runtime API so the deployed
production context, component settings, and configured targets are used.

## Healthcare Add-on

If the code or task mentions HL7v2, FHIR, Health Connect, FHIR bundles, MLLP,
or `EnsLib.HL7`, use the healthcare add-on:

- [Healthcare AI-assisted coding](../healthcare-ai-coding.md)
- [HL7v2 native input](hl7v2-native-input.md)
- [HL7v2 to FHIR with fhir-converter](hl7v2-to-fhir-with-fhir-converter.md)
- [FHIR submission with a Python client](fhir-submission-python-client.md)
