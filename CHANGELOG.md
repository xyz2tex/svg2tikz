# Changelog

## [Unreleased]

### Added
### Changed
- Update version and authors to the doc
### Deprecated
### Removed
### Fixed
- Removing misplaced <br/> leading to warning from inkscape
- Typo in tag leading to mismtach and error from inkscape
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
