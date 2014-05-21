Module guide
============

.. module:: svg2tikz
   :synopsis: Interface to the SVG to TikZ converter
   
.. function:: convert_svg(filename_or_string[, ids=[], crop=False, wrap=True, codeoutput="standalone"])

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
    
        - ``standalone`` -- output a standalone document
        - ``figonly`` -- wrap code in a ``tikzpicture`` environment
        - ``codeonly`` 
   
   :rtype: string
   
   Examples::
   
        from svg2tikz import convert_svg
        
        code = convert_svg("example.svg", ids=['1', '2', 'id2'], verbose=True)
        code = convert_svg("example.svg", verbose=True)
        

