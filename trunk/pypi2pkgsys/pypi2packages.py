# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>

import copy
import os
import os.path

from setuptools.package_index import PackageIndex

from pypi2pkgsys import pkgroot, patchdir, config
from pypi2pkgsys.utils import *
from pypi2pkgsys.pypi_utils import *

def get_bool_opt(stropt):
    stropt = stropt.lower()
    for strvalue, boolvalue in (('false', False), ('no', False),
                                ('true', True), ('yes', True)):
        if stropt == strvalue: return boolvalue
        if stropt == strvalue[0]: return boolvalue
    raise RuntimeError, 'Unsupport bool value: %s' % stropt

class PYPI2Package(object):
    def __init__(self, PackageSystem, argv):
        self.arg0 = argv[0]
        self.options = { '--url' : 'http://pypi.python.org/simple',
                         '--download-dir' : '/var/tmp/pypi/downloads',
                         '--unpack-dir' : '/var/tmp/pypi/unpack',
                         '--deps' : 'false',
                         '--skip-broken' : 'true',
                         '--use-log' : 'true',
                         '--log-path' : '/var/tmp/pypi/pypi2pkgsys.log' }

        self.pkgsys = PackageSystem()
        self.pkgsys.init_options(self.options)

        optname = None
        self.reqarglist = []

        for arg in argv[1:]:
            if optname is not None:
                self.options[optname] = arg
                optname = None
            elif arg in self.options:
                optname = arg
            else:
                self.reqarglist.append(arg)

        # Ensure the exists of the working directories.
        map(lambda diropt: ensure_dir(self.options[diropt]),
            ['--download-dir', '--unpack-dir'])

        for bopt in ['--skip-broken', '--deps', '--use-log']:
            self.options[bopt] = get_bool_opt(self.options[bopt])

        self.pkgsys.finalize_options(self.options)

        if not self.options['--use-log']: self.logobj = pypilog(None)
        else: self.logobj = pypilog(self.options['--log-path'])

    def run(self):
        # Prepare for iterations.
        pkgreqmap = {}
        matchlist = []
        for reqarg in self.reqarglist:
            if '*' in reqarg or '?' in reqarg: matchlist.append(reqarg)
            else: reqmap_add(pkgreqmap, reqstr2obj(reqarg))
        for reqstr in pypi_match(self.logobj, matchlist,
                                 self.options['--url']):
            reqmap_add(pkgreqmap, reqstr2obj(reqstr))

        pkgidx = PackageIndex(index_url = self.options['--url'])

        # Main loop.
        ok_packages = []
        while len(pkgreqmap) > 0:
            new_pkgreqmap = {}
            for pkgreqobj in pkgreqmap.values():
                pkgname = pkgreqobj.project_name
                if pkgname in ok_packages: continue
                ok_packages.append(pkgname)
                reqstr = str(pkgreqobj)

                print

                if self.options['--skip-broken']:
                    try: self.logobj.check_broken(pkgname)
                    except: continue

                # Collect values into args step by step.
                args = copy.copy(self.options)
                args['self'] = self.arg0

                print 'Downloading %s ...' % reqstr
                try:
                    dist = pkgidx.fetch_distribution(pkgreqobj,
                                                     self.options['--download-dir'],
                                                     source = True)
                    if dist is None:
                        raise RuntimeError, 'None'
                except:
                    self.logobj.in_except(pkgname,
                                          'Download %s failed' % reqstr)
                    continue

                print 'Unpacking ...', dist.location
                try: smart_archive(args, dist, self.options['--unpack-dir'])
                except:
                    self.logobj.in_except(pkgname, 'Unpack %s failed' % reqstr)
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

                try: get_package_args(args, dist)
                except:
                    self.logobj.in_except(pkgname, 'Get package args failed')
                    continue

                try:
                    self.pkgsys.setup_args(args)
                except:
                    self.logobj.in_except(pkgname, 'pkgsys.setup_args failed')
                    continue

                ensure_dir(os.path.dirname(args['output']))
                print 'Writing %s' % args['output']
                if smart_write(args['output'],
                               os.path.join(pkgroot, args['template']),
                               args):
                    updated = True
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
                    self.logobj.in_except(pkgname, 'process failed')
                    continue

                if self.options['--deps']:
                    reqstrlist = args['install_requires']
                    for k in args['extras_require'].keys():
                        reqstrlist.extend(args['extras_require'][k])
                    for reqstr in reqstrlist:
                        reqmap_add(new_pkgreqmap, reqstr2obj(reqstr))

                self.logobj.pkgname_ok(pkgname)

                # Process of a single package is finished.

            pkgreqmap = new_pkgreqmap
