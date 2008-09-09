# Copyright (C) 2008, Charles Wang <charlesw1234@163.com>
# Author: Charles Wang <charlesw1234@163.com>

import glob
import os.path
import string
import sys

from pypi2pkgsys.pypi2packages import config
from pypi2pkgsys.PackageSystem import PackageSystem
from pypi2pkgsys.utils import *

pypi_dir = 'dev-python'

ebuild_format = """# This file is generated by %(self)s automatically.

inherit distutils

MY_PN=%(name)s
MY_PF=%(package_file)s
MY_PD=%(package_dir)s

DESCRIPTION="%(desc)s"
HOMEPAGE="%(url)s"
SRC_URI="http://what/${MY_PF}"
LICENSE="%(license)s"
KEYWORDS="~alpha ~amd64 ~hppa ~ia64 ~ppc ~ppc64 ~sparc ~x86"
SLOT="0"
IUSE="%(iuse)s"

RDEPEND="%(rdepend)s"
DEPEND="${RDEPEND}
\t%(depend)s"

S=${WORKDIR}/${MY_PD}

src_unpack() {
\tdistutils_src_unpack
\t%(patchlist)s
}

src_compile() {
\tdistutils_src_compile
\tif use doc ; then
\t\tPYTHONPATH=. "${python}" setup.py pudge || die "generating doc failed."
\tfi
}

src_install() {
\tdistutils_src_install
\tuse doc && dohtml -r docs/html/*
}
"""

licenselist = []
licenselist.append(('Academic Free License version 3.0', 'AFL-3.0'))
licenselist.append(('Apache 2.0', 'Apache-2.0'))
licenselist.append(('Attribution Assurance License', ''))
licenselist.append(('Common Public License version 1.0', 'CPL-1.0'))
licenselist.append(('public domain', 'public-domain'))
licenselist.append(('Public Domain', 'public-domain'))
licenselist.append(('GNU General Public License, version 3 or later', 'GPL-3'))
licenselist.append(('General Public Licence', 'GPL'))
licenselist.append(('General Public License', 'GPL'))
licenselist.append(('Open Software License', 'OSL-2.0'))
licenselist.append(('Zope Public License', 'ZPL'))

licenses = {}
for p in glob.glob('/usr/portage/licenses/*'):
    p = os.path.basename(p)
    pl = p.lower()
    if pl not in licenses: licenses[pl] = p
licenses['%license'] = ''
licenses['afl'] = 'AFL-3.0'
licenses['apache'] = 'Apache-2.0'
licenses['apache license'] = 'Apache-2.0'
licenses['bsd-like'] = 'BSD'
licenses['bsd/mit'] = 'BSD MIT'
licenses['d-fsl'] = ''
licenses['freeware'] = ''
licenses['agpl'] = 'GPL'
licenses['bsd-style'] = 'BSD'
licenses['gnu'] = 'GPL'
licenses['gpl'] = 'GPL'
licenses['gpl2'] = 'GPL-2'
licenses['gpl2.1'] = 'GPL-2'
licenses['gpl3'] = 'GPL-3'
licenses['gplv3'] = 'GPL-3'
licenses['gplv2'] = 'GPL-2'
licenses['lgpl'] = 'LGPL'
licenses['lgpl2'] = 'LGPL-2'
licenses['lgpl 2.1 or later'] = 'LGPL-2.1'
licenses['mit-style'] = 'MIT'
licenses['mit/x'] = 'MIT X11'
licenses['python-like'] = 'PYTHON'
licenses['wxwindows'] = 'wxWinLL-3'
licenses['x11/mit'] = 'X11 MIT'
licenses['psf'] = 'PSF'
licenses['zlib/libpng'] = 'ZLIB'
licenses['zpl2.1'] = 'ZPL'
licenses['http://www.apache.org/licenses/license-2.0'] = 'Apache-2.0'
licenses['http://www.ditrack.org/license'] = 'BSD'
licenses['http://www.gnu.org/licenses/gpl.txt'] = 'GPL'
licenses['http://www.gnu.org/licenses/gpl.html'] = 'GPL'
licenses['http://www.gnu.org/copyleft/gpl.html'] = 'GPL'
licenses['http://www.gnu.org/copyleft/lesser.html'] = 'LGPL'
licenses['http://www.fsf.org/licensing/licenses/lgpl.txt'] = 'LGPL'
licenses['http://www.opensource.org/licenses/gpl-license.php'] = 'GPL'
licenses['http://www.opensource.org/licenses/mit-license.html'] = 'MIT'
licenses['http://www.cecill.info/licences/licence_cecill-c_v1-en.html'] = 'CeCILL-2'

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
