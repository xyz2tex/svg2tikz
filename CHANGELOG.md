# Changelog

## [Unreleased]

### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security

## v3.1.0 - 19/05/2024

### Added
- Adding option to specify texmode via a SVG attribute (see --texmode)
- Adding tests to improve the coverage of the code
### Changed
### Deprecated
### Removed
### Fixed
- Fixed string encoding exception when using stdout as output
- Fixing multiple bugs along the code related to the news tests to improve the coverage
- Fixing typo in github action for pylint and tests
### Security

## v3.0.1 - 14/01/2024

### Added
- Version is now displayed in the inkscape extension
### Changed
### Deprecated
### Removed
### Fixed
- Fix bug with arc where angles values were not replaced
- Fix trailing slash on shebang
### Security

## v3.0.0 - 12/12/2023

### Added
- Adding support for text-anchor
- Rounding of all values + options to change the number of after decimal
- News tests for complete files
- Cleaning of the comments
- Basic colors are not redefined anymore
- Adding logo for SVG2TikZ
- Adding theme for doc of SVG2TikZ
- Adding autodoc
- Adding basic switch tag handle
- Adding failsafe for non defined sys.stdout.buffer
- Adding list of tikz color
- Adding dev dependencies group in the pyproject.toml
- Adding autodoc to generate code doc
- Adding example section in the doc
- Adding scaling on nodes
### Changed
- Using style from new inkex
- Using path from new inkex
- Using transform from new inkex
- Using colors from new inkex
- Using Vector2d from inkex instead of Point DataClass
- Removing input-options and using unit from viewbox
- Correcting licence in the pyproject
- Unify conversion of coordinate: (x, y)
- Convert_file and convert_svg functions are now directly accesible from root
- Try excepting non existing tags in a svg
- Changing the select file option in tikz effect to new file
### Deprecated
- Gradient are commented for the time being
### Removed
- GraphicState class
- ’nsplit’, ’chunks’, ’\_ns’, ’filter\_tag’, ’open\_anything’ functions
- License in the main file
### Fixed
- Transform working with --noreversey
- Fixing the installation of svg2tikz as command line tool
- Wrapping line now respect newline
- Fixing error on treating polylines and polygones
- Verbose option to add name of shapes and layers
- Converting line tag
- Transformation matrix for nodes
### Security

## v2.1.0 - 2023/06/28

### Added
### Changed
- Update version and authors to the doc
### Deprecated
### Removed
### Fixed
- Removing misplaced <br/> leading to warning from inkscape
- Typo in tag leading to mismtach and error from inkscape
- No rounded corners by default
- Correct unit of round corners
### Security

## v2.0.0 - 2023/05/04

### Added
- Tests for all functions and class
- Tests for complete svg document
- Github action for running test on PR
- `Kjell Magne Fauske` to authors in `pyproject.toml`
- Maintainer field in `pyproject.toml`
- Linting with pylint + github action
- Formating with black + github action
- Doc about contributing
- Template for issues
- Template for pull request

### Changed
- Moving the changelog from `README.md` to `CHANGELOG.md`
- Updating python package info
- Updating current Docs about module
- Running GH action for linting and test only when python files are modified
- Rework of the .inx files

### Fixed
- Fixing calc_arc function
- Fixing noreversy option
- Fixing error on path punch variable
- Fixing path selection for inkscape > 1.0.0

### Removed
- to/tikzoutput option as the output option already exist

## V1.2.0
- Adding option to set document unit `input-unit` and the output unit `output-unit`
- Now the tikz output used the unit define by `output-unit`
- Now the default behaviour will read the height of the svg and use the bottom left corner as reference
- This option can be disabled with --noreversey


## V1.1.1
- Supporting svg encoded in utf-8
- Simple `Symbol` handling
- Simple Arrow handling

## V1.1
- Publishing the package to Pypi
- Publishing the document to ReadTheDocs
- Fixing the translate error from matrix

## V1.0
- Now images can also be exported to tikz
- Added a variable `/def /globalscale` to the output tikz document (standalone and tikz figure)
- `/globalscale` when changed will scale the tikzfigure by transforming the vector coordinates.
- `/globalscale` when changed will scale the tikzfigure by scaling the embedded images
- The path element was not exported in correct coordinates. This is fixed
- Added an entry to specify the path to be removed from absolute paths in the images. This is useful to work in a latex project directly
