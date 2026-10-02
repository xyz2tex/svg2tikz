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

.. _lxml: https://lxml.de/
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
    ``C:\Program Files\Inkscape\share\inkscape\extensions\`` *or* if installed through the Windows Store ``C:\Users\<USERNAME>\AppData\Local\Packages\25415Inkscape.Inkscape_9waqn51p1ttv2\LocalCache\Roaming\inkscape\extensions`` (change ``USERNAME`` for the name of the user and ``25415Inkscape.Inkscape_9waqn51p1ttv2`` to your local name)

Linux
    ``/usr/share/inkscape/extensions`` *or* ``~/.config/inkscape/extensions/``

Mac
    ``/Applications/Inkscape.app/Contents/Resources/share/inkscape/extensions/`` *or* ``~/Library/Application Support/org.inkscape.Inkscape/config/inkscape/extensions/``


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

If ``pip`` fails while building ``PyGObject``
---------------------------------------------

``pip install svg2tikz`` also pulls in PyGObject_, which inkex_ uses to talk to
the Inkscape user interface. PyGObject is compiled during installation and
needs the GObject introspection development files, so the installation can
stop with an error that mentions ``gobject-introspection-1.0``,
``girepository-2.0`` or ``pkg-config``. This is common on Windows and on Linux
systems without the development package installed.

Converting files from the command line or from Python does not use PyGObject,
so you can work around the error in one of two ways:

* Install the missing system package and run ``pip install svg2tikz`` again.
  For example ``sudo apt install libgirepository1.0-dev gir1.2-girepository-2.0``
  on Debian or Ubuntu, ``sudo dnf install gobject-introspection-devel`` on
  Fedora, or ``brew install gobject-introspection`` on macOS with Homebrew.
* On Windows, skip it. ``inkex`` itself does not need PyGObject on Windows, so
  install the other dependencies first and then SVG2TikZ without its dependency
  check::

    $ pip install lxml inkex
    $ pip install --no-deps svg2tikz

  To upgrade an installation that already has its dependencies, use
  ``pip install --upgrade --no-deps svg2tikz``.

The Inkscape extension is not affected either way, since Inkscape ships its own
copy of ``inkex``.

.. _PyGObject: https://pygobject.gnome.org/


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
