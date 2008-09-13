# Copyright (C) 2008, Charles Wang <charlesw123456@gmail.com>
# Author: Charles Wang <charlesw123456@gmail.com>
# License: BSD

import filecmp
import os
import os.path

def ensure_dir(dir):
    if not os.path.isdir(dir): os.makedirs(dir)

def smart_write(output, template, args):
    tf = open(template); tmpl = tf.read(); tf.close()
    content = tmpl % args
    if os.path.isfile(output) or os.path.islink(output):
        f = open(output)
        orig_content = f.read()
        f.close()
        if orig_content == content: return False
    f = open(output, 'w')
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

def cut_parentheses(value):
    retvalue = ''; lvl = 0
    for ch in value:
        if ch == '(': lvl = lvl + 1
        elif ch == ')': lvl = lvl - 1
        elif lvl == 0: retvalue = retvalue + ch
    return retvalue
