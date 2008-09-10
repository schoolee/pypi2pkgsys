# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
# License: BSD

import string

from pypi2pkgsys.utils import cut_parentheses

fullmap = {}
fullmap['academic free license version 3.0'] = 'AFL-3.0'
fullmap['apache 2.0'] = 'Apache-2.0'
fullmap['attribution assurance license'] = 'UNKNOWN',
fullmap['common public license version 1.0'] = 'CPL-1.0'
fullmap['public domain'] = 'public-domain'
fullmap['gnu general public license, version 3 or later'] = 'GPL-3'
fullmap['general Public licence'] = 'GPL'
fullmap['general Public license'] = 'GPL'
fullmap['open software license'] = 'OSL-2.0'
fullmap['zope public license'] = 'ZPL'
fullmap['http://www.apache.org/licenses/license-2.0'] = 'Apache-2.0'
fullmap['http://www.ditrack.org/license'] = 'BSD'
fullmap['http://www.gnu.org/licenses/gpl.txt'] = 'GPL'
fullmap['http://www.gnu.org/licenses/gpl.html'] = 'GPL'
fullmap['http://www.gnu.org/copyleft/gpl.html'] = 'GPL'
fullmap['http://www.gnu.org/copyleft/lesser.html'] = 'LGPL'
fullmap['http://www.fsf.org/licensing/licenses/lgpl.txt'] = 'LGPL'
fullmap['http://www.opensource.org/licenses/gpl-license.php'] = 'GPL'
fullmap['http://www.opensource.org/licenses/mit-license.html'] = 'MIT'
fullmap['http://www.cecill.info/licences/licence_cecill-c_v1-en.html'] = 'CeCILL-2'

partmap = {}
#partmap['%license'] = ''
partmap['afl'] = 'AFL-3.0'
partmap['apache'] = 'Apache-2.0'
partmap['apache license'] = 'Apache-2.0'
partmap['bsd-like'] = 'BSD'
partmap['bsd/mit'] = 'BSD MIT'
#partmap['d-fsl'] = ''
#partmap['freeware'] = ''
partmap['agpl'] = 'GPL'
partmap['bsd-style'] = 'BSD'
partmap['gnu'] = 'GPL'
partmap['gpl'] = 'GPL'
partmap['gpl2'] = 'GPL-2'
partmap['gpl2.1'] = 'GPL-2'
partmap['gpl3'] = 'GPL-3'
partmap['gplv3'] = 'GPL-3'
partmap['gplv2'] = 'GPL-2'
partmap['lgpl'] = 'LGPL'
partmap['lgpl2'] = 'LGPL-2'
partmap['lgpl 2.1 or later'] = 'LGPL-2.1'
partmap['mit-style'] = 'MIT'
partmap['mit/x'] = 'MIT X11'
partmap['python-like'] = 'PYTHON'
partmap['wxwindows'] = 'wxWinLL-3'
partmap['x11/mit'] = 'X11 MIT'
partmap['psf'] = 'PSF'
partmap['zlib/libpng'] = 'ZLIB'
partmap['zpl2.1'] = 'ZPL'

portage_license = { 'unknown' : 'UNKNOWN' }
for pl in glob.glob('/usr/portage/licenses/*'):
    pl = os.path.basename(pl)
    pl_lower = pl.lower()
    if pl_lower not in portage_licenses: portage_licenses[pl_lower] = pl

def LicenseConvert(pkgname, pkglicense):
    if pkgname in portage_licenses: return portage_license[pkgname]
    if pkglicense.lower() in fullmap: return fullmap[pkglicense.lower()]
    pkglicense_bk = pkglicense
    pkglicense = cut_parentheses(pkglicense)
    res = []
    for pl in pkglicense.split(','):
        res.extend(pl.split())
    reslicense = []
    for pl in res:
        pl = pl.lower()
        if pl in partmap and pl: reslicense.append(partmap[pl])
    if reslicense == []:
        raise RuntimeError, 'Unrecognized license: %s' % pkglicense_bk
    return string.join(reslicense)
