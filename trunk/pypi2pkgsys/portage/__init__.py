# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
# License: BSD

import glob
import os.path
import string
import sys

from pypi2pkgsys import pkgroot, patchdir, config
from pypi2pkgsys.PackageSystem import PackageSystem
from pypi2pkgsys.utils import *

pypi_dir = 'dev-python'

masked = {}
if config.has_section('portage-broken'):
    for name, value in config.items('portage-broken'):
        assert name not in masked
        masked[name] = value

version_map = {}
if config.has_option('portage', 'version-map'):
    for v in config.get('portage', 'version-map').split():
        name, value = v.split(':')
        version_map[name] = value

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

    def GenPackage(self, args, options, cfgmap):
        def NameConvert(pyname):
            return pyname.lower()
        def VersionConvert(pyname, pyversion):
            if pyversion == '': return pyversion
            fullname = '%s-%s' % (pyname, pyversion)
            if fullname in version_map: return version_map[fullname]
            ver = ''
            while pyversion != '':
                if pyversion[0].isdigit() or pyversion[0] == '.':
                    ver = ver + pyversion[0]
                    pyversion = pyversion[1:]
                else:
                    break
            if ver != '' and ver[-1] == '.': ver = ver[:-1]
            if pyversion != '':
                while pyversion[0] == '_' or pyversion[0] == '-':
                    pyversion = pyversion[1:]
                if 'alpha' in pyversion:
                    ver = ver + '_alpha' + digit_extract(pyversion)
                elif 'beta' in pyversion:
                    ver = ver + '_beta' + digit_extract(pyversion)
                elif 'patch' in pyversion:
                    ver = ver + '_p' + digit_extract(pyversion)
                elif 'preview' in pyversion or 'pre' in pyversion:
                    ver = ver + '_pre' + digit_extract(pyversion)
                elif 'rc' in pyversion:
                    ver = ver + '_rc' + digit_extract(pyversion)
                elif 'dev' in pyversion:
                    ver = ver + '_pre' + digit_extract(pyversion)
                elif 'a' in pyversion:
                    ver = ver + '_alpha' + digit_extract(pyversion)
                elif 'b' in pyversion:
                    ver = ver + '_beta' + digit_extract(pyversion)
                elif 'p' in pyversion:
                    ver = ver + '_p' + digit_extract(pyversion)
                elif 'r' in pyversion or 'c' in pyversion:
                    ver = ver + '_rc' + digit_extract(pyversion)
                else:
                    ver = ver + '_p' + digit_extract(pyversion)
            return ver
        def MakeFullname(pyname, pyversion):
            if pyversion == '': return pyname
            else: return '%s-%s' % (pyname, pyversion)
        def DepConvert(pydep):
            if '>=' not in pydep:
                return '%s/%s' % (pypi_dir, NameConvert(pydep))
            idx = pydep.index('>=')
            name = pydep[:idx].strip(); version = pydep[idx + 2:].strip()
            return '>=%s/%s' % (pypi_dir,
                                MakeFullname(NameConvert(name),
                                             VersionConvert(name, version)))
        def LicenseConvert(pyname, pylicense):
            # It is a really dirty work.
            if pyname in licenses: return licenses[pyname]
            pylicense_bk = pylicense
            pylicense = cut_parentheses(pylicense)
            for lic in licenselist:
                pylicense = pylicense.replace(lic[0], lic[1])
            if pylicense == '': return 'UNKNOWN'
            if pylicense.find(',') >= 0:
                lclist = []
                for part in pylicense.split(','):
                    part = part.strip()
                    lclist.extend(part.split())
            else:
                lclist = pylicense.split()
            reslclist = []
            for lc in lclist:
                lc = lc.lower()
                if lc in licenses:  reslclist.append(licenses[lc])
            if reslclist == []:
                # May be we have to enhance this function.
                raise RuntimeError, 'Unrecognized license: %s' % pylicense_bk
            return string.join(reslclist)

        # Check acceptance.
        if args['name'] in masked:
            print '%r is not accepted: %r.' % (args['name'],
                                               masked[args['name']])
            return (False, [])

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
        fullname = MakeFullname(NameConvert(args['name']),
                                VersionConvert(args['name'], args['version']))
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
