# Copyright (C) 2008, Charles Wang <charlesw1234@163.com>
# Author: Charles Wang <charlesw1234@163.com>

import filecmp
import os
import os.path
import tarfile
import zipfile
from setuptools.archive_util import unpack_archive

def ensure_dir(dir):
    if not os.path.isdir(dir): os.makedirs(dir)

def smart_write(fpath, content):
    if os.path.isfile(fpath) or os.path.islink(fpath):
        f = file(fpath)
        orig_content = f.read()
        f.close()
        if orig_content == content: return False
    f = file(fpath, 'w')
    f.write(content)
    f.close()
    return True

def smart_symlink(src, dst):
    if os.path.islink(dst):
        if os.readlink(dst) == src: return False
        os.unlink(dst)
    elif os.path.isfile(dst):
        if filecmp.cmp(dst, src): return False
        os.unlink(dst)
    os.symlink(src, dst)
    return True

def uniq_extend(result, added):
    for a in added:
        if a not in result: result.append(a)
    return result

def cut_parentheses(value):
    retvalue = ''; lvl = 0
    for ch in value:
        if ch == '(': lvl = lvl + 1
        elif ch == ')': lvl = lvl - 1
        elif lvl == 0: retvalue = retvalue + ch
    return retvalue

def digit_extract(value):
    retvalue = ''
    for v in value:
        if v in '0123456789': retvalue = retvalue + v
        elif retvalue == '': continue # We need not start from scratch.
        else: break # We need not any separated digits.
    return retvalue

def first_dir(path):
    while True:
        path, fname = os.path.split(path)
        if path == '': return fname
        elif path == '/': return os.path.join('/', fname)

def smart_archive(dist, unpackdir):
    cfgmap = { 'pkgpath' : dist.location,
               'pkgfile' : os.path.basename(dist.location) }
    if tarfile.is_tarfile(dist.location):
        tf = tarfile.open(dist.location, 'r:*')
        firstlist = map(lambda tfi: first_dir(tfi.name), tf.getmembers())
        tf.close()
    elif zipfile.is_zipfile(dist.location):
        zf = zipfile.ZipFile(dist.location)
        firstlist = map(lambda zfn: first_dir(zfn), zf.namelist())
        zf.close()
    else:
        return False, {}
    if firstlist == [firstlist[0]] *  len(firstlist):
        cfgmap['pkgdir'] = firstlist[0]
        cfgmap['unpackpath'] = os.path.join(unpackdir, cfgmap['pkgdir'])
        unpack_archive(dist.location, unpackdir)
    else:
        if dist.version == '': cfgmap['pkgdir'] = dist.project_name
        else: cfgmap['pkgdir'] = '%s-%s' % (dist.project_name, dist.version)
        cfgmap['unpackpath'] = os.path.join(unpackdir, cfgmap['pkgdir'])
        unpack_archive(dist.location, cfgmap['unpackpath'])
    return True, cfgmap
