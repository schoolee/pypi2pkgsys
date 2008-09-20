#!/usr/bin/env python
# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
"""Generate ebuilds for the selected PyPI packages, so they can be emerged
but not easy_installed in Gentoo."""

import glob
import os.path
from setuptools import setup, find_packages

version = '0.0.7'

long_desc = \
    """Generate package files from PyPI index.

Now only ebuild for gentoo is generated. spec for rpm-base distribution,
dpkg for dpkg-base distribution will be added in future.

Many features are provided:
* Pre-defined, user-defined schemes for different usage.
  * Update from PyPI and cached into localhost scheme is provided.
  * Update from localhost scheme is provided, so the package file will not have to be downloaded again and again.
* Wildcard is permitted in package names. For example: [Aa]*.
* Full automatically log, all passed or failed packages(with reason) are recorded in log.
* Some packages can be masked for manually written ebuild.
* Multiple template support, to support different packages types. Now only standard distutils/setuptools template and single python template are provided. More template, such as webapp, will be added in future.
* Package specific config, patches supported. User can manage their private config, patches in /etc/pypi2pkgsys too.
* pypi-logstats.py is provided to show the statistics from log files.
* pypi-manualcache.py is provided to generate localhost cache entries from self-downloaded package files. This reserve a great deal of time to download big files from pypi.python.org.

Links:
* News: http://code.google.com/p/pypi2pkgsys/wiki/News
* Main: http://code.google.com/p/pypi2pkgsys/wiki/Main
* Usage:
  * http://code.google.com/p/pypi2pkgsys/wiki/Usage_pypi2portage
  * http://code.google.com/p/pypi2pkgsys/wiki/Usage_logstats
  * http://code.google.com/p/pypi2pkgsys/wiki/Usage_manualcache
"""

setup(name = 'pypi2pkgsys',
      version = version,
      description = 'Generate package files(gentoo ebuild) from PyPI index.',
      long_description = long_desc,
      keywords = 'PyPI distutils setuptools package management',
      license = 'BSD',
      author = 'Charles Wang',
      author_email = 'charlesw123456@gmail.com',
      url = 'http://code.google.com/p/pypi2pkgsys/',
      packages = find_packages(),
      scripts = map(lambda s: os.path.join('scripts', s),
                    ['pypi2portage', 'pypi2dpkg', 'pypi2rpm']) + \
          glob.glob(os.path.join('scripts', '*.py')),
      package_data = { 'pypi2pkgsys' : \
                           [os.path.join('patches', 'index.ini'),
                            os.path.join('patches', 'pypi2pkgsys.log'),
                            os.path.join('patches', '*.patch'),
                            os.path.join('portage', '*.tmpl')] },
      zip_safe = False,
      install_requires = ['setuptools>=0.6c8'],
      classifiers = ['Development Status :: 3 - Alpha',
                     'Intended Audience :: System Administrators',
                     'License :: OSI Approved :: BSD License',
                     'Operating System :: OS Independent',
                     'Programming Language :: Python',
                     'Topic :: System :: Archiving :: Packaging',
                     'Topic :: System :: Systems Administration',
                     'Topic :: Utilities'],
      entry_points = {
        'distutils.commands' : [
            'dump = pypi2pkgsys.dump:dump'
            ] }
)
