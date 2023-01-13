#!/usr/bin/env python
"""
Test conversion of the W3C SVG Test Suite.
"""

import os
import sys
import glob
import logging
import codecs

from os.path import splitext, exists, join, basename, normpath, abspath
import unittest
import string

### Initialize logging

log = logging.getLogger("svg2tikz")
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
# set a format which is simpler for console use
formatter = logging.Formatter('%(levelname)-8s %(message)s')
# tell the handler to use this format
console.setFormatter(formatter)
log.addHandler(console)

LOG_FILENAME = splitext(__file__)[0] + '.log'
hdlr = logging.FileHandler(LOG_FILENAME)
formatter = logging.Formatter('%(levelname)-8s %(message)s')
hdlr.setFormatter(formatter)
log.setLevel(logging.DEBUG)
log.addHandler(hdlr)

try:
    # svg2tikz installed into system's python path?
    import svg2tikz
except ImportError:
    # if not, have a look into default directory
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)) + '/../')
    import svg2tikz

import svg2tikz.extensions.tikz_export as tkzex

BASE_DIR = join(abspath(os.path.dirname(__file__)), "")
EXAMPLES_DIR = normpath(abspath(join(BASE_DIR, "../examples/")))

SVG12TINY_BASEDIR = "../testfiles/svg12tiny"
SVG11FULL_BASEDIR = "testfiles/svg11full"

TEX_DEST_DIR = join(BASE_DIR, 'testdest')

### Templates

comparedoc_template = r"""
\documentclass{article}
\usepackage{tikz}

\usepackage{verbatim}
\usepackage[active,tightpage]{preview}
\setlength\PreviewBorder{0pt}%
\PreviewEnvironment{tikzpicture}

\begin{document}
$figcode
\end{document}
"""

comparedoc_fig_template = r"""
\begin{tikzpicture}
    \matrix (mtrx) {
      \node[label=below:png] {\includegraphics[width=10cm]{$pngfile}};\\
      \node[label=below:tikz] {\includegraphics[width=10cm]{$pdffile}};\\
    };
    \node[above] at (mtrx.north) {$testfile};
\end{tikzpicture}
"""

doc_template = string.Template(comparedoc_template)
fig_template = string.Template(comparedoc_fig_template)


### Utility functions

def runcmd(syscmd):
    sres = os.popen(syscmd)
    resdata = sres.read()
    err = sres.close()
    if err:
        log.warning('Failed to run command:\n%s', syscmd)
        log.debug('Output:\n%s', resdata)
    return err


def create_pdf(texfile, use_pdftex=True):
    if not splitext(texfile)[1]:
        fn = basename(texfile) + '.tex'
    else:
        fn = basename(texfile)
    if sys.platform == 'win32':
        syscmd = 'texify --pdf --clean --max-iterations=1 %s' % (fn)
    else:
        syscmd = 'pdflatex -halt-on-error -interaction nonstopmode %s' % (fn)
    err = runcmd(syscmd)
    return err


# set up a list of tests to skip
skip_list = [
    'animate-*',
    'interact-*',
    'media-anim*',
    'media-audio*',
    'script-*',
    'udom-*',
    '*dom*',
    'filter*',
    'font*',  #tmp
    'text*',  #tmp
]


def build_skip_list(skip_list, path=''):
    combined_skip_list = []
    for file_pattern in skip_list:
        filenames = glob.glob(os.path.join(path, file_pattern))
        combined_skip_list += filenames
    return set(combined_skip_list)


def get_file_list(path, pattern, skip_list=[]):
    # is pattern a list?
    if isinstance(pattern, list):
        full_filelist = []
        for p in pattern:
            full_filelist.extend(glob.glob(os.path.join(path, p)))
    else:
        full_filelist = glob.glob(os.path.join(path, pattern))
    filelist = []
    files_to_skip = build_skip_list(skip_list, path)
    for filename_full in full_filelist:
        filename = os.path.basename(filename_full)
        # is the file in the skip list?
        if not filename_full in files_to_skip:
            filelist.append(os.path.normpath(filename_full))
    return filelist


