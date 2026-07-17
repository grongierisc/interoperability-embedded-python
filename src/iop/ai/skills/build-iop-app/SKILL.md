---
name: build-iop-app
description: Build or modify an IoP application using production graphs, messages, components, tests, and all applicable bundled cookbooks. Use for new or changed Business Services, Business Processes, Business Operations, routes, settings, healthcare flows, or complete productions.
---

# Build An IoP Application

Read `references/instructions.md`, then inspect the project README,
`settings.py`, production graph, messages, components, tests, samples,
dependency manifests, and Docker or Compose lifecycle files.

## Workflow

1. Establish the business goal, inbound and outbound systems, protocols,
   routing or transformation behavior, runtime constraints, and acceptance
   criteria. Infer repository facts before asking questions.
2. Start with `references/cookbooks/index.md` and read every cookbook implicated
   by the requested flow. Complete ingestion work normally requires the
   ingestion-pipeline, polling-service, process, and operation cookbooks. Use
   `code-index.md` when starting from source symbols.
3. Write a short component-role plan before coding: identify the source
   acquisition service, orchestration process, destination operations, messages,
   and graph edges. A polling service fetches from its configured source and
   emits data; a process validates, transforms, and routes it; an operation
   performs persistence or another destination effect. Model complete ingestion
   as `service -> process -> operation` unless a trivial pass-through is
   explicitly justified.
4. Implement through public `iop` imports. Use `target()` and graph connections
   instead of direct component calls. Use `on_init()`, not `__init__()`, for
   startup.
5. Add focused tests and representative samples for each component boundary and
   the production topology. Declare every directly imported third-party package
   in the project's dependency manifest.
6. Ensure the migration entrypoint exports the desired production through
   `PRODUCTIONS` and remains safe to import. Preserve existing container
   initialization, migration, health, and startup automation; update production
   paths and names instead of disabling that lifecycle.
7. Run the `validate-iop-app` skill. Do not deploy unless the user explicitly
   requests it. A repository-owned disposable container is a validation
   environment, not a shared deployment.

For healthcare work, prefer native IRIS or Health Connect standards and
transport components. Use the healthcare cookbooks for HL7v2 and FHIR choices.

For an existing shared production, read the production change workflow and use
plan/review/apply/verify instead of assuming the Python graph is a complete
deployed-state replacement.

## References

- Core IoP rules: `references/instructions.md`
- Task workflows: `references/cookbooks/index.md`
- Existing production safety: `references/production-change-workflow.md`
- Healthcare design: `references/healthcare-ai-coding.md`
