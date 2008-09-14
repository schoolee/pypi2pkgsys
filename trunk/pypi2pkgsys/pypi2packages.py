# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
# License: BSD

import copy
import os
import os.path

from setuptools.package_index import PackageIndex

from pypi2pkgsys import pkgroot, patchdir, config
from pypi2pkgsys.utils import *
from pypi2pkgsys.pypi_utils import *
from pypi2pkgsys.pypi_objects import *

class pypi2package(object):
    def __init__(self, package_system, argv):
        self.arg0 = argv[0]

        self.pkgsys = package_system()

        self.options, self.reqarglist = parse_argv(argv, self.pkgsys)

        if self.options['--log-path'] == '': self.logobj = pypilog(None)
        else: self.logobj = pypilog(self.options['--log-path'])

    def run(self):
        # Prepare for iterations.
        pkgreqmap = reqmap()
        for reqarg in self.reqarglist: pkgreqmap.append_arg(reqarg)
        pkgreqmap.resolve_matchlist(self.logobj, self.options['--url'])

        pkgidx = PackageIndex(index_url = self.options['--url'])

        # Main loop.
        distlist = []
        ok_packages = []
        while len(pkgreqmap) > 0:
            new_pkgreqmap = reqmap()
            for idx, total, pkgreqobj in pkgreqmap.reqobj_seq():

                pkgname = pkgreqobj.project_name
                if pkgname in ok_packages: continue
                ok_packages.append(pkgname)
                reqstr = str(pkgreqobj)

                print '\n======== %s: %d/%d ========' % (pkgname, idx, total)

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
                        new_pkgreqmap.add(reqstr2obj(reqstr))

                self.logobj.pkgname_ok(pkgname)
                if self.options['--cache-root'] != '':
                    distlist.append(dist)

                # Process of a single package is finished.

            pkgreqmap = new_pkgreqmap

        if self.options['--cache-root']:
            cache = pypicache(self.options['--cache-root'],
                              self.options['--cache-url'])
            cache.add_packages(distlist)
            del(cache)
