# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
# License: BSD

import fcntl
import fnmatch
import hashlib
import os
import os.path
import re
import shutil
import sys
import urllib2
from UserDict import UserDict
from pypi2pkgsys.pypi_utils import reqstr2obj

class pypibase(object):
    def __init__(self, lockpath):
        self.lockfd = os.open(lockpath, os.O_WRONLY | os.O_CREAT | os.O_TRUNC)

    def __del__(self):
        os.close(self.lockfd)

    def lock(self):
        try: fcntl.lockf(self.lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            print 'Waiting the lock: ', self.lockfp.name
            fcntl.lockf(self.lockfd, fcntl.LOCK_EX)

    def unlock(self):
        fcntl.lockf(self.lockfd, fcntl.LOCK_UN)

class pypilog(pypibase):
    okvalue = 'OK!'
    logsep = '================================'
    def __init__(self, log_path):
        pypibase.__init__(self, '/var/lock/pypi2pkgsys.log.lock')
        self.log_path = log_path
        if self.log_path is not None:
            if not os.path.isfile(log_path):
                if os.path.exists(log_path): os.remove(log_path)
                shutil.copyfile(os.path.join(patchdir, 'pypi2pkgsys.log'),
                                log_path)
            self.load_from_file()

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
                logfp.write('\t%r\n' % msg)
        logfp.close()
        curstat = os.stat(self.log_path)
        self.st_mtime = curstat.st_mtime

    def check_broken(self, pkgname):
        if self.log_path is None: return
        if not self.check_update(): self.load_from_file()
        if pkgname not in self.pkginfo_map: return
        if self.pkginfo_map[pkgname] == self.okvalue: return
        print '%s: masked: %s' % (pkgname, self.pkginfo_map[pkgname])
        raise RuntimeError

    def get_stats(self):
        ok = 0
        for v in self.pkginfo_map.values():
            if v == self.okvalue: ok = ok + 1
        return (ok, len(self.pkginfo_map))

    def pkgname_ok(self, pkgname):
        print '%s: %s' % (pkgname, self.okvalue)
        if self.log_path is None: return
        self.lock()
        # Update it in the protection of lock.
        if not self.check_update(): self.load_from_file()
        self.pkginfo_map[pkgname] = self.okvalue
        #if pkgname in self.tmpfailed_map: del(self.tmpfailed_map[pkgname])
        self.save_to_file()
        self.unlock()

    def in_except(self, pkgname, msg):
        exc_value = sys.exc_info()[1]
        msg = '%s: %s' % (msg, exc_value)
        print '%s: %s' % (pkgname, msg)
        if self.log_path is None: return
        self.lock()
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
        self.unlock()

class pypicache(pypibase):
    pkgindex_format = """<html><head><title>Links for %(project_name)s</title></head><body><h1>Links for %(project_name)s</h1>
<a href='%(downloads_url)s/%(filename)s#md5=%(md5)s'>%(filename)s</a></br>
</body></html>
"""
    def __init__(self, cacheroot, cacheurl):
        pypibase.__init__(self, '/var/lock/pypi2pkgsys.cache.lock')
        self.simple_root = os.path.join(cacheroot, 'simple')
        self.downloads_url = cacheurl + '/downloads'

    def add_packages(self, distlist):
        self.lock()
        # Write project_name/index.html for all distributions.
        for dist in distlist:
            pkgfp = open(dist.location, 'rb')
            md5obj = hashlib.md5()
            md5obj.update(pkgfp.read())
            pkgfp.close()
            distdir = os.path.join(self.simple_root, dist.project_name)
            if not os.path.isdir(distdir): os.mkdir(distdir)
            distindex = open(os.path.join(distdir, 'index.html'), 'w')
            distindex.write(self.pkgindex_format % \
                                { 'project_name' : dist.project_name,
                                  'downloads_url' : self.downloads_url,
                                  'filename' : os.path.basename(dist.location),
                                  'md5' : md5obj.hexdigest() })
            del(md5obj)
            distindex.close()

        # Re-generate index.html.
        sindex = open(os.path.join(self.simple_root, 'index.html'), 'w')
        sindex.write('<html><head><title>Simple Index</title></head><body>\n')
        allpackages = os.listdir(self.simple_root)
        allpackages.sort()
        for pkg in allpackages:
            pkgpath = os.path.join(self.simple_root, pkg)
            pkgfile = os.path.join(pkgpath, 'index.html')
            if os.path.isdir(pkgpath) and os.path.isfile(pkgfile):
                sindex.write("<a href='%s/'>%s</a><br/>\n" % (pkg, pkg))
        sindex.write('</body></html>\n')

        self.unlock()

class reqmap(UserDict):
    valid_cr = re.compile('^[\w\d\-\_\.]+$')
    def __init__(self):
        UserDict.__init__(self)
        self.matchlist = []

    def append_arg(self, reqarg):
        if '*' in reqarg or '?' in reqarg: self.matchlist.append(reqarg)
        else: self.add(reqstr2obj(reqarg))

    def resolve_matchlist(self, logobj, pkgidx_url):
        if self.matchlist == []: return
        prefix = "<a href='"; sep = "/'>"; suffix = "</a><br/>"
        sockf = urllib2.urlopen(pkgidx_url)
        ln = sockf.readline()
        while ln:
            ln = ln.strip()
            lnidx = ln.find(sep)
            if lnidx > 0 and ln.startswith(prefix) and ln.endswith(suffix):
                s0 = ln[len(prefix):lnidx]
                s1 = ln[lnidx + len(sep): -len(suffix)]
                if s0 == s1: # A valid PyPI package name is recognized.
                    for match in self.matchlist:
                        if fnmatch.fnmatch(s0, match):
                            if self.valid_cr.match(s0) is None:
                                logobj.in_except(s0, 'Invalid name')
                            else:
                                self.add(reqstr2obj(s0))
                            break
            ln = sockf.readline()
        sockf.close()
        self.matchlist = []

    def reqobj_combine(self, reqobj0, reqobj1):
        if reqobj0.project_name != reqobj1.project_name:
            raise RuntimeError, \
                'Try to combine reqobj different project %s, %s.' %\
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

    def add(self, reqobj):
        name = reqobj.project_name
        if name not in self: self[name] = reqobj
        self[name] = self.reqobj_combine(reqobj, self[name])

    def reqobj_seq(self):
        klist = self.keys(); klist.sort()
        for idx in xrange(len(klist)):
            yield (idx, len(klist), self[klist[idx]])
