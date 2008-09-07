# Copyright (C) 2008, Charles Wang <charlesw1234@163.com>
# Author: Charles Wang <charlesw1234@163.com>

import os
import os.path
import popen2
import shutil
import string

from ConfigParser import ConfigParser
from distutils.errors import DistutilsError
from pkg_resources import parse_requirements
from setuptools.package_index import PackageIndex

from pypi2pkgsys.utils import *

patchdir = os.path.join(os.path.dirname(__file__), 'patches')
config = ConfigParser()
config.read(os.path.join(patchdir, 'index.ini'))

masked = {}
broken_file = file(os.path.join(patchdir, 'broken.txt'))
ln = broken_file.readline()
while ln:
    name, value = ln.split('=', 1)
    name = name.strip(); value = value.strip()
    masked[name] = value
    ln = broken_file.readline()

# If setup.py write something else by itself, the following code might not
# work. FIX ME.
popen_fmt = '(cd %s; python setup.py dump)'

class PYPI2Package(object):
    def __init__(self, PackageSystem, argv):
        self.options = { '--url' : 'http://pypi.python.org/simple',
                         '--download-dir' : '/var/tmp/pypi/downloads',
                         '--unpack-dir' : '/var/tmp/pypi/unpack' }

        self.pkgsys = PackageSystem()
        self.options = self.pkgsys.InitializeOptions(self.options)

        optname = None
        self.packages = []

        for arg in argv[1:]:
            if optname is not None:
                self.options[optname] = arg
                optname = None
            elif arg in self.options:
                optname = arg
            else:
                self.packages.append(arg)

        # Ensure the exists of the working directories.
        map(lambda diropt: ensure_dir(self.options[diropt]),
            ['--download-dir', '--unpack-dir'])

        self.options = self.pkgsys.FinalizeOptions(self.options)

    def run(self):
        idx = 0
        while True:
            logfn = 'pypi-download.%03d.log' % idx
            if not os.path.exists(logfn):
                logfile = file(logfn, 'w')
                break
            idx = idx + 1

        # Prepare for iterations.
        pkgidx = PackageIndex(index_url = self.options['--url'])
        packages = self.packages
        dldir = self.options['--download-dir']
        unpackdir = self.options['--unpack-dir']

        # Main loop.
        ok_packages = []
        while len(packages) > 0:
            new_packages = []
            for idx in xrange(len(packages)):
                pkg = packages[idx]

                pkgname = pkg.split('>=')[0].strip()
                if pkgname in masked:
                    print '%r is not accepted: %r' % (pkgname, masked[pkgname])
                    continue

                print 'Downloading %s ...' % pkg
                try:
                    dist = map(lambda reqobj:
                                   pkgidx.fetch_distribution(reqobj, dldir,
                                                             source = True),
                               parse_requirements([pkg]))[0]
                except DistutilsError:
                    logfile.write('%s = %s\n' % (pkgname, sys.exc_info()[1]))
                    logfile.flush()
                    continue
                if dist is None:
                    print 'Download %s failed!' % pkg
                    logfile.write('%s = No downloads.\n' % pkgname)
                    logfile.flush()
                    continue

                print 'Unpacking ...', pkg
                cfgmap = smart_archive(dist, unpackdir)
                unpackpath = cfgmap['unpackpath']

                # Prepare parameters.
                print 'Processing ...', pkg
                pkgnamever = '%s-%s' % (dist.project_name, dist.version)
                if config.has_section(pkgnamever):
                    for name, value in config.items(pkgnamever):
                        cfgmap[name] = value
                if config.has_section(dist.project_name):
                    for name, value in config.items(dist.project_name):
                        if name not in cfgmap: cfgmap[name] = value
                if not 'patches' in cfgmap: cfgmap['patches'] = []
                else: cfgmap['patches'] = cfgmap['patches'].split()

                # Apply patches.
                for p in cfgmap['patches']:
                    print 'Applying %s' % p
                    os.system('(cd %s; patch -p0 < %s)' % \
                                  (unpackpath, os.path.join(patchdir, p)))
                self._setup_convert(os.path.join(unpackpath, 'setup.py'))

                print 'Get distribution args from %s' % unpackpath
                p = popen2.popen2(popen_fmt % unpackpath)
                p[1].close()
                ln = p[0].readline()
                while ln:
                    if ln.strip() == '**** PyPI2PkgSys ****': break
                    ln = p[0].readline()
                if not ln: raise RuntimeError, 'dump does not work.'
                c = p[0].readline()
                p[0].close()
                args = eval(c)
                shutil.rmtree(unpackpath)
                if 'install_requires' not in args or \
                        args['install_requires'] is None:
                    args['install_requires'] = []
                if 'extras_require' not in args or \
                        args['extras_require'] is None:
                    args['extras_require'] = {}

                # Generate package from args and options.
                updated, deps = \
                    self.pkgsys.GenPackage(args, self.options, cfgmap)
                ok_packages.append(pkg)
                new_packages = uniq_extend(new_packages, deps)

            # Process all required but not processed packages.
            packages = []
            for pkg in new_packages:
                if pkg not in ok_packages: packages.append(pkg)
        logfile.close()

    def _setup_convert(self, setup_path):
        modified = False
        setup_fp = file(setup_path)
        output = ''
        ln = setup_fp.readline()
        while ln:
            lnlist = ln.split()
            if len(lnlist) >= 4 and lnlist[0] == 'from' and \
                    lnlist[1] == 'distutils.core' and lnlist[2] == 'import' \
                    and 'setup' in ln:
                idx = ln.find('distutils.core')
                ln = ln[:idx] + 'setuptools' + ln[idx + len('distutils.core'):]
                modified = True
            elif 'distutils.core.setup' in ln:
                idx = ln.find('distutils.core')
                ln = ln[:idx] + 'import setuptools; setuptools' + ln[idx + len('distutils.core'):]
                modified = True
            output = output + ln
            ln = setup_fp.readline()
        setup_fp.close()
        if modified:
            setup_fp = file(setup_path, 'w')
            setup_fp.write(output)
            setup_fp.close()
