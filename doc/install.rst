Installing SVG2TikZ
===================

Inkscape
--------

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

Python module
-------------