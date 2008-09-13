#!/usr/bin/env python
# Copyright (C) 2008, Charles Wang <charlesw1234@163.com>
# Author: Charles Wang <charlesw1234@163.com>
"""Generate ebuilds for the selected PyPI packages, so they can be emerged
but not easy_installed in Gentoo."""

import glob
import os.path
from setuptools import setup, find_packages

version = '0.0.5'

setup(name = 'pypi2pkgsys',
      version = version,
      description = 'Generate package files(gentoo ebuild) for selected PyPI packages',
      long_description = """Generate package files from the selected PyPI packages.

Now only ebuild for gentoo is generated. spec for rpm-base distribution,
dpkg for dpkg-base distribution will be added in future.

* News: http://code.google.com/p/pypi2pkgsys/wiki/News
* Main: http://code.google.com/p/pypi2pkgsys/wiki/Main
* Usage: http://code.google.com/p/pypi2pkgsys/wiki/Usage
""",
      keywords = 'PyPI distutils setuptools package management',
      license = 'BSD',
      author = 'Charles Wang',
      author_email = 'charlesw1234@163.com',
      url = 'http://code.google.com/p/pypi2pkgsys/',
      packages = find_packages(),
      scripts = map(lambda s: os.path.join('scripts', s),
                    ['pypi2portage', 'pypi2rpm', 'pypi2dpkg']),
      package_data = { 'pypi2pkgsys' : \
                           [os.path.join('patches', 'index.ini'),
                            os.path.join('patches', 'broken.txt'),
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
