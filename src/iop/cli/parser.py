from __future__ import annotations

import argparse


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the IOP CLI parser."""
    main_parser = argparse.ArgumentParser(
        epilog=(
            "Remote mode: set IOP_URL (e.g. http://localhost:8080) to run all commands\n"
            "against a remote IRIS instance via its REST API. Optional env vars:\n"
            "  IOP_USERNAME, IOP_PASSWORD, IOP_NAMESPACE (default: USER),\n"
            "  IOP_VERIFY_SSL (set to 0 to disable TLS verification).\n"
            "Alternatively use -R /path/to/settings.py or set IOP_SETTINGS=\n"
            "(file must contain a REMOTE_SETTINGS dict with at least 'url').\n"
            "Use --force-local to suppress remote mode entirely."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser = main_parser.add_mutually_exclusive_group()

    parser.add_argument(
        "-d", "--default", help="set the default production", nargs="?", const="not_set"
    )
    parser.add_argument("-l", "--list", help="list productions", action="store_true")
    parser.add_argument(
        "-s", "--start", help="start a production", nargs="?", const="not_set"
    )
    parser.add_argument("-S", "--stop", help="stop a production", action="store_true")
    parser.add_argument("-k", "--kill", help="kill a production", action="store_true")
    parser.add_argument("-r", "--restart", help="restart a production", action="store_true")
    parser.add_argument("-x", "--status", help="status a production", action="store_true")
    parser.add_argument(
        "-m",
        "-M",
        "--migrate",
        help="migrate production and classes with a Python migration file",
    )
    parser.add_argument(
        "-e", "--export", help="export a production", nargs="?", const="not_set"
    )
    parser.add_argument("-v", "--version", help="display version", action="store_true")
    parser.add_argument("-L", "--log", help="display log", nargs="?", const="not_set")
    parser.add_argument(
        "-q",
        "--queue",
        help="display runtime queue information",
        nargs="?",
        const="not_set",
    )
    parser.add_argument(
        "-i", "--init", help="init the iop module in iris", nargs="?", const="not_set"
    )
    parser.add_argument(
        "-t", "--test", help="test the iop module in iris", nargs="?", const="not_set"
    )
    parser.add_argument("-u", "--update", help="update a production", action="store_true")

    start = main_parser.add_argument_group("start arguments")
    start.add_argument(
        "-D", "--detach", help="start a production in detach mode", action="store_true"
    )

    test = main_parser.add_argument_group("test arguments")
    test.add_argument(
        "-C", "--classname", help="test classname", nargs="?", const="not_set"
    )
    test.add_argument(
        "-B",
        "--body",
        help="test body (JSON string or @path/to/file.json)",
        nargs="?",
        const="not_set",
    )

    migrate = main_parser.add_argument_group("migrate arguments")
    migrate.add_argument(
        "--force-local",
        help="force local mode, skip remote even if REMOTE_SETTINGS or IOP_URL is present",
        action="store_true",
    )
    migrate.add_argument(
        "--dry-run",
        "--explain",
        dest="migration_plan",
        help="show the migration plan and validation messages without writing to IRIS",
        action="store_true",
    )

    remote = main_parser.add_argument_group("remote arguments")
    remote.add_argument(
        "-R",
        "--remote-settings",
        help="path to a settings.py containing REMOTE_SETTINGS (overrides IOP_SETTINGS env var)",
        metavar="FILE",
    )

    namespace = main_parser.add_argument_group("namespace arguments")
    namespace.add_argument(
        "-n", "--namespace", help="set namespace", nargs="?", const="not_set"
    )

    return main_parser
