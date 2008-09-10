# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
# License: BSD

def digit_extract(value):
    retvalue = ''
    for v in value:
        if v in '0123456789': retvalue = retvalue + v
        elif retvalue == '': continue # We need not start from scratch.
        else: break # We need not any separated digits.
    return retvalue

def VersionConvert(pkgversion):
    if pkgversion == '': return pkgversion
    ver = ''
    while pkgversion != '':
        if pkgversion[0].isdigit() or pkgversion[0] == '.':
            ver = ver + pkgversion[0]
            pkgversion = pkgversion[1:]
        else:
            break
    if ver != '' and ver[-1] == '.': ver = ver[:-1]
    if pkgversion != '':
        while pkgversion[0] == '_' or pkgversion[0] == '-':
            pkgversion = pkgversion[1:]
        if 'alpha' in pkgversion:
            ver = ver + '_alpha' + digit_extract(pkgversion)
        elif 'beta' in pkgversion:
            ver = ver + '_beta' + digit_extract(pkgversion)
        elif 'patch' in pkgversion:
            ver = ver + '_p' + digit_extract(pkgversion)
        elif 'preview' in pkgversion or 'pre' in pkgversion:
            ver = ver + '_pre' + digit_extract(pkgversion)
        elif 'rc' in pkgversion:
            ver = ver + '_rc' + digit_extract(pkgversion)
        elif 'dev' in pkgversion:
            ver = ver + '_pre' + digit_extract(pkgversion)
        elif 'a' in pkgversion:
            ver = ver + '_alpha' + digit_extract(pkgversion)
        elif 'b' in pkgversion:
            ver = ver + '_beta' + digit_extract(pkgversion)
        elif 'p' in pkgversion:
            ver = ver + '_p' + digit_extract(pkgversion)
        elif 'r' in pkgversion or 'c' in pkgversion:
            ver = ver + '_rc' + digit_extract(pkgversion)
        else:
            ver = ver + '_p' + digit_extract(pkgversion)
    return ver
