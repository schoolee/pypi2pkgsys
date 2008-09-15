#!/usr/bin/python
# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
# License: BSD

import os.path
import shutil
import sys
from pkg_resources import Distribution
from pypi2pkgsys.package_system import package_system
from pypi2pkgsys.pypi_objects import pypicache

if len(sys.argv) < 4:
    print 'Usage: %s CACHE_ROOT CACHE_URL FILENAME,DISTNAME ...' % sys.argv[0]
    sys.exit(-1)

cacheroot = sys.argv[1]
cacheurl = sys.argv[2]
downloads = os.path.join(cacheroot, 'downloads')
distlist = []
for arg in sys.argv[3:]:
    filename, distname = arg.split(',')
    dlfname = os.path.join(downloads, os.path.basename(filename))
    print 'Copy %s %s ...' % (filename, dlfname)
    shutil.copyfile(filename, dlfname)
    dist = Distribution(dlfname, None, project_name = distname)
    distlist.append(dist)
cache = pypicache(package_system(), cacheroot, cacheurl)
cache.add_packages(distlist)
del(cache)
