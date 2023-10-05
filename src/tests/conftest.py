import sys
from os.path import dirname as d
from os.path import abspath, join
root_dir = d(d(abspath(__file__)))
sys.path.append(root_dir)
# add registerFiles to the path
sys.path.append(join(join(root_dir, 'tests'), 'registerFiles'))

from grongier.pex import Utils

Utils.setup()