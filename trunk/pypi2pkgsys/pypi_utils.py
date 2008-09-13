# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
# License: BSD

import fcntl
import fnmatch
import os.path
import popen2
import re
import shutil
import sys
import tarfile
import urllib2
import zipfile
from pkg_resources import parse_requirements
from setuptools.archive_util import unpack_archive

from pypi2pkgsys import patchdir

pkg2license = {}
pkg2license['Adaptation'] = 'UNKNOWN'
pkg2license['brian'] = 'CeCILL-2'
pkg2license['config'] = 'UNKNOWN'
pkg2license['dbmigrate'] = 'BSD'
pkg2license['Durus'] = 'CNRI'
pkg2license['encutils'] = 'LGPL-3'
pkg2license['ftputil'] = 'BSD'
pkg2license['fui'] = 'GPL-3'
pkg2license['Geohash'] = 'GPL-3'
pkg2license['logging'] = 'MIT'
pkg2license['meld'] = 'ZPL'
pkg2license['qpy'] = 'BSD'
pkg2license['Quixote'] = 'CNRI-QUIXOTE-2.4'
pkg2license['pytz'] = 'MIT'

class pypilog(object):
    lockpath = '/var/lock/pypi2pkgsys.log.lock'
    okvalue = 'OK!'
    logsep = '================================'
    def __init__(self, log_path):
        self.log_path = log_path
        if self.log_path is not None:
            self.lockfd = os.open(self.lockpath,
                                  os.O_WRONLY | os.O_CREAT | os.O_TRUNC)
            if not os.path.isfile(log_path):
                if os.path.exists(log_path): os.remove(log_path)
                shutil.copyfile(os.path.join(patchdir, 'pypi2pkgsys.log'),
                                log_path)
            self.load_from_file()

    def __del__(self):
        if self.log_path is not None:
            os.close(self.lockfd)

    def check_update(self):
        curstat = os.stat(self.log_path)
        return self.st_mtime >= curstat.st_mtime

    def load_from_file(self):
        logfp = open(self.log_path)
        curstat = os.stat(self.log_path)
        self.st_mtime = curstat.st_mtime
        self.pkginfo_map = {}; self.tmpfailed_map = {}
        # Load self.pkginfo_map
        ln = logfp.readline()
        while ln and ln.strip() != self.logsep:
            krepr, vrepr = ln.split('\t')
            k = eval(krepr); v = eval(vrepr)
            self.pkginfo_map[k] = v
            ln = logfp.readline()
        # Load self.tmpfailed_map
        if ln: ln = logfp.readline()
        curkey = None; curlist = []
        while ln and ln.strip() != self.logsep:
            if ln[0] != '\t':
                if curkey != None and curlist != []:
                    self.tmpfailed_map[curkey] = curlist
                curkey = eval(ln.strip())
                curlist = []
            else:
                curlist.append(eval(ln.strip()))
            ln = logfp.readline()
        if curkey != None and curlist != []:
            self.tmpfailed_map[curkey] = curlist
        # No further content.
        logfp.close()

    def save_to_file(self):
        # Lock must be acquired.
        logfp = open(self.log_path, 'w')
        karr = self.pkginfo_map.keys(); karr.sort()
        for k in karr: logfp.write('%r\t%r\n' % (k, self.pkginfo_map[k]))
        logfp.write(self.logsep + '\n')
        karr = self.tmpfailed_map.keys(); karr.sort()
        for k in karr:
            logfp.write('%r\n' % k)
            for msg in self.tmpfailed_map[k]:
                logfp.write('\t%r\n', msg)
        logfp.close()
        curstat = os.stat(self.log_path)
        self.st_mtime = curstat.st_mtime

    def check_broken(self, pkgname):
        if self.log_path is not None: return
        if not self.check_update(): self.load_from_file()
        if pkgname not in self.pkginfo_map: return
        if self.pkginfo_map[pkgname] == self.okvalue: return
        print '%s: masked: %s' % (pkgname, self.pkginfo_map[pkgname])
        raise RuntimeError

    def pkgname_ok(self, pkgname):
        print '%s: %s' % (pkgname, self.okvalue)
        if self.log_path is None: return
        self._acq_lock()
        # Update it in the protection of lock.
        if not self.check_update(): self.load_from_file()
        self.pkginfo_map[pkgname] = self.okvalue
        if pkgname in self.tmpfailed_map: del(self.tmpfailed_map[pkgname])
        self.save_to_file()
        self._rel_lock()

    def in_except(self, pkgname, msg):
        exc_value = sys.exc_info()[1]
        print '%s: %s: %s' % (pkgname, msg, exc_value)
        if self.log_path is None: return
        self._acq_lock()
        # Update it in the protection of lock.
        if not self.check_update(): self.load_from_file()
        if pkgname in self.pkginfo_map:
            if self.pkginfo_map[pkgname] == self.okvalue:
                if pkgname in self.tmpfailed_map:
                    self.tmpfailed_map[pkgname].append(msg)
                else:
                    self.tmpfailed_map[pkgname] = [msg]
            else:
                self.pkginfo_map[pkgname] = msg
        else:
            self.pkginfo_map[pkgname] = msg
        self.save_to_file()
        self._rel_lock()

    def _acq_lock(self):
        try: fcntl.lockf(self.lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            print 'Waiting the lock: ', self.lockpath
            fcntl.lockf(self.lockfd, fcntl.LOCK_EX)

    def _rel_lock(self):
        fcntl.lockf(self.lockfd, fcntl.LOCK_UN)

valid_cr = re.compile('^[\w\d\-\_\.]+$')
def pypi_match(logobj, matchlist, url = 'http://pypi.python.org/simple'):
    prefix = "<a href='"; sep = "/'>"; suffix = "</a><br/>"
    result = []
    sockf = urllib2.urlopen(url)
    ln = sockf.readline()
    while ln:
        ln = ln.strip()
        lnidx = ln.find(sep)
        if lnidx > 0 and ln.startswith(prefix) and ln.endswith(suffix):
            s0 = ln[len(prefix):lnidx]
            s1 = ln[lnidx + len(sep): -len(suffix)]
            if s0 == s1: # A valid PyPI package name is recognized.
                for match in matchlist:
                    if fnmatch.fnmatch(s0, match):
                        if valid_cr.match(s0) is None:
                            logobj.in_except(s0, 'Invalid name')
                        else:
                            result.append(s0)
                        break
        ln = sockf.readline()
    sockf.close()
    return result

def reqstr2obj(reqstr):
    return list(parse_requirements([reqstr]))[0]

def reqobj_combine(reqobj0, reqobj1):
    if reqobj0.project_name != reqobj1.project_name:
        raise RuntimeError, \
            'Requirements for different project %s, %s can not be combined.' %\
            (reqobj0.project_name, reqobj1.project_name)
    extras = reqobj0.extras
    for e1 in reqobj1.extras:
        if e1 not in extras: extras.append(e1)
    extras = ','.join(extras)
    if extras: extras = '[%s]' % extras
    specs = [''.join(s) for s in reqobj0.specs]
    for s1 in [''.join(s) for s in reqobj1.specs]:
        if s1 not in specs: specs.append(s1)
    specs = ','.join(specs)
    return reqstr2obj('%s%s%s' % (reqobj0.project_name, extras, specs))

def reqmap_add(reqmap, reqobj):
    name = reqobj.project_name
    if name not in reqmap: reqmap[name] = reqobj
    reqmap[name] = reqobj_combine(reqobj, reqmap[name])

def smart_archive(args, dist, unpackdir):
    # Set pkgpath, pkgfile, pkgdir, unpackpath, pkgtype.
    # setup_path is optional.
    def check_filename(fname, isfile, leading_dir, single_file, setup_path):
        def first_dir(path, isfile):
            while True:
                path, fname = os.path.split(path)
                if path == '':
                    if isfile: return ''
                    else: return fname
                elif path == '/':
                    if isfile: return '/'
                    else: return os.path.join('/', fname)
                isfile = False

        if leading_dir is None: leading_dir = first_dir(fname, isfile)
        elif leading_dir is False: pass
        elif leading_dir != first_dir(fname, isfile): leading_dir = False

        if isfile:
            if single_file is None: single_file = fname
            elif single_file is False: pass
            else: single_file = False

        if isfile and os.path.basename(fname) == 'setup.py':
            if setup_path is None: setup_path = fname
            elif len(fname) < len(setup_path): setup_path = fname
        return leading_dir, single_file, setup_path

    args['pkgpath'] = dist.location
    args['pkgfile'] = os.path.basename(dist.location)
    leading_dir = None; single_file = None; setup_path = None
    if tarfile.is_tarfile(dist.location):
        tf = tarfile.open(dist.location, 'r:*')
        for tfi in tf.getmembers():
            leading_dir, single_file, setup_path = \
                check_filename(tfi.name, tfi.isfile(),
                               leading_dir, single_file, setup_path)
        tf.close()
    elif zipfile.is_zipfile(dist.location):
        zf = zipfile.ZipFile(dist.location)
        for zfn in zf.namelist():
            leading_dir, single_file, setup_path = \
                check_filename(zfn, True,
                               leading_dir, single_file, setup_path)
        zf.close()
    else:
        raise RuntimeError, 'Unrecognized archive format: %s' % dist.location

    if leading_dir is None or single_file is None:
        raise RuntimeError, 'Empty package encountered: %s' % dist.location
    elif leading_dir is False:
        if dist.version == '': args['pkgdir'] = dist.project_name
        else: args['pkgdir'] = '%s-%s' % (dist.project_name, dist.version)
        args['unpackpath'] = os.path.join(unpackdir, args['pkgdir'])
        unpack_archive(dist.location, args['unpackpath'])
    else:
        args['pkgdir'] = leading_dir
        args['unpackpath'] = os.path.join(unpackdir, args['pkgdir'])
        unpack_archive(dist.location, unpackdir)
        if setup_path is not None:
            if setup_path == os.path.join(leading_dir, 'setup.py'):
                setup_path = 'setup.py'
            else:
                setup_path = None
    if setup_path is not None:
        args['setup_path'] = setup_path
        args['pkgtype'] = 'setup.py'
    elif single_file is not False:
        args['pkgtype'] = 'single'
    else:
        raise RuntimeError, 'Unsupported archive type'

def fix_setup(setup_path):
    modified = False; add_import = False
    setup_fp = open(setup_path)
    linearr = setup_fp.read().splitlines(True)
    reslinearr = []
    for line in linearr:
        lnsplit = line.split()
        # ( have to be added to avoid convert setup_xxx.
        # FIX ME: If somebody add spaces between distutils.core.setup and (, ...
        if 'distutils.core.setup(' in line:
            #import distutils ... distutils.core.setup
            add_import = True
            line = line.replace('distutils.core.setup(',
                                'setuptools.setup(')
        # FIX ME: If somebody add spaces between core.setup and (, ...
        elif 'core.setup(' in line:
            #from distutils import core ... core.setup
            add_import = True
            line = line.replace('core.setup(', 'setuptools.setup(')
        elif len(lnsplit) >= 4 and lnsplit[0] == 'from' and \
                lnsplit[1] == 'distutils.core' and lnsplit[2] == 'import' \
                and 'setup' in line:
            # from distutils.core import setup
            modified = True
            line = line.replace('distutils.core', 'setuptools')
        reslinearr.append(line)
    if modified or add_import:
        setup_fp = open(setup_path, 'w')
        if add_import: setup_fp.write('import setuptools\n')
        setup_fp.write(''.join(reslinearr))
        setup_fp.close()

popen_fmt = '(cd %s; python setup.py dump)'
def get_package_args(args):
    p = popen2.popen3(popen_fmt % args['unpackpath'])
    p[1].close()
    ln = p[0].readline()
    while ln:
        if ln.strip() == '**** PyPI2PkgSys ****': break
        ln = p[0].readline()
    if ln: # We got result.
        c = p[0].readline()
        p[0].close()
        newargs = eval(c)
        shutil.rmtree(args['unpackpath'])
        for k in newargs.keys():
            if k not in args: args[k] = newargs[k]
            else: raise RuntimeError, 'args key conflict: %s' % k
        p[2].close()
    else: # Some error encountered.
        p[0].close()
        cr = re.compile('\w+Error:\s+')
        ln = p[2].readline()
        while ln:
            if cr.match(ln):
                p[2].close()
                raise RuntimeError, ln.strip()
            ln = p[2].readline()
        raise RuntimeError

def fix_args(args, pkgname):
    if pkgname in pkg2license: args['license'] = pkg2license[pkgname]
    elif 'license' not in args: args['license'] = 'UNKNOWN'
    if 'install_requires' not in args or \
            args['install_requires'] is None:
        args['install_requires'] = []
    if 'extras_require' not in args or \
            args['extras_require'] is None:
        args['extras_require'] = {}
