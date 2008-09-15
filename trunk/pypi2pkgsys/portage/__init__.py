# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>

import glob
import os.path
import string
import sys

import portage
from portage.manifest import Manifest
from portage.output import EOutput

from pypi2pkgsys.package_system import package_system
from pypi2pkgsys.utils import ensure_dir
from pypi2pkgsys.portage.utils import *

class pkgsys_portage(package_system):
    pkgsysname = 'portage'
    def __init__(self):
        package_system.__init__(self)
        self.eout = EOutput()

    def begin(self, msg):
        self.eout.ebegin(msg)

    def end(self, success_ornot):
        if success_ornot: self.eout.eend(0)
        else: self.eout.eend(1)

    def info(self, msg):
        self.eout.einfo(msg)

    def error(self, msg):
        self.eout.eerror(msg)

    def init_options(self, options):
        options['--portage-distfiles'] = portage.settings['DISTDIR']
        options['--portage-dir'] = os.path.join('/usr/local/portage',
                                                pypi_dir)

    def finalize_options(self, options):
        map(lambda diropt: ensure_dir(options[diropt]),
            ['--portage-distfiles', '--portage-dir'])

    def setup_args(self, args):
        if args['license'] != None and args['license'] != '':
            args['license'] = LicenseConvert(args['name'], args['license'])
        elif 'classifiers' in args and args['classifiers'] is not None:
            for cfline in args['classifiers']:
                cflist = map(lambda cf: cf.strip(), cfline.split('::'))
                if len(cflist) == 3 and \
                        cflist[0] == 'License' and cflist[1] == 'OSI Approved':
                    args['license'] = LicenseConvert(args['name'], cflist[2])
        if args['license'] == '': args['license'] = 'UNKNOWN'

        iuse_arr = ['doc'] + args['extras_require'].keys()
        args['iuse'] = string.join(iuse_arr)

        rdepend = map(lambda dep: DepConvert(dep), args['install_requires'])
        args['rdepend'] = string.join(rdepend, '\n\t')

        ereq = {}
        for k in args['extras_require']:
            if args['extras_require'][k] == []: continue
            ereq[k] = args['extras_require'][k]
        depend = []
        if args['name'] != 'setuptools':
            depend.append('dev-python/setuptools')
        depend.append('doc? ( dev-python/pudge dev-python/buildutils )')
        depend.extend(map(lambda extra: '%s? ( %s )' % \
                              (extra, string.join(map(lambda edep:
                                                          DepConvert(edep),
                                                      ereq[extra]))),
                          ereq.keys()))
        args['depend'] = string.join(depend, '\n\t')
        args['patchlist'] = \
            string.join(map(lambda p: 'epatch "${FILESDIR}/%s"' % p,
                            args['patches']), '\n\t')

        # Setup ebuild.
        fullname = MakeFullname(args['name'], args['version'])
        if 'rev' not in args:
            ebuild_fn = '%s.ebuild' % fullname
        else:
            ebuild_fn = '%s-r%s.ebuild' % (fullname, args['rev'])
        ebuild_dir = os.path.join(args['--portage-dir'],
                                  NameConvert(args['name']))
        ebuild_path = os.path.join(ebuild_dir, ebuild_fn)
        for pkgtype in ['setup.py', 'single.py']:
            if args['pkgtype'] == pkgtype:
                args['template'] = os.path.join('portage', '%s.tmpl' % pkgtype)
                break
        if 'template' not in args:
            raise RuntimeError, 'Unsupported package type %s' % args['pkgtype']
        args['output'] = ebuild_path
        args['filedir'] = args['--portage-distfiles']
        args['patchdir'] = os.path.join(ebuild_dir, 'files')

    def process(self, args):
        # Call ebuild ... digest
        try:
            portage._doebuild_manifest_exempt_depend += 1
            pkgdir = os.path.dirname(args['output'])
            fetchlist_dict = portage.FetchlistDict(pkgdir, portage.settings,
                                                   portage.portdb)
            mf = Manifest(pkgdir, args['--portage-distfiles'],
                          fetchlist_dict = fetchlist_dict,
                          manifest1_compat = False)
            mf.create(requiredDistfiles = None,
                      assumeDistHashesSometimes = True,
                      assumeDistHashesAlways = True)
            mf.write()
        finally:
            portage._doebuild_manifest_exempt_depend -= 1
