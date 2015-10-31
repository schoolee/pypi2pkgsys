# usage page of pypi-manualcache.py

# Usage of pypi-manualcache.py #

There are some big files which have to be downloaded again and again from
pypi.python.org. For example, the size of basemap is 97M!. And pypi.python.org
is very slow for me, so I want to download it from other faster site and cache
it in my localhost. pypi-manualcache.py is usable here.

pypi-manualcache.py check the downloaded file and generate pypi index in the
document directory of localhost.

After the package and package file is cached in localhost, we can use local
scheme to access them without any remote network actions.

## Command line ##

```
# pypi-manualcache.py CACHEROOT CACHEURL PKGFN,PKGNAME ...
```

The provided packages will be copied into CACHEROOT/downloads, and they can be
accessed from CACHEURL/downloads/PKGFN. The PKGNAME is the package name for
the package file used in PyPI.

## Example ##

```
# pypi-manualcache.py /var/www/localhost/htdocs/pypicache http://127.0.0.1/pypicache basemap-0.99.1.tar.gz,basemap athenaCL.tar.gz,athenaCL
```