# Author: Charles Wang <charlesw1234@163.com>

class PackageSystem(object):
    def __init__(self):
        pass

    def InitializeOptions(self, options):
        raise RuntimeError, 'It has to be overridden.'

    def FinalizeOptions(self, options):
        raise RuntimeError, 'It has to be overridden.'

    def GenPackage(self, pkgtype, args, options, cfgmap):
        raise RuntimeError, 'It has to be overridden.'

    def PostGenerate(self, name, version):
        pass
