Command line guide
******************

You can get direct help from the command line with ``svg2tikz -h``

::

  usage: svg2tikz [-h] [--output OUTPUT] [--id IDS] [--selected-nodes SELECTED_NODES]
                [--codeoutput {standalone,codeonly,figonly}] [-t {math,escape,raw}]
                [--markings {ignore,include,interpret,arrows}] [--arrow {latex,stealth,to,>}]
                [--output-unit {mm,cm,m,in,pt,px,Q,pc}]
                [--input-unit {mm,cm,m,in,pt,px,Q,pc}] [--crop] [--clipboard] [--wrap]
                [--indent] [--latexpathtype] [--noreversey] [-r REMOVEABSOLUTE]
                [-m {output,effect,cli}] [--standalone] [--figonly] [--codeonly]
                [--scale SCALE] [-V] [--verbose]
                [INPUT_FILE]

  Doc string

  positional arguments:
    INPUT_FILE            Filename of the input file (default is stdin)

  options:
    -h, --help            show this help message and exit
    --output OUTPUT       Optional output filename for saving the result (default is stdout).
    --id IDS              id attribute of object to manipulate
    --selected-nodes SELECTED_NODES
                          id:subpath:position of selected nodes, if any
    --codeoutput {standalone,codeonly,figonly}
                          Amount of boilerplate code (standalone, figonly, codeonly).
    -t {math,escape,raw}, --texmode {math,escape,raw}
                          Set text mode (escape, math, raw). Defaults to 'escape'
    --markings {ignore,include,interpret,arrows}
                          Set markings mode. Defaults to 'ignore'
    --arrow {latex,stealth,to,>}
                          Set arrow style for markings mode arrow. Defaults to 'latex'
    --output-unit {mm,cm,m,in,pt,px,Q,pc}
                          Set output units. Defaults to 'cm'
    --input-unit {mm,cm,m,in,pt,px,Q,pc}
                          Set input units. Defaults to 'mm'
    --crop                Use the preview package to crop the tikzpicture
    --clipboard           Export to clipboard
    --wrap                Wrap long lines
    --indent              Indent lines
    --latexpathtype       Allow path modification for image
    --noreversey          Do not reverse the y axis (Inkscape axis)
    --removeabsolute REMOVEABSOLUTE
                          Remove the value of removeabsolute from image path
    -m {output,effect,cli}, --mode {output,effect,cli}
                          Extension mode (effect default)
    --notext              Ignore all text
    --standalone          Generate a standalone document
    --figonly             Generate figure only
    --codeonly            Generate drawing code only
    --scale SCALE         Apply scale to resulting image, defaults to 1.0
    -V, --version         Print version information and exit
    --verbose             Verbose output (useful for debugging)

Argument
========
The only positional argument is the input file which must be a valid svg file

Options
=======

Help
----
The option `-h`, `- -help` print the help

Output file
-----------
Select an output file the `- -output` option


Ids selections
--------------
Select the id of the element to export with the `- -id` option.
For multiple ids, multiple occurences of the option are allowed.

Output Type
-----------
Set the type of output that SVG2TikZ will output with the `- -codeoutput` option:

* `standalone` (default): a full `.tex` document
* `figonly`: only the code to produce the figure
* `codeonly`: only the tikz code

The option can also be set with:

* `- -standalone`
* `- -figonly`
* `- -codeonly`

Text mode
---------
Set how the text should be handled with `-t` option:

* `math`: the text will be inside a `$` math environnement
* `escape` (default): all special caracter will be escaped
* `raw`: the text will not be altered

The text can also be ignore with the `- -notext` option


Markings
--------
Set the marking mode with `- -markings`:

* `ignore` (default): no marking will be added
* `include`: Not available
* `interpret`: Using the given mapping between inkscape markers and TikZ markers
* `arrows`: Select the maker to use with the `- -arrow` option:

  * `latex`
  * `stealth`
  * `to`
  * `>`

Units
-----
Select the unit from the document (`- -input-unit`) to convert to the input of the `.tex` file (`- -output-unit`):

* `mm` (default input)
* `cm` (default output)
* `m`
* `in`
* `pt`
* `px`
* `Q`
* `pc`

Cropping the figure
-------------------
Crop the pdf to figure with the `- -crop` option.


Clipboard
---------
Export the tikz code directly to your clipboard with the `- -clipboard` option

Line wrapping
-------------
Wrap long lines with the `- -wrap` option.

Indent
------
Indent the code with the `- -indent` option.

Image
-----
If the option `- -latexpathtype` is set, the path to the image image will be shortened by the value of `- -removeabsolute`

Origin
------

The default origin of a svg file is the top left. The default origin of a tikz figure is the bottom left. The default behaviour of SVG2TikZ is to convert the origin of the svgfile to the origin of the tikz file. This option allow to keep the origin of the svg file.

Scaling
-------
Set the scaling of the tikz code with `- -scale`


Version
-------
Get the version of SVG2TikZ with `-v` / `- -version`

Verbosity
---------
Get a verbose output with `- -versbose`
