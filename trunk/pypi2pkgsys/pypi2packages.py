# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>

import copy
import os
import os.path

from setuptools.package_index import PackageIndex

from pypi2pkgsys import pkgroot, patchdir, config
from pypi2pkgsys.utils import *
from pypi2pkgsys.pypi_utils import *

class PYPI2Package(object):
    def __init__(self, PackageSystem, argv):
        self.options = { '--url' : 'http://pypi.python.org/simple',
                         '--download-dir' : '/var/tmp/pypi/downloads',
                         '--unpack-dir' : '/var/tmp/pypi/unpack',
                         '--deps' : 'false' }

        self.pkgsys = PackageSystem()
        self.pkgsys.init_options(self.options)

        optname = None
        self.pkgreqmap = {}

        for arg in argv[1:]:
            if optname is not None:
                self.options[optname] = arg
                optname = None
            elif arg in self.options:
                optname = arg
            else:
                reqmap_add(self.pkgreqmap, reqstr2obj(arg))

        # Ensure the exists of the working directories.
        map(lambda diropt: ensure_dir(self.options[diropt]),
            ['--download-dir', '--unpack-dir'])

        deps = self.options['--deps'].lower()
        self.options['--deps'] = \
            deps == 'true' or deps == 't' or \
            deps == 'yes' or deps == 'y'

        self.pkgsys.finalize_options(self.options)

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
        args = copy.copy(self.options)
        # Prepare for iterations.
        pkgidx = PackageIndex(index_url = self.options['--url'])
        pkgreqmap = self.pkgreqmap
        dldir = args['--download-dir']
        unpackdir = args['--unpack-dir']

        # Main loop.
        ok_packages = []
        while len(pkgreqmap) > 0:
            new_pkgreqmap = {}
            for pkgreqobj in pkgreqmap.values():
                pkgname = pkgreqobj.project_name
                if pkgname in ok_packages: continue
                ok_packages.append(pkgname)
                reqstr = str(pkgreqobj)

                try: check_broken(pkgname)
                except:
                    in_except(None, pkgname, 'masked')
                    continue

                # Collect values into args step by step.
                args = copy.copy(self.options)

                print '\nDownloading %s ...' % reqstr
                try:
                    dist = pkgidx.fetch_distribution(pkgreqobj, dldir,
                                                     source = True)
                    if dist is None:
                        raise RuntimeError, 'None'
                except:
                    in_except(logfp, pkgname, 'Download %s failed' % reqstr)
                    continue

                print 'Unpacking ...', dist.location
                try: smart_archive(args, dist, unpackdir)
                except:
                    in_except(logfp, pkgname, 'Unpack %s failed' % reqstr)
                    continue
                unpackpath = args['unpackpath']

                print 'Processing ...', pkgname
                for secname in ('%s-%s' % (dist.project_name, dist.version),
                                dist.project_name):
                    if config.has_section(secname):
                        for name, value in config.items(secname):
                            if name not in args: args[name] = value
                if not 'patches' in args: args['patches'] = []
                else: args['patches'] = args['patches'].split()

                # Apply patches.
                for patch in args['patches']:
                    print 'Applying %s ...' % patch
                    os.system('(cd %s; patch -p0 < %s)' % \
                                  (unpackpath, os.path.join(patchdir, patch)))
                
                if args['pkgtype'] == 'setup.py':
                    fix_setup(os.path.join(unpackpath, args['setup_path']))
                    print 'Get distribution args from %s ...' % unpackpath
                    try: get_package_args(args)
                    except:
                        in_except(logfp, pkgname, '"setup.py dump" failed')
                        continue

                fix_args(args, pkgname)

                # Generate package from args and options.
                try:
                    self.pkgsys.setup_args(args)
                except:
                    in_except(logfp, pkgname, 'pkgsys.setup_args failed')
                    continue

                tmplf = file(os.path.join(pkgroot, args['template']))
                tmpl = tmplf.read()
                tmplf.close()

                ensure_dir(os.path.dirname(args['output']))
                print 'Writing %s' % args['output']
                if smart_write(args['output'], tmpl % args): updated = True
                if smart_symlink(args['pkgpath'],
                                 os.path.join(args['filedir'],
                                              args['pkgfile'])):
                    updated = True
                if args['patches'] != []:
                    ensure_dir(args['patchdir'])
                    for patch in args['patches']:
                        if smart_symlink(os.path.join(patchdir, patch),
                                         os.path.join(args['patchdir'],
                                                      patch)):
                            updated = True
                try:
                    self.pkgsys.process(args)
                except:
                    in_except(logfp, pkgname, 'process failed')
                    continue

                if self.options['--deps']:
                    reqstrlist = args['install_requires']
                    for k in args['extras_require'].keys():
                        reqstrlist.extend(args['extras_require'][k])
                    for reqstr in reqstrlist:
                        reqmap_add(new_pkgreqmap, reqstr2obj(reqstr))

                print 'Finish the processing of %s.' % pkgname

                # Process of a single package is finished.

            pkgreqmap = new_pkgreqmap
