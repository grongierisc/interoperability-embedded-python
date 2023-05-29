# _manager.py is the main entry point of the pex package
# it's a command line interface to manage productions
# eg :
#   python3 -m grongier.pex -h : display help and the default production name
#   python3 -m grongier.pex -l : list productions
#   python3 -m grongier.pex -d <production_name> : set the default production to <production_name>
#   python3 -m grongier.pex -s <production_name> : start a production named <production_name> if <production_name> is not set, the default production is started
#   python3 -m grongier.pex -k <production_name> : stop a production named <production_name> if <production_name> is not set, the default production is killed
#   python3 -m grongier.pex -r <production_name> : restart a production named <production_name> if <production_name> is not set, the default production is restarted
#   python3 -m grongier.pex -m <settings_file> : migrate a production and classes with the settings file <settings_file>
#   python3 -m grongier.pex -x <production_name> : export a production named <production_name> if <production_name> is not set, the default production is exported
from grongier.pex._director import _Director
from grongier.pex._utils import _Utils

import argparse
import sys

def parse_args(argv):
    # parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--default', help='set the default production', nargs='?', const='not_given')
    parser.add_argument('-l', '--lists', help='list productions', action='store_true')
    parser.add_argument('-s', '--start', help='start a production')
    parser.add_argument('-k', '--kill', help='kill a production')
    parser.add_argument('-r', '--restart', help='restart a production')
    parser.add_argument('-m', '--migrate', help='migrate production and classes with settings file')
    parser.add_argument('-x', '--export', help='export a production')
    return parser.parse_args(argv)

def main(argv=None):
    # build arguments
    args = parse_args(argv)
    if args.default:
        if args.default == 'not_given':
            # display default production name
            print(_Director.get_default_production())
        else:
            # set default production
            _Director.set_default_production(args.default)
    else:
        # display help and default production name
        print("usage: python3 -m grongier.pex [-h] [-d DEFAULT] [-l] [-s START] [-k KILL] [-r RESTART] [-m MIGRATE] [-x EXPORT]")
        print("optional arguments:")
        print("  -h, --help            display help and default production name")
        print("  -d DEFAULT, --default DEFAULT")
        print("                        set the default production")
        print("  -l, --lists           list productions")
        print("  -s START, --start START")
        print("                        start a production")
        print("  -k KILL, --kill KILL  kill a production")
        print("  -r RESTART, --restart RESTART")
        print("                        restart a production")
        print("  -m MIGRATE, --migrate MIGRATE")
        print("                        migrate production and classes with settings file")
        print("  -x EXPORT, --export EXPORT")
        print("                        export a production")
        print("default production: " + _Director.get_default_production())


if __name__ == '__main__':
    main()
