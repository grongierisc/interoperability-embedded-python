# _manager.py is the main entry point of the pex package
# it's a command line interface to manage productions
# eg :
#   python3 -m iop -h : display help and the default production name
#   python3 -m iop -l : list productions
#   python3 -m iop -d <production_name> : set the default production to <production_name>
#   python3 -m iop -s <production_name> : start a production named <production_name> if <production_name> is not set, the default production is started
#   python3 -m iop -k <production_name> : stop a production named <production_name> if <production_name> is not set, the default production is killed
#   python3 -m iop -r <production_name> : restart a production named <production_name> if <production_name> is not set, the default production is restarted
#   python3 -m iop -m <settings_file> : migrate a production and classes with the settings file <settings_file>
#   python3 -m iop -x <production_name> : export a production named <production_name> if <production_name> is not set, the default production is exported
from iop._director import _Director
from iop._utils import _Utils

import argparse
import json
import os
from importlib.metadata import version 

def parse_args():
    # parse arguments
    main_parser = argparse.ArgumentParser()
    parser = main_parser.add_mutually_exclusive_group()
    parser.add_argument('-d', '--default', help='set the default production', nargs='?', const='not_set')
    parser.add_argument('-l', '--list', help='list productions', action='store_true')
    parser.add_argument('-s', '--start', help='start a production', nargs='?', const='not_set')
    start = main_parser.add_argument_group('start arguments')
    start.add_argument('-D', '--detach', help='start a production in detach mode', action='store_true')
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
    test = main_parser.add_argument_group('test arguments')
    # add classname argument
    test.add_argument('-C', '--classname', help='test classname', nargs='?', const='not_set')
    # body argument
    test.add_argument('-B', '--body', help='test body', nargs='?', const='not_set')
    return main_parser

def main(argv=None):
    # build arguments
    parser = parse_args()
    args = parser.parse_args(argv)

    if args.default:
        # set default production
        if args.default == 'not_set':
            # display default production name
            print(_Director.get_default_production())
        else:
            _Director.set_default_production(args.default)

    elif args.list:
        # display list of productions
        dikt = _Director.list_productions()
        print(json.dumps(dikt, indent=4))

    elif args.start:
        production_name = None
        if args.start == 'not_set':
            # start default production
            production_name = _Director.get_default_production()
        else:
            # start production with name
            production_name = args.start
        if args.detach:
            # start production in detach mode
            _Director.start_production(production_name)
            print(f"Production {production_name} started")
        else:
            _Director.start_production_with_log(production_name)

    elif args.init:
        if args.init == 'not_set':
            # set arg to None
            args.init = None
        _Utils.setup(args.start)

    elif args.kill:
        # kill a production
        _Director.shutdown_production()

    elif args.restart:
        # restart a production
        _Director.restart_production()

    elif args.migrate:
        # check if migrate is absolute path
        if os.path.isabs(args.migrate):
            # migrate a production with absolute path
            _Utils.migrate(args.migrate)
        else:
            # migrate a production with relative path
            _Utils.migrate(os.path.join(os.getcwd(), args.migrate))

    elif args.version:
        # display version
        print(version('iris-pex-embedded-python'))

    elif args.log:
        # display log
        if args.log == 'not_set':
            # display default production log
            _Director.log_production()
        else:
            _Director.log_production_top(args.log)

    elif args.stop:
        # stop a production
        _Director.stop_production()
        print(f"Production {_Director.get_default_production()} stopped")

    elif args.status:
        dikt=_Director.status_production()
        print(json.dumps(dikt, indent=4))

    elif args.test:
        classname = None
        body = None
        if args.test == 'not_set':
            # set arg to None
            args.test = None
        if args.classname:
            classname = args.classname
        if args.body:
            body = args.body
        response = _Director.test_component(args.test, classname=classname, body=body)
        print(response)

    elif args.export:
        if args.export == 'not_set':
            # export default production
            args.export=_Director.get_default_production()

        dikt = _Utils.export_production(args.export)
        print(json.dumps(dikt, indent=4))

    else:
        # display help
        parser.print_help()
        print()
        print("Default production : " + _Director.get_default_production())


if __name__ == '__main__':
    main()
