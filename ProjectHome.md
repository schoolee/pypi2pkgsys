Generate package files from PyPI index.

Now only ebuild for gentoo is generated. spec for rpm-base distribution,
dpkg for dpkg-base distribution will be added in future.

Many features are provided:
  * Pre-defined, user-defined schemes for different usage.
    * Update from PyPI and cached into localhost scheme is provided.
    * Update from localhost scheme is provided, so the package file will not have to be downloaded again and again.
  * Wildcard is permitted in package names. For example: [Aa](Aa.md)**.
  * Offline mirror support: Cache the downloaded packages and generate localhost cache entries index in the PyPI format. So we can treat our local-machine as a PyPI server.
  * Full automatically log, all passed or failed packages(with fail reason) are recorded in log.
  * Some packages can be masked for manually written ebuild/deb package.
  * Multiple template support, to support different packages types. Now only standard distutils/setuptools template and single python template are provided. More template, such as webapp, will be added in future.
  * Package specific config, patches supported. User can manage their private config, patches in /etc/pypi2pkgsys too.
  * pypi-logstats.py is provided to show the statistics from log files.
  * pypi-manualcache.py is provided to generate localhost cache entries from self-downloaded package files. This reserve a great deal of time to download big files from pypi.python.org.**

Links:
  * News: http://code.google.com/p/pypi2pkgsys/wiki/News
  * Main: http://code.google.com/p/pypi2pkgsys/wiki/Main
  * Usage:
    * http://code.google.com/p/pypi2pkgsys/wiki/Usage_pypi2portage
    * http://code.google.com/p/pypi2pkgsys/wiki/Usage_logstats
    * http://code.google.com/p/pypi2pkgsys/wiki/Usage_manualcache