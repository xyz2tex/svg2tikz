#!/usr/bin/env python
"""\
Export Inkscape paths as TikZ paths

Author: Kjell Magne Fauske
"""

# Copyright (C) 2008 Kjell Magne Fauske, http://www.fauskes.net
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

__version__ = '0.1'
__author__ = 'Kjell Magne Fauske'


# Todo:
# Basic functionality:
#
# Stroke properties
#   - dash patterns
#   - miterlimit
# Fill properties
#   - linear shading
#   - radial shading
# Paths:
#   - arcs
# Text
# 
# Other stuff:
# - Better output code formatting!
# - Add a + prefix to coordinates to speed up pgf parsing
# - Transformations
# - support the <use> element

from itertools import izip
from textwrap import wrap

import itertools
import inkex, simplepath, simplestyle
import pprint, os,re,math

def copy_to_clipboard(text):
    """Copy text to the clipboard

    Returns True if successful. False otherwise.

    Works on Windows, *nix and Mac. Tries the following:
    1. Use the win32clipboard module from the win32 package.
    2. Calls the xclip command line tool (*nix)
    3. Calls the pbcopy command line tool (Mac)
    4. Try pygtk
    """
    # try windows first
    try:
        import win32clipboard
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(text)
        win32clipboard.CloseClipboard()
        return True
    except:
        pass
    # try xclip
    try:
        import subprocess
        p = subprocess.Popen(['xclip', '-selection', 'c'], stdin=subprocess.PIPE)
        p.stdin.write(text)
        p.stdin.close()
        retcode = p.wait()
        return True
    except:
        pass
    # try pbcopy (Os X)
    try:
        import subprocess
        p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        p.stdin.write(text)
        p.stdin.close()
        retcode = p.wait()
        return True
    except:
        pass
    # try pygtk
    try:
        # Code from
        # http://www.vector-seven.com/2007/06/27/
        #    passing-data-between-gtk-applications-with-gtkclipboard/
        import pygtk
        pygtk.require('2.0')
        import gtk
        # get the clipboard
        clipboard = gtk.clipboard_get()
        # set the clipboard text data
        clipboard.set_text(text)
        # make our data available to other applications
        clipboard.store()
    except:
        return False

def nsplit(seq, n=2):
    """Split a sequence into pieces of length n

    If the length of the sequence isn't a multiple of n, the rest is discarded.
    Note that nsplit will strings into individual characters.

    Examples:
    >>> nsplit('aabbcc')
    [('a', 'a'), ('b', 'b'), ('c', 'c')]
    >>> nsplit('aabbcc',n=3)
    [('a', 'a', 'b'), ('b', 'c', 'c')]

    # Note that cc is discarded
    >>> nsplit('aabbcc',n=4)
    [('a', 'a', 'b', 'b')]
    """
    return [xy for xy in izip(*[iter(seq)]*n)]

crop_template = r"""
\usepackage[active,tightpage]{preview}
\PreviewEnvironment{tikzpicture}
"""


# Templates
standalone_template=r"""
\documentclass{article}
\usepackage{tikz}
%(cropcode)s
\begin{document}
%(colorcode)s
\begin{tikzpicture}[y=0.80pt,x=0.80pt,yscale=-1]
%(pathcode)s
\end{tikzpicture}
\end{document}
"""

fig_template = r"""
%(colorcode)s
\begin{tikzpicture}[y=0.80pt, x=0.8pt,yscale=-1]
%(pathcode)s
\end{tikzpicture}
"""


SCALE = 'scale'
DICT = 'dict'
DIMENSION = 'dimension'
FACTOR = 'factor' # >= 1

# Map Inkscape/SVG stroke and fill properties to corresponding TikZ options.
# Format:
#   'svg_name' : ('tikz_name', value_type, data)


properties_map = {
    'opacity' : ('opacity',SCALE,''),
    # filling    
    'fill-opacity' : ('fill opacity', SCALE,''),
    'fill-rule' : ('',DICT,
                   dict(nonzero='nonzero rule',evenodd='even odd rule')),
    # stroke    
    'stroke-opacity' : ('draw opacity', SCALE,''),
    'stroke-linecap' : ('line cap',DICT,
                        dict(butt='butt',round='round',square='rect')),
    'stroke-linejoin' : ('line join',DICT,
                         dict(miter='miter',round='round',bevel='bevel')),
    'stroke-width' : ('line width',DIMENSION,''),
    'stroke-miterlimit' : ('miter limit', FACTOR,'')
        
}

def chunks(s, cl):
    """Split a string or sequence into pieces of length cl and return an iterator
    """
    for i in xrange(0, len(s), cl):
        yield s[i:i+cl]


