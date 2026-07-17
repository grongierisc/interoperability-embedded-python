# Cookbook: Build A Source-To-Destination Ingestion Pipeline

## When To Use This

Use this cookbook for a complete production that polls or receives data from a
source, applies application logic, and writes or submits it to a destination.
Read the polling-service, business-process, and business-operation cookbooks as
well; this workflow spans all three boundaries.

## Required Architecture

Model the default graph as:

```text
PollingBusinessService -> BusinessProcess -> BusinessOperation
source acquisition        validation,        destination effect
and data message           transform, route   such as persistence
```

- The service performs acquisition from the source it is configured to poll.
  HTTP scraping, file reads, and source-database reads belong here.
- The service emits a data-bearing `Message`, not an empty command asking a
  downstream operation to fetch.
- The process validates, normalizes, transforms, deduplicates, or routes the
  acquired data.
- The operation receives processed data and owns destination effects such as an
  `iris-persistence` write.
- A direct `service -> operation` graph is acceptable only for a genuinely
  trivial pass-through. State the reason when omitting the process.

## Implementation Workflow

1. Inspect the existing graph, dependency manifest, tests, Docker or Compose
   files, initialization entrypoint, and documented run commands.
2. Write down the source, destination, component roles, messages, graph edges,
   and observable end-to-end result.
3. Define typed messages for acquired and processed data.
4. Implement the polling service so `on_poll()` reads the source and sends the
   acquired message through a `target()`.
5. Implement a process with a target for the destination operation. Keep source
   and destination I/O out of its routing and transformation logic.
6. Implement the operation so it performs only the destination effect. For
   persistence, initialize or synchronize the schema through the operation
   lifecycle and write the records received in the message.
7. Register all three components and both edges in `settings.py`.
8. Declare direct third-party dependencies, including `iris-persistence` when
   the application imports it.
9. Preserve the repository's working initialization, migration, production
   startup, and container health lifecycle. Update paths and production names;
   never replace setup with a keep-alive loop.

## Testing

Add focused tests for:

- source response parsing and service message construction;
- process validation, transformation, and routing;
- operation persistence behavior;
- graph nodes and `service -> process -> operation` edges.

For a repository-owned disposable container, unit tests are not completion.
Rebuild and start the environment, migrate and start the production, trigger or
wait for the polling service through the runtime, trace the message flow, and
query an actual destination record.

Prefer repository scripts and these IoP CLI capabilities over raw ObjectScript:

```bash
iop --migrate settings.py --dry-run --strict-production-validation
iop --migrate settings.py
iop --start <production-name> --detach
iop --status
iop --log
iop --queue
```

Use an ObjectScript terminal only when the IoP public API does not expose the
required observation, and state that reason in the verification report.

## Completion Evidence

- Unit tests and strict migration validation pass.
- Container initialization completes without disabling existing setup steps.
- The intended production, not only the IRIS container, is running.
- Runtime evidence shows messages crossing both graph edges.
- The destination contains the expected record or external effect.
- Exact commands, results, skipped checks, and residual risks are reported.

## Common Mistakes

- Emitting an empty message from the service and fetching in the persistence
  operation.
- Omitting the process without considering validation or transformation.
- Mocking both source and destination and calling that end-to-end validation.
- Checking container health without checking production status.
- Removing initialization, migration, or startup commands to keep the container
  alive.
- Using ObjectScript for status or logs when an `iop` command exists.
