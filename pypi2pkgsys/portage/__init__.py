# Copyright (C) 2008, Charles Wang <charlesw1234@163.com>
# Author: Charles Wang <charlesw1234@163.com>

import glob
import os.path
import string
import sys

from pypi2pkgsys.PackageSystem import PackageSystem
from pypi2pkgsys.utils import ensure_dir
from pypi2pkgsys.portage.utils import *

class PkgSysPortage(PackageSystem):
    def __init__(self):
        PackageSystem.__init__(self)

    def init_options(self, options):
        options['--portage-distfiles'] = '/usr/portage/distfiles'
        options['--portage-dir'] = os.path.join('/usr/local/portage',
                                                pypi_dir)

    def finalize_options(self, options):
        map(lambda diropt: ensure_dir(options[diropt]),
            ['--portage-distfiles', '--portage-dir'])

    def setup_args(self, args):
        args['self'] = sys.argv[0]
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
        for pkgtype in ['setup.py', 'single']:
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
        cmd = 'ebuild %s digest' % args['output']
        print 'Running %s ...' % cmd
        os.system(cmd)
