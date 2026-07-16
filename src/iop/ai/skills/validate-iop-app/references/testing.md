# IoP Validation Reference

Run local tests before IRIS-backed checks. Strict migration dry-run imports the
settings file, validates production objects and settings, and prints the
migration plan without writing to IRIS.

Live migration, production start or stop, plan application, and rollback are
mutating operations. Run them only against an identified environment and when
the user requests runtime verification.

For Business Services, test through the runtime director or production API.
This preserves the deployed production context, settings, schedules, and
configured targets.
