# SVG2TikZ (Inkscape 1.x.x compatible)
[![Documentation Status](https://readthedocs.org/projects/svg2tikz/badge/?version=latest)](https://svg2tikz.readthedocs.io/en/latest/?badge=latest)
[![PyPI version](https://badge.fury.io/py/svg2tikz.svg)](https://badge.fury.io/py/svg2tikz)

SVG2TikZ, formally known as Inkscape2TikZ ,are a set of tools for converting SVG graphics to TikZ/PGF code.
This project is licensed under the GNU GPL  (see  the [LICENSE](/LICENSE) file).

## Documentation and installation
`SVG2TikZ` is now available on pypi so you can install it with if you want to use it with a command line. But the `inkex` package is not on pypi so you need first to add an extra url to repository:

```
export PIP_EXTRA_INDEX_URL=https://gitlab.com/api/v4/projects/40060814/packages/pypi/simple
```
Then you can install the package:

```
pip install svg2tikz
```
It is also true if you install the package from this repository.


All the informations to install (as an inkscape extension) and use `SVG2TikZ` can be found in our [Documentation](https://svg2tikz.readthedocs.io/en/latest).

## Changes, Bug fixes and Known Problems from the original

### V1.2.0
- Adding option to set document unit `input-unit` and the output unit `output-unit`
- Now the tikz output used the unit define by `output-unit`
- Now the default behaviour will read the height of the svg and use the bottom left corner as reference
- This option can be disabled with --noreversey


### V1.1.1
- Supporting svg encoded in utf-8
- Simple `Symbol` handling
- Simple Arrow handling

### V1.1
- Publishing the package to Pypi
- Publishing the document to ReadTheDocs
- Fixing the translate error from matrix

### V1.0
- Now images can also be exported to tikz
- Added a variable `/def /globalscale` to the output tikz document (standalone and tikz figure)
- `/globalscale` when changed will scale the tikzfigure by transforming the vector coordinates.
- `/globalscale` when changed will scale the tikzfigure by scaling the embedded images
- The path element was not exported in correct coordinates. This is fixed
- Added an entry to specify the path to be removed from absolute paths in the images. This is useful to work in a latex project directly

## Known Problems
- Currently only images that are "linked" in svg are exported. Base64 embed is not yet supported so avoid choosing embed option
- Grouped elements will not work. So ungroup everything
