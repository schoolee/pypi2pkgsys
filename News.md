# news page of pypi2pkgsys

# News of pypi2pkgsys #

## September 30, 2008 ##

0.1.0 is released after all packages are scanned and we can scan the new
added packages automatically. This is a milestone in my mind. :)

Full local mirror feature are finished, the PyPI can be mirrored offline in
local machine (with modification). This feature keep me from the dirty work
of link/download packages to unlinkable sites greatly. '--skip-logged' is
added to scan the unlogged packages only so I shall not have to remember which
packages are scanned already.

Some bugs are fixed too.

TODO:

**Add the support of deb for Ubuntu.** Add webapp template for web applications, such as Trac.

## September 13, 2008 ##

There are many enhancements of pypi2pkgsys in this week. I'm tring to let it
scan the PyPI index automatically. Most of the problems encountered can be
recorded automatically. And all log informations can be reported into the
specified log files without any handwork.

Now the PyPI packages which have only one python file is supported. Such as
"DeferArgs" and "googlecalc".

Wildcard in PyPI packages name is supported. pypi2pkgsys will search in
PyPI index and write ebuilds for all of the matched packages.

TODO:

The progress informations should be added, for example: How many packages are
processed and the total number of the packages in the current list.

For the packages which problem can be resolved easily, I shall try to provide
patches for them.

Scan more packages to find what problems might be encountered and try to
resolve them.

## September 7, 2008 ##

Now I'm working on the first scan of all PyPI packages. Of course there are
many packages in its list, more than 4000. And some packages are not released
in the standard way, so I have to cut them off now.

For example, some packages have only one python module file, and some packages
are built and installed with autoconf/automake/make. They need some other style
ebuild for them.

And there is not any download links in the package index for some packages,
I have to mask them too.

Now the check of  the packages which started with 'A', 'a', 'B', 'b', 'C', 'c',
'D', 'd', 'E', 'e', 'F', 'f', 'G'. 'g', 'H' have been done. I shall go on
in these days.

Now the pypi2pkgsys is stronger than the previous version. I believe after the
first scan of the PyPI, pypi2pkgsys will be usable for more than half of the
all packages in PyPI.

The version will be changed to '0.1.0' after this fisrt scan.