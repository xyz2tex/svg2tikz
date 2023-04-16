Installation guide
******************

Svg2TikZ can be used in three different ways:

* as an Inkscape extension
* as a command line tool
* as a python module

Dependencies
============

SVG2TikZ has the following dependencies:

* lxml_ (not required if SVG2TikZ is run as an inkscape extension)
* xclip_ or pbcopy_ (required only if you want clipboard support on Linux or Os X)
* inkex_ (not required if SVG2TiKz is run as an inkscape extension)

xclip_ is a command line tools available in most Linux distributions. Use your favorite package manager to install it. pbcopy_ is a command line tool available in OS X.

.. _lxml: http://lxml.de/
.. _pbcopy: http://developer.apple.com/library/mac/#documentation/Darwin/Reference/ManPages/man1/pbcopy.1.html
.. _xclip: http://sourceforge.net/projects/xclip/
.. _inkex: https://pypi.org/project/inkex/

.. _inkscape-install:

Installing for use with Inkscape
================================

SVG2TikZ is not bundled with Inkscape. You therefore have to install it manually.

The extension consists of the following files:

* ``tikz_export.py``, extension code
* ``tikz_export_effect.inx``, effect setup file
* ``tikz_export_output.inx``, output setup file

Which are located in the ``svg2tikz/extensions`` folder. Installing is as simple as copying the script and its INX files to the Inkscape extensions directory. The location of the extensions directory depends on which operating system you use:

Windows
    ``C:\Program Files\Inkscape\share\inkscape\extensions\``

Linux
    ``/usr/share/inkscape/extensions`` *or* ``~/.config/inkscape/extensions/``

Mac
    ``/Applications/Inkscape.app/Contents/Resources/extensions`` *or* ``~/.config/inkscape/extensions/``


Additionally the extension has the following dependencies:

* inkex_
* lxml_

The dependencies are bundled with Inkscape and normally you don't need to install them yourself. But in the case they are not her, look in the main extensions directory. You can also download them from the repository


Installing for use as library or command line tool
==================================================

SVG2TikZ started out as an Inkscape extension, but it can also be used as a standalone tool.

Automatic installation via a package manager
--------------------------------------------

SVG2TikZ is available on pypi_. You can install it directly with the following command:

``pip install svg2tikz``

.. _pypi: https://pypi.org/project/svg2tikz/


Manual installation from a Git checkout
---------------------------------------

- Clone this repository from GitHub, using
  ``git clone https://github.com/xyz2tex/svg2tikz.git``
- ``cd`` into ``svg2tikz``.
- For installation as a Python 3 package, type


  ::

    $ pip install .

You should now be able to import the ``svg2tikz`` module from the
Python 3 prompt without error:

::

   >>> import svg2tikz

For more information on the use of ``svg2tikz`` as a Python module,
see the :ref:`module-guide`.

Installation using ``pip`` also makes available the ``svg2tikz``
command-line tool; typically (for non-root installation), it will be in
the directory ``$HOME/.local/bin/``, so to run it, you need to ensure
that directory is on your PATH.
