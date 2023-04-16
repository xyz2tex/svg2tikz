
.. _module-guide:

Module guide
============

.. module:: svg2tikz
   :synopsis: Interface to the SVG to TikZ converter

.. function:: convert_svg(filename_or_string, **kwargs)

   Main interface

   :param filename_or_string: Path to an SVG file or an SVG document stored in a string.
   :type filename_or_string: string
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
   :param makings: Marking mode. Allowed values:

        - ``ignore`` -- No marking (default)
        - ``include`` -- Not implemented
        - ``interpret`` -- Defined Mapping between inkscape and tikz markings
        - ``arrows`` -- Use the making defined by the arrow option
   :type t: string

   :param arrows: Tikz marking used in the marking mode. Allowed values:

        - ``latex``  (default)
        - ``stealth``
        - ``to``
        - ``>``
   :type t: string

   :param input-unit: Unit of the svg file. Allowed values:

        - ``mm`` (default)
        - ``cm``
        - ``m``
        - ``in``
        - ``pt``
        - ``px``
        - ``Q``
        - ``pc``
   :type t: string

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

        from svg2tikz import convert_svg

        code = convert_svg("example.svg", ids=['1', '2', 'id2'], verbose=True)
        code = convert_svg("example.svg", verbose=True)
