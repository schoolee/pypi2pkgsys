# Copyright (C) 2008, Charles Wang <charlesw1234@163.com>
# Author: Charles Wang <charlesw1234@163.com>

import glob
import os.path
import string
import sys

from pypi2pkgsys import pkgroot
from pypi2pkgsys.PackageSystem import PackageSystem
from pypi2pkgsys.utils import *
from pypi2pkgsys.portage.utils import *

pypi_dir = 'dev-python'

class PkgSysPortage(PackageSystem):
    def __init__(self):
        PackageSystem.__init__(self)

    def InitializeOptions(self, options):
        options['--portage-distfiles'] = '/usr/portage/distfiles'
        options['--portage-dir'] = os.path.join('/usr/local/portage',
                                                pypi_dir)
        return options

    def FinalizeOptions(self, options):
        map(lambda diropt: ensure_dir(options[diropt]),
            ['--portage-distfiles', '--portage-dir'])
        return options

    def GenPackage(self, pkgtype, args, options, cfgmap):
        # Setup eb_args.
        eb_args = {}
        eb_args['self'] = sys.argv[0]
        eb_args['name'] = args['name']
        eb_args['package_file'] = cfgmap['pkgfile']
        eb_args['package_dir'] = cfgmap['pkgdir']
        eb_args['desc'] = args['description']
        eb_args['url'] = args['url']
        if args['license'] is not None and args['license'] != '':
            eb_args['license'] = LicenseConvert(args['name'], args['license'])
        elif 'classifiers' in args and args['classifiers'] is not None:
            for cfline in args['classifiers']:
                cflist = map(lambda cf: cf.strip(), cfline.split('::'))
                if len(cflist) == 3 and \
                        cflist[0] == 'License' and cflist[1] == 'OSI Approved':
                    eb_args['license'] = LicenseConvert(args['name'],
                                                        cflist[2])
        if 'license' not in eb_args or eb_args['license'] == '':
            eb_args['license'] = 'UNKNOWN'

        iuse_arr = ['doc'] + args['extras_require'].keys()
        eb_args['iuse'] = string.join(iuse_arr)

        rdepend = map(lambda dep: DepConvert(dep),
                      args['install_requires'])
        eb_args['rdepend'] = string.join(rdepend, '\n\t')

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
        eb_args['depend'] = string.join(depend, '\n\t')
        eb_args['patchlist'] = \
            string.join(map(lambda p: 'epatch "${FILESDIR}/%s"' % p,
                            cfgmap['patches']), '\n\t')

        # Setup ebuild.
        fullname = MakeFullname(args['name'], args['version'])
        if 'rev' not in cfgmap:
            ebuild_fn = '%s.ebuild' % fullname
        else:
            ebuild_fn = '%s-r%s.ebuild' % (fullname, cfgmap['rev'])
        ebuild_dir = os.path.join(options['--portage-dir'],
                                  NameConvert(args['name']))
        ensure_dir(ebuild_dir)
        ebuild_path = os.path.join(ebuild_dir, ebuild_fn)
        updated = False
        print 'Writing %s' % ebuild_path
        if pkgtype == 'setup.py':
            tmplf = file(os.path.join(pkgroot, 'portage', 'setup_py.tmpl'))
        else:
            raise RuntimeError, 'Unsupport package type: %s' % pkgtype
        ebuild_format = tmplf.read()
        tmplf.close()
        if smart_write(ebuild_path, ebuild_format % eb_args):
            updated = True
        if smart_symlink(cfgmap['pkgpath'],
                         os.path.join(options['--portage-distfiles'],
                                      cfgmap['pkgfile'])):
            updated = True
        if cfgmap['patches'] != []:
            ebuild_dir_files = os.path.join(ebuild_dir, 'files')
            ensure_dir(ebuild_dir_files)
            for p in cfgmap['patches']:
                if smart_symlink(os.path.join(os.path.dirname(__file__),
                                              'patches', p),
                                 os.path.join(ebuild_dir_files, p)):
                    updated = True

        # Call ebuild ... digest
        os.system('ebuild %s digest' % (ebuild_path))

        deps = []
        if updated:
            deps = uniq_extend(deps, args['install_requires'])
            for k in args['extras_require'].keys():
                deps = uniq_extend(deps, args['extras_require'][k])
        return (updated, deps)