class SVGListTestCase(unittest.TestCase):
    """Base class for testing a list of SVG files"""
    svglist = []
    svgdir = os.path.join(SVG11FULL_BASEDIR, 'svg')
    skip_list = skip_list
    pattern = '*.xxxxx'
    texdir = TEX_DEST_DIR
    pngdir = os.path.join(SVG11FULL_BASEDIR, 'png')

    def __init__(self, *kwargs):
        unittest.TestCase.__init__(self, *kwargs)
        self.svglist = get_file_list(self.svgdir, self.pattern, self.skip_list)
        self.converted_files = []
        self.failed_files = []
        self.compiled_files = []

    def test_convert(self):
        for svgfile in self.svglist:
            try:
                tikz_code = tkzex.convert_file(svgfile, crop=True, ignore_text=True, verbose=True)
            except:
                print("Failed to convert %s" % basename(svgfile))
                log.exception("Failed to convert %s", basename(svgfile))
                self.failed_files.append(svgfile)
                continue
            log.info('Converted %s', svgfile)
            tex_fn = join(self.texdir, \
                          basename(splitext(svgfile)[0]) + '.tex')
            #
            f = codecs.open(normpath(tex_fn), 'w', encoding='latin-1')
            f.write(tikz_code)
            f.close()
            self.converted_files.append(tex_fn)
            #self.failUnless(len(self.failed_files) == 0, 'Failed to parse %s' % self.failed_files)

        #    def test_makepdf(self):
        cwd = os.getcwd()
        if not os.path.exists(TEX_DEST_DIR):
            os.mkdir(TEX_DEST_DIR)
        os.chdir(TEX_DEST_DIR)
        failed_files = []
        for fn in self.converted_files:
            err = create_pdf(basename(fn))
            if err:
                failed_files.append('fn')
            else:
                self.compiled_files.append(fn)
                log.info('Compiled %s', fn)
        os.chdir(cwd)
        #self.failUnless(len(failed_files) == 0, 'Failed to compile %s' % failed_files)

        #    def test_makesummary(self):
        # create a summary report
        s = ""
        if len(self.compiled_files) == 0:
            return
        for fn in self.compiled_files:
            # get PNG filename
            # LaTeX does not like backward slashes.
            png_fn = os.path.realpath(normpath(join(self.pngdir, \
                                                    '' + basename(splitext(fn)[0]) + '.png'))).replace('\\', '/')
            pdffile = normpath(splitext(fn)[0]).replace('\\', '/')
            testfile = basename(splitext(fn)[0]) + '.svg'
            s += fig_template.substitute(pngfile=png_fn, pdffile=pdffile, testfile=testfile)

        cwd = os.getcwd()
        os.chdir(TEX_DEST_DIR)
        report_fn = 'report%s.tex' % self.__class__.__name__
        f = open(report_fn, 'w')
        f.write(doc_template.substitute(figcode=s))
        #print self.__str__()
        f.close()
        err = create_pdf(basename(report_fn))
        os.chdir(cwd)


class PathTestCase(SVGListTestCase):
    pattern = 'paths*.svg'
    #pattern=['paths-data-18-f.svg']


#   # pattern='*.svg'
#
class ShapesCase(SVGListTestCase):
    pattern = 'shapes*.svg'


#class PaintingStrokeCase(SVGListTestCase):
#    pattern='painting-stroke*.svg'

class ShadingCase(SVGListTestCase):
    #    #pattern='pservers-grad*.svg'
    pattern = [
        'pservers-grad-01-b.svg',
        'pservers-grad-02-b.svg',
        'pservers-grad-04-b.svg',
    ]


#class FailCase(SVGListTestCase):
#    pattern=[
#        'shapes-intro-01-t.svg',
#        'shapes-ellipse-02-t.svg',
#        'shapes-circle-02-t.svg',
#        'coords-units-03-b.svg',
#        'masking-mask-01-b.svg',
#        'masking-opacity-01-b.svg',
#        'painting-marker-02-f.svg',
#        'render-elems-03-t.svg',
#        'render-groups-01-b.svg',
#        'struct-group-02-b.svg',
#        'styling-pres-01-t.svg',
#        'styling-inherit-01-b.svg',
#    ]
#
#
class ClippingTestCase(SVGListTestCase):
    pattern = [
        'shapes-ellipse-02-t.svg',
        'shapes-circle-02-t.svg',
    ]


#class PaintingFillCase(SVGListTestCase):
#    pattern='painting-fill*.svg'
#pattern='painting-*.svg'

#    #pattern='painting-fill-04-t.svg'


class TestAllCase(SVGListTestCase):
    pattern = '*.svg'

#class UseCase(SVGListTestCase):
#    pattern=['struct-use-01-t.svg', 'struct-use-03-t.svg']


if __name__ == "__main__":
    unittest.main()

    # Fails:
    # shapes-intro-01-t
    # shapes-ellipse-02-t.svg
    # paths-data-03-f.svg
    # shapes-circle-02-t.svg
    # shapes-rect-01-t.svg


    #coords-units-03-b.svg
    #masking-mask-01-b.svg
    #masking-opacity-01-b.svg
    #painting-marker-02-f.svg
    #render-elems-03-t.svg
    #render-groups-01-b.svg
    #struct-group-02-b.svg
    #styling-pres-01-t.svg
    #styling-inherit-01-b.svg
