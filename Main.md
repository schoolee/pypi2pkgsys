#main page of pypi2pkgsys

# pypi2pkgsys #

## Why not easy\_install? ##

Now Python packages are distributed through PyPI(Python Package Index), they
can be installed by easy\_install which is provided by setuptools.

But most of the linux user is using some distribution, such as Gentoo, Ubuntu
or Fedora. They manage all installed software packages by different package
management tools. For example, gentoo provide portage, ubuntu use dpkg and
fedora use rpm. These package management tools install/uninstall softwares and
manage the dependencies between them. Some other features, such as package
listing, file quering, are provided. These additional features help the system
administrator greatly.

If we install PyPI packages by easy\_install, so the distribution package
management will not believe they are installed. If some other software require
PyPI packages which are installed by easy\_install, the distribution package
management tool will install it again. And usally, the packages provided by
distribution are not updated frequently as the PyPI list. For example, Pylons
in gentoo portage is 0.9.4.1, but the latest version provided in PyPI is
0.9.7rc1 now. Two or more versions of the same packages might be installed in
this case. This problem mess my /usr/lib/python2.5/site-packages.

So I want to generate package files from the PyPI list automatically. If we can
install them automatically by easy\_install, why we can not generate packages
files from PyPI list?

We shall benefit from all features provided by distribution package management
tools if we generate package files from PyPI list and then install PyPI
packages by distribution package management tools but not easy\_install. In this
way, we shall avoid dup-install, version conflict of the PyPI packages. And can
get the latest packages easily in the same time.

## Difficulties ##

We know that there are many differencies between different packages because
they are developed by different developers. And these packages are changed at
any time.

So the distribution package maintainers have to maintain their package files
with the evolving of the managed packages.

The rules of PyPI list reduce this mess fact but can not eliminate it.

In fact, pypi2pkgsys can be treated as a sub-part of the whole distribution
package management tools. Because the exists of the rules of PyPI list, most of
the packages provided by PyPI can be installed automatically and do not need
any more adjustment. For these packages, we generate package files
automatically to simplify the work of the distribution maintainer.

But there are still some inconsistencies between PyPI packages, we resolve
these problems by provide patch, mask it out, or make pypi2pkgsys more smart.

For the widespread problem, such as using distutils but not setuptools, we can
enhance the pypi2pkgsys to make it more smart. And we shall not be distribbed
by this problems again.

For the package specific problem, we can define a patch to fix it. Or even mask
it out and maintain it by hand. This will keep pypi2pkgsys from unnecessary
complexity.

## Usage ##

Now pypi2pkgsys can generate ebuild for gentoo portage only. Global options
are:
  * --url: provide the url of PyPI list. The default value is http://pypi.python.org/simple
  * --download-dir: Where to save the downloaded packages. The default value is /var/tmp/pypi/downloads
  * --unpack-dir: Where to unpack the downloaded packages. The default value is /var/tmp/pypi/unpack

Portage specific options are:
  * --portage-distfiles: The directory where the portage to store its package files. The default value is /usr/portage/distfiles.
  * --portage-dir: The directory where the generated ebuild will be saved. The default value is /usr/local/portage/dev-python.

## Examples ##
```
pypi2portage setuptools docutils
```
The new generated ebuilds will be saved into /usr/local/portage/dev-python.
And then
```
emerge setuptools docutils
```