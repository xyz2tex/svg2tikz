
.. _module-guide:

package guide
=============

.. module:: svg2tikz
   :synopsis: Interface to the SVG to TikZ converter

.. autofunction:: svg2tikz.convert_file


.. autofunction:: svg2tikz.convert_svg



   Examples::

        from svg2tikz import convert_svg

        var_svg = """<svg>
        ...
        </svg>"""
        code = convert_svg(var_svg, ids=['1', '2', 'id2'], verbose=True)
