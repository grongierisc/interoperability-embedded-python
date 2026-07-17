# IoP Validation Reference

Run local tests before IRIS-backed checks. Strict migration dry-run imports the
settings file, validates production objects and settings, and prints the
migration plan without writing to IRIS.

Live migration, production start or stop, plan application, and rollback are
mutating operations. Run them against a repository-owned disposable container
when it is the project's documented validation environment. Require explicit
user intent before mutating a shared, remote, or otherwise non-disposable IRIS
environment.

For Business Services, test through the runtime director or production API.
This preserves the deployed production context, settings, schedules, and
configured targets.

## Container-Backed Validation

When `Dockerfile`, `docker-compose.yml`, or `compose.yaml` is present:

1. Read the repository instructions and existing entrypoint before changing or
   running it.
2. Rebuild and start the disposable environment using the repository's command,
   commonly `docker compose up --build -d`.
3. Confirm initialization, migration, and production startup completed. Do not
   accept a healthy IRIS container as proof that the production is running.
4. Use `iop --status`, `iop --log`, and `iop --queue` before reaching for an
   ObjectScript session.
5. Trigger or wait for the service through the production runtime and verify a
   message crosses every expected edge.
6. Inspect the destination effect, such as an actual persisted row. Mock-only
   unit tests do not satisfy end-to-end validation.

If credentials, network access, licensing, or an unavailable external system
blocks runtime validation, keep the container lifecycle intact and report the
specific skipped check and residual risk.
