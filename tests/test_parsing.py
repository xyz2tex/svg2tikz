import unittest

try:
    # svg2tikz installed into system's python path?
    import svg2tikz
except ImportError:
    # if not, have a look into default directory
    import sys, os

    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + "/../")
    import svg2tikz

from svg2tikz.extensions.tikz_export import parse_transform
from svg2tikz.extensions.tikz_export import parse_color
from inkex import Path


class ParseTransformTest(unittest.TestCase):
    """Test for single transformations"""

    def test_translate(self):
        "Parse 'translate(10,10)'"
        parse_transform("translate(10,10)")

    def test_matrix(self):
        "Parse 'matrix(0.8660254,-0.5,0.5,0.8660254,-91.088088,126.14017)'"
        parse_transform("matrix(0.8660254,-0.5,0.5,0.8660254,-91.088088,126.14017)")

    def test_rotate(self):
        "Parse 'rotate(10)'"
        parse_transform("rotate(10)")

    def test_rotateabout(self):
        "Parse 'rotate(10,1,2)'"
        parse_transform("rotate(10,1,2)")

    def test_scale(self):
        "Parse 'scale(10)'"
        parse_transform("scale(10)")

    def test_scalexy(self):
        "Parse 'scale(10,5)'"
        parse_transform("scale(10,5)")

    def test_skewX(self):
        "Parse 'skewX(10)'"
        parse_transform("skewX(10)")

    def test_skewY(self):
        "Parse 'skewY(10)'"
        parse_transform("skewY(10)")


class ParseTransformWhitespaceTest(unittest.TestCase):
    """Test arguments separated by whitespace"""

    def test_translatewsp(self):
        "Parse 'translate(10 10)'"
        parse_transform("translate(10 10)")

    def test_matrixwsp(self):
        "Parse 'matrix(0.8660254 -0.5 0.5 0.8660254 -91.088088 126.14017)'"
        parse_transform("matrix(0.8660254 -0.5 0.5 0.8660254 -91.088088 126.14017)")

    def test_rotateaboutwsp(self):
        "Parse 'rotate(10 1 2)'"
        parse_transform("rotate(10 1 2)")

    def test_scalexywsp(self):
        "Parse 'scale(10 5)'"
        parse_transform("scale(10 5)")

    def test_trailingwsp(self):
        "Parse '  rotate(10)'"
        parse_transform("  rotate(10)")

    def test_transformationwsparguments(self):
        "Parse 'translate (10 10)'"
        parse_transform("translate (10 10)")

    def test_commawhitespace(self):
        "Parse 'translate(0, -150)'"
        parse_transform("translate(0, -150)")

    def test_commawhitespace2(self):
        "Parse 'matrix(0.8660254, -0.5, 0.5 0.8660254 -91.088088 , 126.14017)'"
        parse_transform("matrix(0.8660254, -0.5, 0.5 0.8660254 -91.088088 , 126.14017)")


class ParseTransformMultiple(unittest.TestCase):
    """Test multiple transformations"""

    def test_twotransform(self):
        "Parse 'translate(700,210) rotate(-30)'"
        parse_transform("translate(700,210) rotate(-30)")

    def test_threetransform(self):
        "Parse 'translate(700,210) skewX(10) rotate(-30) '"
        parse_transform("translate(700,210) skewX(10) rotate(-30) ")

    def test_twotransformwithcomma(self):
        "Parse 'scale(0.9),translate(20,30)'"
        parse_transform("scale(0.9),translate(20,30)")

    def test_threetransform2(self):
        "Parse 'translate(700,210)  , skewX(10)  rotate(-30), skewY(30) '"
        parse_transform("translate(700,210)  , skewX(10)  rotate(-30), skewY(30) ")


class ParseColorTest(unittest.TestCase):
    """Test for single transformations"""

    def test_namedcolor(self):
        "Parse 'red'"
        col = parse_color("red")
        self.assertEqual((255, 0, 0), col)

    def test_hexcolor4digit(self):
        "Parse '#ff0102'"
        col = parse_color("#ff0102")
        self.assertEqual((255, 1, 2), col)

    def test_hexcolor3digit(self):
        "Parse '#fff'"
        col = parse_color("#fff")
        self.assertEqual((255, 255, 255), col)

    def test_rgbcolorint(self):
        "Parse 'rgb(255,255,255)'"
        col = parse_color("rgb(255,255,255)")
        self.assertEqual((255, 255, 255), col)

    def test_rgbcolorpercent(self):
        "Parse 'rgb(100%,100%,100%)'"
        col = parse_color("rgb(100%,100%,100%)")
        self.assertEqual((255, 255, 255), col)

    def test_rgbcolorpercent2(self):
        "Parse 'rgb(100%,100%,100%)'"
        col = parse_color("rgb(50%,0%,1%)")
        self.assertEqual((127, 0, 2), col)

    def test_rgbcolorpercentdecimal(self):
        "Parse 'rgb(66.667%,0%,6.667%)'"
        col = parse_color("rgb(66.667%,0%,6.667%)")
        self.assertEqual((170, 0, 17), col)

    def test_currentColor(self):
        "Parse 'currentColor'"
        parse_color("currentColor")


class TestErrorHandling(unittest.TestCase):
    def test_no_transform(self):
        res = parse_transform("")
        self.assertEqual(res, [])

    def test_invalid_transform(self):
        self.assertRaises(SyntaxError, parse_transform, "curl(100,100)")

# We should not test inkex functions
# class TestPathParsing(unittest.TestCase):
    # def test_invalid_path(self):
        # path = "M 20 100 H 40#90"

        # def invalid_path():
            # return Path(path).to_arrays()
        # print(Path(path).to_arrays())
        # self.assertRaises(ValueError, invalid_path)


if __name__ == "__main__":
    unittest.main()
