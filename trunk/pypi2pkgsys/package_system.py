# Author: Charles Wang <charlesw123456@gmail.com>

class package_system(object):
    def __init__(self):
        pass

    def sepline(self):
        print

    def begin(self, msg):
        # Show some action will be performed.
        print msg, '...',

    def end(self, success_ornot):
        # Show whether the action finished successfully.
        if success_ornot: print 'ok'
        else: print 'failed'

    def info(self, msg):
        # Show title.
        print msg

    def error(self, msg):
        # Show error.
        print msg

    def init_options(self, options):
        raise RuntimeError, 'It has to be overridden.'

    def finalize_options(self, options):
        raise RuntimeError, 'It has to be overridden.'

    def setup_args(self, args):
        raise RuntimeError, 'It has to be overridden.'

    def process(self, args):
        pass
