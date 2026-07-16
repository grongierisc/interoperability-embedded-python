---
name: build-iop-app
description: Build or modify an IoP application using production graphs, messages, components, tests, and the relevant bundled cookbook. Use for new or changed Business Services, Business Processes, Business Operations, routes, settings, healthcare flows, or complete productions.
---

# Build An IoP Application

Read `references/instructions.md`, then inspect the project README,
`settings.py`, production graph, messages, components, tests, and samples.

## Workflow

1. Establish the business goal, inbound and outbound systems, protocols,
   routing or transformation behavior, runtime constraints, and acceptance
   criteria. Infer repository facts before asking questions.
2. Select and read only the relevant cookbook from `references/cookbooks/`.
   Start with `index.md`; use `code-index.md` when starting from source symbols.
3. Model the flow as messages and a production graph. Keep inbound concerns in
   services, orchestration in processes, and outbound effects in operations.
4. Implement through public `iop` imports. Use `target()` and graph connections
   instead of direct component calls. Use `on_init()`, not `__init__()`, for
   startup.
5. Add focused tests and representative samples for changed behavior.
6. Ensure the migration entrypoint exports the desired production through
   `PRODUCTIONS` and remains safe to import.
7. Run the `validate-iop-app` skill. Do not deploy unless the user explicitly
   requests it.

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