def parse_transform(transf):
    """Parse a transformation attribute and return a list of transformations"""
    # Based on the code in parseTransform in the simpletransform.py module
    # Copyright (C) 2006 Jean-Francois Barraud
    if transf=="" or transf==None:
        return(mat)
    stransf = transf.strip()
    result=re.match("(translate|scale|rotate|skewX|skewY|matrix)\s*\(([^)]*)\)",stransf)
    transforms = []
    #-- translate --
    if result.group(1)=="translate":
        args=result.group(2).replace(' ',',').split(",")
        dx=float(args[0])
        if len(args)==1:
            dy=0.0
        else:
            dy=float(args[1])
        matrix=[[1,0,dx],[0,1,dy]]
        transforms.append(['translate',(dx,dy)])
    #-- scale --
    if result.group(1)=="scale":
        args=result.group(2).replace(' ',',').split(",")
        sx=float(args[0])
        if len(args)==1:
            sy=sx
        else:
            sy=float(args[1])
        transforms.append(['scale',(sx,sy)])
    #-- rotate --
    if result.group(1)=="rotate":
        args=result.group(2).replace(' ',',').split(",")
        a=float(args[0])#*math.pi/180
        if len(args)==1:
            cx,cy=(0.0,0.0)
        else:
            cx,cy=map(float,args[1:])
        transforms.append(['rotate',(a,cx,cy)])
    #-- skewX --
    if result.group(1)=="skewX":
        a=float(result.group(2))#"*math.pi/180
        matrix=[[1,math.tan(a),0],[0,1,0]]
        transforms.append(['skewX',tuple(a)])
    #-- skewY --
    if result.group(1)=="skewY":
        a=float(result.group(2))#*math.pi/180
        matrix=[[1,0,0],[math.tan(a),1,0]]
        transforms.append(['skewY',tuple(a)])
    #-- matrix --
    if result.group(1)=="matrix":
        #a11,a21,a12,a22,v1,v2=result.group(2).replace(' ',',').split(",")
        #matrix=[[float(a11),float(a12),float(v1)],[float(a21),float(a22),float(v2)]]
        transforms.append(['matrix',tuple(map(float,result.group(2).replace(' ',',').split(",")))])


    if result.end()<len(stransf):
        return transforms + parse_transform(stransf[result.end():])
    else:
        return transforms

