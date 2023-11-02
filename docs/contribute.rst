
How to contribute
*****************

First of all thanks for your interest in contributing in this project.

Tools
=====
We used black_ and pylint_ to format and lint the code. Github actions are run on the merge request to check that the code is valid.

.. _black: https://github.com/psf/black
.. _pylint: https://github.com/pylint-dev/pylint

You can directly install the dev depedencies with `poetry install --with dev`

Tests
=====
The tests of SVG2TikZ are writting using the unittest package. You can run all the test with command `python -m unittest`.


.. _unittest: https://docs.python.org/3/library/unittest.html
