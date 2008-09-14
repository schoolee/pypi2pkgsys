# Author: Charles Wang <charlesw123456@gmail.com>

class package_system(object):
    def __init__(self):
        pass

    def init_options(self, options):
        raise RuntimeError, 'It has to be overridden.'

    def finalize_options(self, options):
        raise RuntimeError, 'It has to be overridden.'

    def setup_args(self, args):
        raise RuntimeError, 'It has to be overridden.'

    def process(self, args):
        pass
