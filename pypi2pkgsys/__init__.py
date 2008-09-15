# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
# License: BSD

import os.path
from ConfigParser import ConfigParser

pkgroot = os.path.dirname(__file__)

class pypiconfig(object):
    def __init__(self, pkgroot, etcdir):
        self.sysdir = os.path.join(pkgroot, 'patches')
        self.etcdir = etcdir

        self.sysconfig = ConfigParser()
        self.sysconfig.read(os.path.join(self.sysdir, 'index.ini'))

        self.etcconfig = ConfigParser()
        if os.path.isfile(os.path.join(self.etcdir, 'index.ini')):
            self.etcconfig.read(os.path.join(self.etcdir, 'index.ini'))

    def has_section(self, secname):
        return self.etcconfig.has_section(secname) or \
            self.sysconfig.has_section(secname)

    def items(self, secname):
        if self.etcconfig.has_section(secname):
            for name, value in self.etcconfig.items(secname):
                yield (name, value)
        elif self.sysconfig.has_section(secname):
            for name, value in self.sysconfig.items(secname):
                yield (name, value)

    def patches(self, secnamelist):
        for pconfig, pdir in [(self.etcconfig, self.etcdir),
                              (self.sysconfig, self.sysdir)]:
            for secname in secnamelist:
                if pconfig.has_option(secname, 'patches'):
                    plist = pconfig.get(secname, 'patches').split()
                    for pfn in plist:
                        yield os.path.join(pdir, pfn)
                    return

config = pypiconfig(pkgroot, os.path.join('/etc', 'pypi2pkgsys'))
