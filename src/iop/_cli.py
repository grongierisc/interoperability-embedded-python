from __future__ import annotations
import argparse
import json
import logging
import os
from dataclasses import dataclass
from enum import Enum, auto
import sys
from typing import Optional
from importlib.metadata import version

from ._local import _LocalDirector
from ._remote import _RemoteDirector, get_remote_settings
from ._director_protocol import DirectorProtocol
from ._utils import _Utils


class CommandType(Enum):
    DEFAULT = auto()
    LIST = auto()
    START = auto()
    STOP = auto()
    KILL = auto()
    RESTART = auto()
    STATUS = auto()
    TEST = auto()
    VERSION = auto()
    EXPORT = auto()
    MIGRATE = auto()
    LOG = auto()
    INIT = auto()
    HELP = auto()
    UPDATE = auto()

@dataclass
class CommandArgs:
    """Container for parsed command arguments"""
    default: Optional[str] = None
    list: bool = False
    start: Optional[str] = None
    detach: bool = False
    stop: bool = False
    kill: bool = False
    restart: bool = False
    status: bool = False
    migrate: Optional[str] = None
    export: Optional[str] = None
    version: bool = False
    log: Optional[str] = None
    init: Optional[str] = None
    test: Optional[str] = None
    classname: Optional[str] = None
    body: Optional[str] = None
    namespace: Optional[str] = None
    force_local: bool = False
    remote_settings: Optional[str] = None
    update: bool = False

class Command:
    def __init__(self, args: CommandArgs):
        self.args = args

        if self.args.namespace and self.args.namespace != 'not_set':
            # set environment variable IRISNAMESPACE
            os.environ['IRISNAMESPACE'] = self.args.namespace

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
                if self.args.namespace and self.args.namespace != 'not_set':
                    remote_settings['namespace'] = self.args.namespace
                self.director = _RemoteDirector(remote_settings)
                self._is_remote = True
            else:
                self.director = _LocalDirector()
                self._is_remote = False

    def _has_primary_command(self) -> bool:
        return any([
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
            self.args.init,
            self.args.update,
        ])

    def execute(self) -> None:
        if self.args.namespace == 'not_set' and not self._has_primary_command():
            print(os.getenv('IRISNAMESPACE', 'not set'))
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
            CommandType.INIT: self._handle_init,
            CommandType.HELP: self._handle_help,
            CommandType.UPDATE: self._handle_update,
        }
        handler = command_handlers.get(command_type)
        if handler:
            handler()

    def _determine_command_type(self) -> CommandType:
        if self.args.default: return CommandType.DEFAULT
        if self.args.list: return CommandType.LIST
        if self.args.start: return CommandType.START
        if self.args.stop: return CommandType.STOP
        if self.args.kill: return CommandType.KILL
        if self.args.restart: return CommandType.RESTART
        if self.args.status: return CommandType.STATUS
        if self.args.test: return CommandType.TEST
        if self.args.version: return CommandType.VERSION
        if self.args.export: return CommandType.EXPORT
        if self.args.migrate: return CommandType.MIGRATE
        if self.args.log: return CommandType.LOG
        if self.args.init: return CommandType.INIT
        if self.args.update: return CommandType.UPDATE
        return CommandType.HELP

    def _handle_default(self) -> None:
        if self.args.default == 'not_set':
            print(self.director.get_default_production())
        elif self.args.default is not None:
            self.director.set_default_production(self.args.default)

    def _handle_list(self) -> None:
        dikt = self.director.list_productions()
        print(json.dumps(dikt, indent=4))

    def _handle_start(self) -> None:
        if self.args.start != 'not_set':
            production_name = self.args.start
        else:
            production_name = self.director.get_default_production()
            if not production_name or production_name == "Not defined":
                print("Error: no production name provided and no default production is defined.", file=sys.stderr)
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
        test_name = None if self.args.test == 'not_set' else self.args.test
        classname = self.args.classname if self.args.classname != 'not_set' else None
        body = self.args.body if self.args.body != 'not_set' else None

        # Support @filename.json body expansion
        if body and body.startswith('@'):
            filepath = body[1:]
            if not os.path.isabs(filepath):
                filepath = os.path.join(os.getcwd(), filepath)
            with open(filepath, 'r', encoding='utf-8') as fh:
                body = fh.read()

        response = self.director.test_component(
            test_name, classname=classname, body=body
        )
        print(_format_test_response(response))

    def _handle_version(self) -> None:
        print(version('iris-pex-embedded-python'))

    def _handle_export(self) -> None:
        export_name = self.director.get_default_production() if self.args.export == 'not_set' else self.args.export
        print(json.dumps(self.director.export_production(export_name), indent=4))

    def _handle_migrate(self) -> None:
        migrate_path = self.args.migrate
        if migrate_path is not None:
            if not os.path.isabs(migrate_path):
                migrate_path = os.path.join(os.getcwd(), migrate_path)
            _Utils.migrate_remote(migrate_path, force_local=self.args.force_local)

    def _handle_log(self) -> None:
        if self.args.log == 'not_set':
            self.director.log_production()
        elif self.args.log is not None:
            self.director.log_production_top(int(self.args.log))

    def _handle_init(self) -> None:
        if self._is_remote:
            logging.warning("'init' is a local-only command and cannot be run remotely.")
            return
        _Utils.setup(None)

    def _handle_help(self) -> None:
        create_parser().print_help()
        if self._is_remote:
            print(f"\nMode: REMOTE ({os.environ.get('IOP_URL', 'via IOP_SETTINGS')})")
        try:
            print(f"\nDefault production: {self.director.get_default_production()}")
            ns = (self.director._namespace  # type: ignore[union-attr]
                  if self._is_remote else os.getenv('IRISNAMESPACE', 'not set'))
            print(f"\nNamespace: {ns}")
        except Exception:
            logging.warning("Could not retrieve default production.")

