# Author: Charles Wang <charlesw1234@163.com>

from setuptools import Command

class dump(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        values = {}
        for opt in ['name', 'version', 'description', 'author', 'author_email',
                    'license', 'long_description', 'keywords', 'url',
                    'classifiers']:
            try:
                values[opt] = getattr(self.distribution.metadata, opt)
            except AttributeError:
                pass
        for opt in ['install_requires',
                    'extras_require',
                    'entry_points']:
            try:
                values[opt] = getattr(self.distribution, opt)
            except AttributeError:
                pass
        print '**** PyPI2PkgSys ****'
        print repr(values)
