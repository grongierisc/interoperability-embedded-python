# Ingestion Pipeline Agent Evaluation

## Prompt

```text
create an iop production that fetch the last rated movied from rotten tomatos
and store them in iris using iris-persistence
```

## Hard Gates

- The production graph is `PollingBusinessService -> BusinessProcess ->
  BusinessOperation` with both edges declared through targets.
- The service fetches Rotten Tomatoes and emits fetched movie data.
- The process validates, transforms, deduplicates, or routes movie data.
- The operation performs IRIS persistence and does not fetch Rotten Tomatoes.
- Unit tests cover the service, process, operation, and graph topology.
- Existing Docker initialization, migration, and startup automation is
  preserved and updated for the new production.
- The agent rebuilds and runs the disposable container, confirms the production
  is running with the IoP CLI, exercises the polling flow, and verifies at least
  one persisted movie.
- Standard lifecycle checks use repository scripts or the IoP CLI rather than
  raw ObjectScript commands.

An evaluation fails when any hard gate is absent, even if unit tests and
migration dry-run pass.
