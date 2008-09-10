# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>

import os
import os.path
import sys

from pkg_resources import parse_requirements
from setuptools.package_index import PackageIndex

from pypi2pkgsys import patchdir, config
from pypi2pkgsys.utils import *
from pypi2pkgsys.pypi_utils import *

class PYPI2Package(object):
    def __init__(self, PackageSystem, argv):
        self.options = { '--url' : 'http://pypi.python.org/simple',
                         '--download-dir' : '/var/tmp/pypi/downloads',
                         '--unpack-dir' : '/var/tmp/pypi/unpack',
                         '--deps' : 'false' }

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

        deps = self.options['--deps'].lower()
        self.options['--deps'] = \
            deps == 'true' or deps == 't' or \
            deps == 'yes' or deps == 'y'

        self.options = self.pkgsys.FinalizeOptions(self.options)

        idx = 0
        while True:
            logfn = 'pypi-download.%03d.log' % idx
            if not os.path.exists(logfn):
                logfile = file(logfn, 'w')
                break
            idx = idx + 1
        self.options['log'] = logfile

    def __del__(self):
        self.options['log'].close()

    def run(self):
        logfp = self.options['log']
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
                print
                pkg = packages[idx]

                pkgname = pkg.split('>=')[0].strip()

                try: check_broken(pkgname)
                except:
                    exc_value = sys.exc_info()[1]
                    print '%r is not accepted: %r' % (pkgname, exc_value)
                    continue

                print 'Downloading %s ...' % pkg
                try:
                    dist = map(lambda reqobj:
                                   pkgidx.fetch_distribution(reqobj, dldir,
                                                             source = True),
                               parse_requirements([pkg]))[0]
                except:
                    exc_value = sys.exc_info()[1]
                    print 'Download %s failed: %s!' % (pkgname, exc_value)
                    logfp.write('%s = Download failed: %s\n' % \
                                    (pkgname, exc_value))
                    logfp.flush()
                    continue
                if dist is None:
                    print 'Download %s failed!' % pkgname
                    logfp.write('%s = No downloads.\n' % pkgname)
                    logfp.flush()
                    continue

                print 'Unpacking ...', pkg
                try: cfgmap = smart_archive(dist, unpackdir)
                except:
                    exc_value = sys.exc_info()[1]
                    print 'Unpack %s failed: %s!' % (pkgname, exc_value)
                    logfp.write('%s = Unpack failed: %s\n' % \
                                    (pkgname, exc_value))
                    logfp.flush()
                    continue
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
                pkgtype = check_package_type(unpackpath)
                if pkgtype == 'setup.py':
                    fix_setup(unpackpath)
                    print 'Get distribution args from %s' % unpackpath
                    try: args = get_package_args(unpackpath)
                    except:
                        exc_value = sys.exc_info()[1]
                        print 'Dump %s failed: %s.' % (pkgname, exc_value)
                        logfp.write('%s = Dump args failed: %s\n' % \
                                        (pkgname, exc_value))
                        logfp.flush()
                        continue
                else:
                    print '%s: Unsupported package type.' % pkgname
                    logfp.write('%s = Unsupport package type.\n' % pkgname)
                    logfp.flush()
                    continue

                args = fix_args(pkgname, args)

                # Generate package from args and options.
                try:
                    updated, deps = \
                        self.pkgsys.GenPackage(pkgtype, args, self.options,
                                               cfgmap)
                except:
                    exc_value = sys.exc_info()[1]
                    print '%s: GenPackage failed: %s' % (pkgname, exc_value)
                    logfp.write('%s = GenPackage failed: %s\n' %\
                                    (pkgname, exc_value))
                    logfp.flush()
                    deps = []
                new_packages = uniq_extend(new_packages, deps)

            # Process all required but not processed packages.
            packages = []
            if self.options['--deps']:
                for pkg in new_packages:
                    if pkg not in ok_packages: packages.append(pkg)
