
.. _module-guide:

package guide
=============


.. argparse::
   :module: svg2tikz.tikz_export
   :func: return_arg_parser_doc
   :prog: svg

Wip
====

.. module:: svg2tikz
   :synopsis: Interface to the SVG to TikZ converter

.. function:: convert_file(filename_or_stream, no_output=True, **kwargs)

   Main interface

   :param filename_or_stream: Path to an SVG file or a stream to a SVG document.
   :type filename_or_stream: string
   :param no_output: Set the output of the converter to None
   :type no_output: bool
   :param returnstring: Return the output code as as string
   :type returnstring: bool
   :param ids: A list of path ids to convert
   :type ids: list of strings
   :param wrap: Wrap generated code lines
   :type wrap: bool
   :param crop: Crop figure using the preview package
   :type crop: bool
   :param codeoutput: Amount of code to generate. Allowed values:

        - ``standalone`` -- output a standalone document (default)
        - ``figonly`` -- wrap code in a ``tikzpicture`` environment
        - ``codeonly``
   :type codeoutput: string
   :param t: Text mode. Allowed values:

        - ``math`` -- output the text in a $ math environment
        - ``escape`` -- escape the tex characters (default)
        - ``raw`` -- do not modify the text
   :type t: string
   :param markings: Marking mode. Allowed values:

        - ``ignore`` -- No marking (default)
        - ``include`` -- Not implemented
        - ``interpret`` -- Defined Mapping between inkscape and tikz markings
        - ``arrows`` -- Use the making defined by the arrow option
   :type t: string

   :param arrow: Tikz marking used in the marking mode. Allowed values:

        - ``latex``  (default)
        - ``stealth``
        - ``to``
        - ``>``
   :type t: string

   :param round-number: Number after the decimal after rounding
   :type round-number: integer

   :param output-unit: Unit of the tikz file. Allowed values:

        - ``mm``
        - ``cm`` (default)
        - ``m``
        - ``in``
        - ``pt``
        - ``px``
        - ``Q``
        - ``pc``
   :type t: string

   :param indent: indent the tikz code
   :type indent: bool

   :param noreversey: keep the origin in the svg convention (top left) instead of converting it to the origin of the tikz convention (bottom left)
   :type noreversey: bool

   :param latexpathtype: Allow path modification for image
   :type latexpathtype: bool

   :param removeabsolute: Remove specified part form path
   :type removeabsolute: string

   :param notext: The text will be ignored
   :type notext: bool

   :param standalone: Set the codeoutput to standalone
   :type standalone: bool

   :param figonly: Set the codeoutput to figonly
   :type figonly: bool

   :param codeonly: Set the codeoutput to codeonly
   :type codeonly: bool

   :param scale: Apply the scale factor to the figure
   :type scale: float


   :rtype: string or None

   Examples::

        from svg2tikz import convert_file

        code = convert_file("example.svg", ids=['1', '2', 'id2'], verbose=True)
        code = convert_file("example.svg", verbose=True)


.. function:: convert_svg(filename_or_string, **kwargs)

   All the parameter are the same as convert_file


   Examples::

        from svg2tikz import convert_svg

        var_svg = """<svg>
        ...
        </svg>"""
        code = convert_svg(var_svg, ids=['1', '2', 'id2'], verbose=True)
