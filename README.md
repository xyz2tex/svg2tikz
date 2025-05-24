
<picture>
  <img alt="SVG2TikZ Logo" src="logo/svg2tikz.svg">
</picture>

[![Documentation][documentation-badge]][documentation-url]
[![PyPI version](https://badge.fury.io/py/svg2tikz.svg)](https://badge.fury.io/py/svg2tikz)

# SVG2TikZ 3.3.X (Inkscape 1.4.x compatible)


SVG2TikZ, formally known as Inkscape2TikZ ,are a set of tools for converting SVG graphics to TikZ/PGF code.
This project is licensed under the GNU GPL  (see  the [LICENSE](/LICENSE) file).

## Documentation and installation
`SVG2TikZ` is now available on pypi so you can install it with if you want to use it with a command line. You can install the package with the following command:

```
pip install svg2tikz
```

All the information to install (as an inkscape extension) and use `SVG2TikZ` can be found in our [Documentation](https://xyz2tex.github.io/svg2tikz/install.html).


## Changes and Bug fixes

A complete changelog is available in the [CHANGELOG.md](CHANGELOG.md) file.


[documentation-badge]: https://img.shields.io/website?up_message=Online&url=http%3A%2F%2Fxyz2tex.github.io%2Fsvg2tikz%2F&label=Doc
[documentation-url]: https://xyz2tex.github.io/svg2tikz

## Dependencies and contribution
All the dependencies are listed in the [pyproject.toml](pyproject.toml). There is no particular dependencies for testing. For building, the project use [poetry](https://python-poetry.org/).

For more information on how to contribute, you can check the [documentation](https://xyz2tex.github.io/svg2tikz/contribute.html).

## Troubleshooting

If you have error about `lxml` when trying to install `SVG2TikZ` you can check [this link](https://stackoverflow.com/questions/18025730/pygobject-2-28-6-wont-configure-no-package-gobject-introspection-1-0-found).
