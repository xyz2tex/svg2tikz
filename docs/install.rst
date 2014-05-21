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

xclip_ is a command line tools available in most Linux distributions. Use your favorite package manager to install it. pbcopy_ is a command line tool available i OS X.   

.. _lxml: http://lxml.de/
.. _pbcopy: http://developer.apple.com/library/mac/#documentation/Darwin/Reference/ManPages/man1/pbcopy.1.html
.. _xclip: http://sourceforge.net/projects/xclip/
.. _inkscape-install:

Installing for use with Inkscape
================================

SVG2TikZ is not bundled with Inkscape. You therefore have to install it manually. 

The extension consists of the following files:

* ``tikz_export.py``, extension code
* ``tikz_export_effect.inx``, effect setup file
* ``tikz_export_output.inx``, output setup file

Installing is as simple as copying the script and its INX files to the Inkscape extensions directory. The location of the extensions directory depends on which operating system you use:

Windows
    ``C:\Program Files\Inkscape\share\extensions\``

Linux
    ``/usr/share/inkscape/extensions`` *or* ``~/.config/inkscape/extensions/``

Mac
    ``/Applications/Inkscape.app/Contents/Resources/extensions`` *or* ``~/.config/inkscape/extensions/``


Additionally the extension has the following dependencies:

* ``inkex.py``
* ``simplestyle.py``
* ``simplepath.py``
* lxml_

The dependencies are bundled with Inkscape and normally you don't need to install them yourself. However, if the extension is not loaded, copy the following files to the same directory as you put the ``tikz_export*`` files. 

    * ``inkex.py``
    * ``simplestyle.py``
    * ``simplepath.py``

The above files should be bundled with Inkscape. Look in the main extensions directory. You can also download them from the repository 


Installing for use as library or command line tool
==================================================

SVG2TikZ started out as an Inkscape extension, but it can also be used as a standalone tool.  

Automatic installation via a package manager
--------------------------------------------

Svg2Tikz is registered on PyPi and may therefore be installed automatically using
package managers like `easy_install
<http://peak.telecommunity.com/DevCenter/EasyInstall>`_ and `pip
<http://pip.openplans.org/>`_. 

Using ``easy_install``, type::

    easy_install svg2tikz


Using ``pip``, type::

    pip install svg2tikz
    
Depending on your system setup, you may have to write ``sudo easy_install ...`` or ``sudo pip ...``


Manual installation from a downloaded package
---------------------------------------------

Manual installation from a Mercurial checkout
---------------------------------------------


