from __future__ import annotations

import json
import logging
import os
import sys
from importlib.metadata import version

import requests

from ..migration import utils as migration_utils
from ..runtime.local import _LocalDirector
from ..runtime.protocol import DirectorProtocol
from ..runtime.remote import _RemoteDirector, get_remote_settings
from .formatting import format_test_response
from .parser import create_parser
from .types import CommandArgs, CommandType

_format_test_response = format_test_response


class Command:
    def __init__(self, args: CommandArgs):
        self.args = args

        if self.args.namespace and self.args.namespace != "not_set":
            # set environment variable IRISNAMESPACE
            os.environ["IRISNAMESPACE"] = self.args.namespace

        # Resolve director: remote when IOP_URL / IOP_SETTINGS env vars are set
        # or when the -m settings.py file contains REMOTE_SETTINGS.
        # --force-local overrides everything and always uses the local director.
        if self.args.force_local:
            self.director: DirectorProtocol = _LocalDirector()
            self._is_remote = False
        else:
            # Resolve absolute paths for --remote-settings and -m so
            # get_remote_settings can load them regardless of cwd.
            explicit_path = self.args.remote_settings
            if explicit_path and not os.path.isabs(explicit_path):
                explicit_path = os.path.join(os.getcwd(), explicit_path)

            migrate_path = self.args.migrate
            if migrate_path and not os.path.isabs(migrate_path):
                migrate_path = os.path.join(os.getcwd(), migrate_path)

            remote_settings = get_remote_settings(
                explicit_settings_path=explicit_path,
                fallback_settings_path=migrate_path,
            )
            if remote_settings:
                if self.args.namespace and self.args.namespace != "not_set":
                    remote_settings["namespace"] = self.args.namespace
                self.director = _RemoteDirector(remote_settings)
                self._is_remote = True
            else:
                self.director = _LocalDirector()
                self._is_remote = False

    def _has_primary_command(self) -> bool:
        return any(
            [
                self.args.default,
                self.args.list,
                self.args.start,
                self.args.stop,
                self.args.kill,
                self.args.restart,
                self.args.status,
                self.args.test,
                self.args.version,
                self.args.export,
                self.args.migrate,
                self.args.log,
                self.args.queue,
                self.args.init,
                self.args.update,
            ]
        )

    def execute(self) -> None:
        if self.args.namespace == "not_set" and not self._has_primary_command():
            print(os.getenv("IRISNAMESPACE", "not set"))
            return

        command_type = self._determine_command_type()
        command_handlers = {
            CommandType.DEFAULT: self._handle_default,
            CommandType.LIST: self._handle_list,
            CommandType.START: self._handle_start,
            CommandType.STOP: self._handle_stop,
            CommandType.KILL: self._handle_kill,
            CommandType.RESTART: self._handle_restart,
            CommandType.STATUS: self._handle_status,
            CommandType.TEST: self._handle_test,
            CommandType.VERSION: self._handle_version,
            CommandType.EXPORT: self._handle_export,
            CommandType.MIGRATE: self._handle_migrate,
            CommandType.LOG: self._handle_log,
            CommandType.QUEUE: self._handle_queue,
            CommandType.INIT: self._handle_init,
            CommandType.HELP: self._handle_help,
            CommandType.UPDATE: self._handle_update,
        }
        handler = command_handlers.get(command_type)
        if handler:
            handler()

    def _determine_command_type(self) -> CommandType:
        if self.args.default:
            return CommandType.DEFAULT
        if self.args.list:
            return CommandType.LIST
        if self.args.start:
            return CommandType.START
        if self.args.stop:
            return CommandType.STOP
        if self.args.kill:
            return CommandType.KILL
        if self.args.restart:
            return CommandType.RESTART
        if self.args.status:
            return CommandType.STATUS
        if self.args.test:
            return CommandType.TEST
        if self.args.version:
            return CommandType.VERSION
        if self.args.export:
            return CommandType.EXPORT
        if self.args.migrate:
            return CommandType.MIGRATE
        if self.args.log:
            return CommandType.LOG
        if self.args.queue:
            return CommandType.QUEUE
        if self.args.init:
            return CommandType.INIT
        if self.args.update:
            return CommandType.UPDATE
        return CommandType.HELP

    def _handle_default(self) -> None:
        if self.args.default == "not_set":
            print(self.director.get_default_production())
        elif self.args.default is not None:
            self.director.set_default_production(self.args.default)

    def _handle_list(self) -> None:
        dikt = self.director.list_productions()
        print(json.dumps(dikt, indent=4))

    def _handle_start(self) -> None:
        if self.args.start != "not_set":
            production_name = self.args.start
        else:
            production_name = self.director.get_default_production()
            if not production_name or production_name == "Not defined":
                print(
                    "Error: no production name provided and no default production is defined.",
                    file=sys.stderr,
                )
                sys.exit(1)
        if self.args.detach:
            self.director.start_production(production_name)
            print(f"Production {production_name} started")
        else:
            self.director.start_production_with_log(production_name)

    def _handle_stop(self) -> None:
        self.director.stop_production()
        print(f"Production {self.director.get_default_production()} stopped")

    def _handle_kill(self) -> None:
        self.director.shutdown_production()

    def _handle_restart(self) -> None:
        self.director.restart_production()

    def _handle_status(self) -> None:
        print(json.dumps(self.director.status_production(), indent=4))

    def _handle_update(self) -> None:
        self.director.update_production()

    def _handle_test(self) -> None:
        test_name = None if self.args.test == "not_set" else self.args.test
        classname = self.args.classname if self.args.classname != "not_set" else None
        body = self.args.body if self.args.body != "not_set" else None

        # Support @filename.json body expansion
        if body and body.startswith("@"):
            filepath = body[1:]
            if not os.path.isabs(filepath):
                filepath = os.path.join(os.getcwd(), filepath)
            with open(filepath, encoding="utf-8") as fh:
                body = fh.read()

        response = self.director.test_component(
            test_name, classname=classname, body=body
        )
        print(format_test_response(response))

    def _handle_version(self) -> None:
        print(version("iris-pex-embedded-python"))

    def _handle_export(self) -> None:
        export_name = (
            self.director.get_default_production()
            if self.args.export == "not_set"
            else self.args.export
        )
        print(json.dumps(self.director.export_production(export_name), indent=4))

    def _handle_migrate(self) -> None:
        migrate_path = self.args.migrate
        if migrate_path is not None:
            if not os.path.isabs(migrate_path):
                migrate_path = os.path.join(os.getcwd(), migrate_path)
            mode = "REMOTE" if self._is_remote else "LOCAL"
            if self.args.migration_plan:
                print(
                    migration_utils.explain_migration(
                        migrate_path, mode=mode, namespace=self.director.namespace
                    )
                )
                return
            if self._is_remote:
                print(
                    migration_utils.explain_migration(
                        migrate_path, mode=mode, namespace=self.director.namespace
                    )
                )
            self.director.migrate(migrate_path)
            if self._is_remote:
                print(
                    migration_utils.format_migration_success(
                        migrate_path, namespace=self.director.namespace
                    )
                )

    def _handle_log(self) -> None:
        if self.args.log == "not_set":
            self.director.log_production()
        elif self.args.log is not None:
            self.director.log_production_top(int(self.args.log))

    def _handle_queue(self) -> None:
        production_name = (
            self.director.get_default_production()
            if self.args.queue == "not_set"
            else self.args.queue
        )
        if not production_name or production_name == "Not defined":
            print(
                "Error: no production name provided and no default production is defined.",
                file=sys.stderr,
            )
            sys.exit(1)
        print(
            json.dumps(
                self.director.export_production_queue_info(production_name),
                indent=4,
            )
        )

    def _handle_init(self) -> None:
        path = None if self.args.init == "not_set" else self.args.init
        self.director.setup(path)

    def _handle_help(self) -> None:
        create_parser().print_help()
        if self._is_remote:
            print(f"\nMode: REMOTE ({os.environ.get('IOP_URL', 'via IOP_SETTINGS')})")
        try:
            print(f"\nDefault production: {self.director.get_default_production()}")
            print(f"\nNamespace: {self.director.namespace}")
        except Exception:
            logging.warning("Could not retrieve default production.")


def main(argv=None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)
    cmd_args = CommandArgs(**vars(args))

    try:
        command = Command(cmd_args)
        command.execute()
    except requests.exceptions.ConnectionError as exc:
        url = os.environ.get("IOP_URL", "")
        msg = (
            f"Connection error: could not reach {url!r}"
            if url
            else f"Connection error: {exc}"
        )
        print(f"Error: {msg}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.HTTPError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)


if __name__ == "__main__":
    main()
