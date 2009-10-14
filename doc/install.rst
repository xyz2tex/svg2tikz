Installation guide
==================

Svg2TikZ has three different interfaces:

* An Inkscape extension.
* A command line tool.
* A python library.

.. _inkscape-install:

Installing for use with Inkscape
--------------------------------

Installing is as simple as copying the script (unless it resides in your path) and its INX files to the Inkscape extensions directory.

Windows

Copy the tikz_extport.py file and the tikz_export_effect.inx and tikz_export_output.inx files to your inkscape/share/extensions directory.
Linux and OSX

Copy the tikz_extport.py file and the tikz_export_effect.inx and tikz_export_output.inx files to your home/.inkscape/extensions directory. If you are using Inkscape 0.47 the directory is home/.config/inkscape/extensions.

Additionally you have to copy the following dependencies to the same directory as above:

    * inkex.py
    * simplestyle.py
    * simplepath.py 

The above files should be bundled with Inkscape. Look in the main extensions directory. You can also download them from the repository 


Installing for use as library or command line tool
--------------------------------------------------

Automatic installation via a package manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Svg2Tikz is registered on PyPi and may therefore be installed manually using
package managers like `easy_install
<http://peak.telecommunity.com/DevCenter/EasyInstall>`_ and `pip
<http://pip.openplans.org/>`_. 

Using ``easy_install``, type::

    easy_install svg2tikz


Using ``pip``, type::

    pip install svg2tikz
    
Depending on your system setup, you may have to write ``sudo easy_install ...`` or ``sudo pip ...``


Manual installation from a downloaded package
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Manual installation from a Mercurial checkout
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