class TikZPathExporter(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        parser = self.OptionParser
        parser.add_option('--codeoutput', dest='codeoutput', default = 'standalone',
                  choices = ('standalone','codeonly', 'figonly'),
                  help = "Set text mode (verbatim, math, raw).")

        parser.add_option('--crop',action="store", type="inkbool",
                        dest="crop", default=False,
                        help="Use the preview package to crop the tikzpicture")
        parser.add_option('--clipboard',action="store", type="inkbool",
                        dest="clipboard", default=True,
                        help="Export to clipboard")
        parser.add_option('--wrap',action="store", type="inkbool",
                        dest="wrap", default=True,
                        help="Wrap long lines")
        self.x_o = self.y_o = 0.0
        # px -> cm scale factors
        self.x_scale = 0.02822219;
        # SVG has its origin in the upper left corner, while TikZ' origin is
        # in the lower left corner. We therefore have to reverse the y-axis.
        self.y_scale = -0.02822219;
        self.colors = {}
        self.colorcode = ""

    def getselected(self):
        """Get selected nodes in document order

        The nodes are stored in the selected dictionary and as a list of
        nodes in selected_sorted.
        """
        self.selected_sorted = []
        self.selected = {}
        if len(self.options.ids) == 0:
            return
        # Iterate over every element in the document
        for node in self.document.getiterator():
            id = node.get('id','')
            if id in self.options.ids:
                self.selected[id] = node
                self.selected_sorted.append(node)


    def transform(self,coord_list,cmd=None):
        """Apply transformations to input coordinates"""
        coord_transformed = []
        try:
            if not len(coord_list) % 2:
                for x, y in nsplit(coord_list,2):
                    #coord_transformed.append("%.4fcm" % ((x-self.x_o)*self.x_scale))
                    #oord_transformed.append("%.4fcm" % ((y-self.y_o)*self.y_scale))
                    coord_transformed.append("%.4f" % x)
                    coord_transformed.append("%.4f" % y)
            elif len(coord_list)==1:
                coord_transformed = ["%.4fcm" % (coord_list[0]*self.x_scale)]
            else:
                coord_transformed = coord_list
        except:
            coord_transformed = coord_list
        return tuple(coord_transformed)

    def get_color(self, color):
        """Return a valid xcolor color name and store color"""

        if color in self.colors:
            return self.colors[color]
        else:

            r,g,b = simplestyle.parseColor(color)
            if not (r or g or b):
                return "black"
            xcolorname = color.replace('#','c')
            self.colors[color] = xcolorname
            self.colorcode += "\\definecolor{%s}{RGB}{%s,%s,%s}\n" \
                              % (xcolorname,r,g,b)
            return xcolorname

    def get_styles(self, node,closed_path=False):
        """Return a node's SVG styles as a list of TikZ options"""
        style = simplestyle.parseStyle(node.get('style',''))
        options = []
        # get stroke and fill options
        display = style.get('display') or node.get('display')
        stroke = style.get('stroke','') or node.get('stroke')
        if display <>  'none':
            # FIXME: If a path or shape is part of a group they inherit the
            # group's stroke and fill properties. This is currently not handled
            # properly.
            if stroke <> 'none':
                if stroke:
                    options.append('draw=%s' % self.get_color(stroke))
                else:
                    options.append('draw')
            fill = style.get('fill','') or node.get('fill')
            if fill <> 'none':
                if fill:
                    options.append('fill=%s' % self.get_color(fill))
                elif closed_path:
                    options.append('fill')

        for svgname, tikzdata in properties_map.iteritems():
            tikzname, valuetype,data = tikzdata
            value = style.get(svgname) or node.get(svgname)
            if not value: continue
            if valuetype == SCALE:
                val = float(value)
                if not val == 1:
                    options.append('%s=%.3f' % (tikzname,float(value)))
            elif valuetype == DICT:
                if tikzname:
                    options.append('%s=%s' % (tikzname,data.get(value,'')))
                else:
                    options.append('%s' % data.get(value,''))
            elif valuetype == DIMENSION:
                # FIXME: Handle different dimensions in a general way
                options.append('%s=%.3fpt' % (tikzname,inkex.unittouu(value)*0.80)),
            elif valuetype == FACTOR:
                val = float(value)
                if val >= 1.0:
                    options.append('%s=%.2f' % (tikzname,val))
                    

        
        return options

    def get_transform(self, transform):
        """Convert a SVG transform attribute to a list of TikZ transformations"""
        #return ""
        if not transform:
            return ""

        transforms = parse_transform(transform)
        options = []
        for cmd, params in transforms:
            if cmd == 'translate':
                x, y = params
                if x and y:
                    options.append("shift={(%s,%s)}" % params)
                elif x:
                    options.append("xshift=%s" % x)
                else:
                    options.append("yshift=%s" % y)

            elif cmd == 'rotate':
                if params[1] or params[2]:
                    options.append("rotate around={%s,(%s,%s)}" % params)
                else:
                    options.append("rotate=%s" % params[0])
            elif cmd == 'matrix':
                options.append("cm={{%s,%s,%s,%s,(%s,%s)}}" % params)
            elif cmd == 'skewX':
                options.append("xslant=%.3f" % math.tan(params[0]*math.pi/180))
            elif cmd == 'skewY':
                options.append("yslant=%.3f" % math.tan(params[0]*math.pi/180))

        return options


    def get_shape_data(self, node):
        """Extract shape data from node"""
        options = []
        if node.tag == inkex.addNS('rect','svg'):
            inset = node.get('rx',0) or node.get('ry',0)
            x = float(node.get('x',0))
            y = float(node.get('y',0))
            # map from svg to tikz
            width = float(node.get('width',0))+x
            height = float(node.get('height',0))+y
            if inset:
                options = ["rounded corners=%s" % self.transform([float(inset)])]
            return ('rect',(x,y,width,height)),options
        elif node.tag in [inkex.addNS('polyline','svg'),
                          inkex.addNS('polygon','svg'),
                          ]:
            points = node.get('points','').replace(',',' ')
            points = map(float,points.split())

            if node.tag == inkex.addNS('polyline','svg'):
                cmd = 'polyline'
            else:
                cmd = 'polygon'
            return (cmd,points),options
        elif node.tag in inkex.addNS('line','svg'):
            points = [node.get('x1'),node.get('y1'),
                      node.get('x2'),node.get('y2')]
            points = map(float,points)
            return ('polyline',points),options

        if node.tag == inkex.addNS('circle','svg'):
            # ugly code...
            center = map(float,[node.get('cx',0),node.get('cy',0)])
            r = float(node.get('r',0))
            return ('circle',self.transform(center)+self.transform([r])),options

        elif node.tag == inkex.addNS('ellipse','svg'):
            center = map(float,[node.get('cx',0),node.get('cy',0)])
            rx = float(node.get('rx',0))
            ry = float(node.get('ry',0))
            return ('ellipse',self.transform(center)+self.transform([rx])
                             +self.transform([ry])),options
        else:
            return (None,None),options


    def output_tikz_path(self,path=None,node=None,shape=None,text=None):
        """Covert SVG paths, shapes and text to TikZ paths"""
        s = pathcode = ""

        options = []
        transform = node.get('transform','')
        if transform:
            options += self.get_transform(transform)
        if shape:
            shapedata,opts = self.get_shape_data(node)
            if opts:
                options += opts
            p = [shapedata]
        elif text:
            textstr = self.get_text(node)
            x = node.get('x','0')
            y = node.get('y','0')
            p = [('M',[x,y]),('T',textstr)]
            
        else:
            # check that it really is a path
            if not node.tag == inkex.addNS('path','svg'):
                return ""
            if not path:
                p = simplepath.parsePath(node.get('d'))
            else:
                p = path
        id = node.get('id')
        closed_path = False
        for cmd,params in p:
            # transform coordinates
            tparams = self.transform(params,cmd)
            # SVG paths
            if cmd == 'M':
                s += "(%s,%s)" % tparams
            elif cmd == 'L':
                s += " -- (%s,%s)" % tparams
            elif cmd == 'C':
                s += " .. controls (%s,%s) and (%s,%s) .. (%s,%s)" % tparams
            elif cmd == 'Z':
                s += " -- cycle"
                closed_path = True
            elif cmd == 'A':
                # not implemented yet
                pass
            elif cmd == 'T':
                s += " node[above right] (%s) {%s}" %(id,params)
            # Shapes
            elif cmd == 'rect':
                s += "(%s,%s) rectangle (%s,%s)" % tparams
            elif cmd in ['polyline','polygon']:
                points = ["(%s,%s)" % (x,y) for x,y in chunks(tparams,2)]
                if cmd == 'polygon':
                    points.append('cycle')
                    closed_path = True
                s += " -- ".join(points)
            # circle and ellipse does not use the transformed parameters
            elif cmd == 'circle':
                s += "(%s,%s) circle (%s)" % params
            elif cmd == 'ellipse':
                s += "(%s,%s) ellipse (%s and %s)" % params

        options += self.get_styles(node,closed_path)

        if options:
            optionscode = "[%s]" % ','.join(options)
        else:
            optionscode = ""
            
        pathcode = "\\path%s %s;" % (optionscode,s)
        if self.options.wrap:
            pathcode = "\n".join(wrap(pathcode,80,subsequent_indent="  ",break_long_words=False))
    
        pathcode = "%%%s\n%s\n" % (id,pathcode)
        
        return pathcode
    
    def get_text(self,node):
        """Return content of a text node as string"""
        text = ""
        if node.text != None:
            text += node.text
    
        for child in node:
            text += self.get_text(child)
            
        if node.tail:
            text += node.tail
            
    
        return text

    def output_group(self,group):
        s = ""
        for node in group:
            if node.tag == inkex.addNS('path','svg'):
                p = simplepath.parsePath(node.get('d'))

                cc, params = p[0]
                # Set the origin to the first coordinate in the first path.
                # Should probably be an option.
                if not (self.x_o <> 0 or self.y_o <> 0):
                    self.x_o, self.y_o = params
                s += self.output_tikz_path(p,node,shape=False)
            elif node.tag in [inkex.addNS('rect','svg'),
                              inkex.addNS('polyline','svg'),
                              inkex.addNS('polygon','svg'),
                              inkex.addNS('line','svg'),
                              inkex.addNS('circle','svg'),
                              inkex.addNS('ellipse','svg')]:
                x = float(node.get('x',0))
                y = float(node.get('y',0))
                # Set the origin to the first coordinate in the first path.
                # Should probably be an option.
                if not (self.x_o <> 0 or self.y_o <> 0):
                    self.x_o, self.y_o = x,y
                s += self.output_tikz_path(None,node,shape=True)

            # group node
            elif node.tag == inkex.addNS('g','svg'):
                transform = node.get('transform','')
                cm = []
                if transform:
                    cm = self.get_transform(transform)
                code = self.output_group(node)
                styles = self.get_styles(node)
                if cm or styles:
                    s += "\\begin{scope}[%s]\n%s\n\\end{scope}\n" % \
                        (",".join(cm+styles),code)
                else:
                    s += code
            elif node.tag == inkex.addNS('text','svg'):
                s += self.output_tikz_path(None,node,text=True)
                

        return s


    def effect(self):
        s = ""
        nodes = self.selected_sorted
        if len(nodes) == 0:
            nodes = self.document.getroot()
        s = self.output_group(nodes)

        codeoutput = self.options.codeoutput
        if not self.options.crop:
            cropcode = ""
        else:
            cropcode = crop_template
        if codeoutput == 'standalone':
            output = standalone_template % dict(pathcode=s,\
                                                colorcode=self.colorcode,\
                                                cropcode=cropcode)
        elif codeoutput == 'figonly':
            output = fig_template % dict(pathcode=s,colorcode=self.colorcode)
        else:
            output = s
        if self.options.clipboard:
            copy_to_clipboard(output)

if __name__ == '__main__':
    # Create effect instance and apply it.
    effect = TikZPathExporter()
    effect.affect()
