# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
# License: BSD

import os.path
from ConfigParser import ConfigParser

pkgroot = os.path.dirname(__file__)
patchdir = os.path.join(pkgroot, 'patches')
config = ConfigParser()
config.read(os.path.join(patchdir, 'index.ini'))
