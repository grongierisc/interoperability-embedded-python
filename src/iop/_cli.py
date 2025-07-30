from __future__ import annotations
import argparse
import json
import os
from dataclasses import dataclass
from enum import Enum, auto
import sys
from typing import Optional, Callable
from importlib.metadata import version

from ._director import _Director
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

class Command:
    def __init__(self, args: CommandArgs):
        self.args = args

        if self.args.namespace and self.args.namespace != 'not_set':
            # set environment variable IRISNAMESPACE
            os.environ['IRISNAMESPACE'] = self.args.namespace

    def execute(self) -> None:
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
            CommandType.HELP: self._handle_help
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
        return CommandType.HELP

    def _handle_default(self) -> None:
        if self.args.default == 'not_set':
            print(_Director.get_default_production())
        elif self.args.default is not None:
            _Director.set_default_production(self.args.default)

    def _handle_list(self) -> None:
        dikt = _Director.list_productions()
        print(json.dumps(dikt, indent=4))

    def _handle_start(self) -> None:
        production_name = self.args.start if self.args.start != 'not_set' else _Director.get_default_production()
        if self.args.detach:
            _Director.start_production(production_name)
            print(f"Production {production_name} started")
        else:
            _Director.start_production_with_log(production_name)

    def _handle_stop(self) -> None:
        _Director.stop_production()
        print(f"Production {_Director.get_default_production()} stopped")

    def _handle_kill(self) -> None:
        _Director.shutdown_production()

    def _handle_restart(self) -> None:
        _Director.restart_production()

    def _handle_status(self) -> None:
        print(json.dumps(_Director.status_production(), indent=4))

    def _handle_test(self) -> None:
        test_name = None if self.args.test == 'not_set' else self.args.test
        response = _Director.test_component(
            test_name,
            classname=self.args.classname if self.args.classname != 'not_set' else None,
            body=self.args.body if self.args.body != 'not_set' else None
        )
        print(response)

    def _handle_version(self) -> None:
        print(version('iris-pex-embedded-python'))

    def _handle_export(self) -> None:
        export_name = _Director.get_default_production() if self.args.export == 'not_set' else self.args.export
        print(json.dumps(_Utils.export_production(export_name), indent=4))

    def _handle_migrate(self) -> None:
        migrate_path = self.args.migrate
        if migrate_path is not None:
            if not os.path.isabs(migrate_path):
                migrate_path = os.path.join(os.getcwd(), migrate_path)
            _Utils.migrate_remote(migrate_path)

    def _handle_log(self) -> None:
        if self.args.log == 'not_set':
            print(_Director.log_production())
        elif self.args.log is not None:
            print(_Director.log_production_top(int(self.args.log)))

    def _handle_init(self) -> None:
        _Utils.setup(None)

    def _handle_help(self) -> None:
        create_parser().print_help()
        print(f"\nDefault production: {_Director.get_default_production()}")

def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser"""
    main_parser = argparse.ArgumentParser()
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

    # Command groups
    start = main_parser.add_argument_group('start arguments')
    start.add_argument('-D', '--detach', help='start a production in detach mode', action='store_true')
    
    test = main_parser.add_argument_group('test arguments')
    test.add_argument('-C', '--classname', help='test classname', nargs='?', const='not_set')
    test.add_argument('-B', '--body', help='test body', nargs='?', const='not_set')

    namespace = main_parser.add_argument_group('namespace arguments')
    namespace.add_argument('-n', '--namespace', help='set namespace', nargs='?', const='not_set')
    
    return main_parser

def main(argv=None) -> None:
    parser = create_parser()
    args = parser.parse_args(argv)
    cmd_args = CommandArgs(**vars(args))
    
    command = Command(cmd_args)
    command.execute()
    sys.exit(0)

if __name__ == '__main__':
    main()