def _format_test_response(response) -> str:
    """Pretty-print any test_component() return value.

    Handles three cases:
    - dict  : remote response with ``classname`` / ``body`` keys
    - str   : local response in ``"ClassName : {json}"`` format
    - other : Python dataclass / object returned by the local director
    """
    if isinstance(response, dict):
        parts = []
        if response.get("error"):
            return f"Error: {response['error']}"
        if response.get("classname"):
            parts.append(f"classname: {response['classname']}")
        body = response.get("body", "")
        if body:
            try:
                parsed = json.loads(body)
                parts.append("body:\n" + json.dumps(parsed, indent=4))
            except (json.JSONDecodeError, TypeError):
                parts.append(f"body: {body}")
        if response.get("truncated"):
            parts.append("(response body was truncated)")
        return "\n".join(parts) if parts else str(response)

    if isinstance(response, str):
        # Try to detect the "ClassName : {json_body}" pattern from local mode
        if " : " in response:
            classname_part, _, body_part = response.partition(" : ")
            try:
                parsed = json.loads(body_part)
                return (
                    f"classname: {classname_part.strip()}\n"
                    f"body:\n{json.dumps(parsed, indent=4)}"
                )
            except (json.JSONDecodeError, TypeError):
                pass
        # Plain string — try JSON pretty-print
        try:
            return json.dumps(json.loads(response), indent=4)
        except (json.JSONDecodeError, TypeError):
            return response

    # Python dataclass / arbitrary object
    try:
        import dataclasses
        if dataclasses.is_dataclass(response):
            return json.dumps(dataclasses.asdict(response), indent=4)
    except Exception:
        pass
    return str(response)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
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
    
    # Main commands
    parser.add_argument('-d', '--default', help='set the default production', nargs='?', const='not_set')
    parser.add_argument('-l', '--list', help='list productions', action='store_true')
    parser.add_argument('-s', '--start', help='start a production', nargs='?', const='not_set')
    parser.add_argument('-S', '--stop', help='stop a production', action='store_true')
    parser.add_argument('-k', '--kill', help='kill a production', action='store_true')
    parser.add_argument('-r', '--restart', help='restart a production', action='store_true')
    parser.add_argument('-x', '--status', help='status a production', action='store_true')
    parser.add_argument('-m', '-M', '--migrate', help='migrate production and classes with settings file')
    parser.add_argument('-e', '--export', help='export a production', nargs='?', const='not_set')
    parser.add_argument('-v', '--version', help='display version', action='store_true')
    parser.add_argument('-L', '--log', help='display log', nargs='?', const='not_set')
    parser.add_argument('-i', '--init', help='init the pex module in iris', nargs='?', const='not_set')
    parser.add_argument('-t', '--test', help='test the pex module in iris', nargs='?', const='not_set')
    parser.add_argument('-u', '--update', help='update a production', action='store_true')

    # Command groups
    start = main_parser.add_argument_group('start arguments')
    start.add_argument('-D', '--detach', help='start a production in detach mode', action='store_true')
    
    test = main_parser.add_argument_group('test arguments')
    test.add_argument('-C', '--classname', help='test classname', nargs='?', const='not_set')
    test.add_argument('-B', '--body', help='test body (JSON string or @path/to/file.json)', nargs='?', const='not_set')

    migrate = main_parser.add_argument_group('migrate arguments')
    migrate.add_argument('--force-local', help='force local mode, skip remote even if REMOTE_SETTINGS or IOP_URL is present', action='store_true')

    remote = main_parser.add_argument_group('remote arguments')
    remote.add_argument('-R', '--remote-settings', help='path to a settings.py containing REMOTE_SETTINGS (overrides IOP_SETTINGS env var)', metavar='FILE')

    namespace = main_parser.add_argument_group('namespace arguments')
    namespace.add_argument('-n', '--namespace', help='set namespace', nargs='?', const='not_set')
    
    return main_parser

def main(argv=None) -> None:
    import requests as _requests
    parser = create_parser()
    args = parser.parse_args(argv)
    cmd_args = CommandArgs(**vars(args))

    try:
        command = Command(cmd_args)
        command.execute()
    except _requests.exceptions.ConnectionError as exc:
        url = os.environ.get("IOP_URL", "")
        msg = f"Connection error: could not reach {url!r}" if url else f"Connection error: {exc}"
        print(f"Error: {msg}", file=sys.stderr)
        sys.exit(1)
    except _requests.exceptions.HTTPError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    sys.exit(0)

if __name__ == '__main__':
    main()
