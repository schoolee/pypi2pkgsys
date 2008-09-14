#!/usr/bin/python
# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
# License: BSD

import sys
from pypi2pkgsys.pypi_objects import pypilog

for log_path in sys.argv[1:]:
    logobj = pypilog(log_path)
    ok, total = logobj.get_stats()
    bad = total - ok
    if total == 0: print '%s: empty.'
    else: print '%s: %d(%5.2f%%) ok, %d(%5.2f%%) bad.' % \
            (log_path, ok, ok * 100.0 / total, bad, bad * 100.0 / total)
    del(logobj)
