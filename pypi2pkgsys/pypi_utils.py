# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
# License: BSD

import os.path
import popen2
import shutil
import tarfile
import zipfile
from setuptools.archive_util import unpack_archive

from pypi2pkgsys import patchdir, config

pkg2license = {}
if config.has_section('pkg2license'):
    for name, value in config.items('pkg2license'):
        pkg2license[name] = value

broken = {}
broken_file = file(os.path.join(patchdir, 'broken.txt'))
ln = broken_file.readline()
while ln:
    name, value = ln.split('=', 1)
    name = name.strip(); value = value.strip()
    broken[name] = value
    ln = broken_file.readline()
broken_file.close()
del(broken_file)
del(ln)

def check_broken(pkgname):
    if pkgname in broken: raise RuntimeError, broken[pkgname]

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
        raise RuntimeError, 'Unrecognized archive format: %s' % dist.location
    if firstlist == [firstlist[0]] *  len(firstlist):
        cfgmap['pkgdir'] = firstlist[0]
        cfgmap['unpackpath'] = os.path.join(unpackdir, cfgmap['pkgdir'])
        unpack_archive(dist.location, unpackdir)
    else:
        if dist.version == '': cfgmap['pkgdir'] = dist.project_name
        else: cfgmap['pkgdir'] = '%s-%s' % (dist.project_name, dist.version)
        cfgmap['unpackpath'] = os.path.join(unpackdir, cfgmap['pkgdir'])
        unpack_archive(dist.location, cfgmap['unpackpath'])
    return cfgmap

def check_package_type(unpackpath):
    if os.path.isfile(os.path.join(unpackpath, 'setup.py')):
        return 'setup.py'
    return None

def fix_setup(unpackpath):
    setup_path = os.path.join(unpackpath, 'setup.py')
    modified = False; add_import = False
    setup_fp = file(setup_path)
    linearr = setup_fp.read().splitlines(True)
    reslinearr = []
    for line in linearr:
        lnsplit = line.split()
        if 'distutils.core.setup' in line:
            #import distutils ... distutils.core.setup
            add_import = True
            line = line.replace('distutils.core.setup',
                                'setuptools.setup')
        elif 'core.setup' in line:
            #from distutils import core ... core.setup
            add_import = True
            line = line.replace('core.setup', 'setuptools.setup')
        elif len(lnsplit) >= 4 and lnsplit[0] == 'from' and \
                lnsplit[1] == 'distutils.core' and lnsplit[2] == 'import' \
                and 'setup' in line:
            # from distutils.core import setup
            modified = True
            line = line.replace('distutils.core', 'setuptools')
        reslinearr.append(line)
    if modified or add_import:
        setup_fp = file(setup_path, 'w')
        if add_import: setup.fp.write('import setuptools\n')
        setup_fp.write(''.join(reslinearr))
        setup_fp.close()

popen_fmt = '(cd %s; python setup.py dump)'
def get_package_args(unpackpath):
    p = popen2.popen2(popen_fmt % unpackpath)
    p[1].close()
    ln = p[0].readline()
    while ln:
        if ln.strip() == '**** PyPI2PkgSys ****': break
        ln = p[0].readline()
    if not ln: raise RuntimeError, 'dump does not work.'
    c = p[0].readline()
    p[0].close()
    args = eval(c)
    shutil.rmtree(unpackpath)
    return args

def fix_args(pkgname, args):
    if pkgname in pkg2license: args['license'] = pkg2license[pkgname]
    elif 'license' not in args: args['license'] = 'UNKNOWN'
    if 'install_requires' not in args or \
            args['install_requires'] is None:
        args['install_requires'] = []
    if 'extras_require' not in args or \
            args['extras_require'] is None:
        args['extras_require'] = {}
    return args
