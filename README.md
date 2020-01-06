# SVG2TikZ

SVG2TikZ, formally known as Inkscape2TikZ ,are a set of tools for converting SVG graphics to TikZ/PGF code. 
This project is licensed under the GNU GPL  (see  the [LICENSE](/LICENSE) file).

## Changes, Bug fixes and Known Problems from the original

- Now images can also be exported to tikz
- Added a variable `/def /globalscale` to the output tikz document (standalone and tikz figure)
- `/globalscale` when changed will scale the tikzfigure by transforming the vector coordinates.
- `/globalscale` when changed will scale the tikzfigure by scaling the embedded images
- The path element was not exported in correct coordinates. This is fixed
- Paths can now have start and end markers. Refer to [this](https://gist.github.com/AndiH/f99d9b0cbd3519c27af5b96cfbeff97c#file-tikz-arrows-tex) to know supported markers
- Added an entry to specify the path to be removed from absolute paths in the images. This is useful to work in a latex project directly

## Supported markers from `arrows.meta` package of latex

```
MARKER_NAME_TRANSLATIONS = {'url(#CurveIn)':'Arc Barb', 'url(#CurveOut)':'Arc Barb', 'url(#StopL)':'Bar', 
                            'url(#StopM)':'Bracket', 'url(#CurvyCross)':'Hooks', 'url(#SemiCircleIn)':'Parenthesis', 
                            'url(#EmptyTriangleInS)':'Straight Barb', 'url(#StopS)': 'Tee Barb', 
                            'url(#EmptyTriangleInM)':'Classical TikZ Rightarrow', 'url(#EmptyTriangleOutM)':'Classical TikZ Rightarrow',
                            'url(#EmptyTriangleInL)':'Computer Modern Rightarrow', 'url(#EmptyTriangleOutL)':'Computer Modern Rightarrow', 
                            'url(#Arrow1Lstart)': 'To', 'url(#Arrow1Lend)': 'To', 'url(#DotL)': 'Circle', 
                            'url(#DiamondL)': 'Diamond', 'url(#DotS)': 'Ellipse', 
                            'url(#Arrow2Lstart)': 'Kite', 'url(#Arrow2Lend)': 'Kite', 'url(#Arrow2Mstart)': 'Latex', 
                            'url(#Arrow2Mend)': 'Latex', 'url(#Arrow2Sstart)': 'Latex[round]', 'url(#Arrow2Send)': 'Latex''Latex[round]', 
                            'url(#SquareS)':'Rectangle', 'url(#SquareL)':'Square', 'url(#TriangleInL)':'Stealth', 'url(#TriangleOutL)':'Stealth',
                            'url(#TriangleInS)': 'Triangle', 'url(#TriangleOutS)': 'Triangle', 'url(#DiamondM)': 'Turned Square', 
                            'url(#DotM)': 'Circle[open]', 'url(#SquareM)': 'Square[open]', 'url(#EmptyTriangleInL)': 'Triangle[open]', 'url(#EmptyTriangleOutL)': 'Triangle[open]', 
                            'url(#EmptyDiamondM)': 'Turned Square[open]', 'url(#Tail)': 'Rays'};
```

In the above key:value pairs, the left side key is the name referred to in Inkscape and the right side value is the one referred to the markers in `arrows.meta` from latex

## Known Problems
- Currently only images that are "linked" in svg are exported. Base64 embed is not yet supported so avoid choosing embed option
- Grouped elements will not work. So ungroup everything
- Transformation like rotation is not working

More documentation can be found in the [docs/](/docs/index.rst) directory. Also head over to [wiki](https://github.com/aalavandhaann/svg2tikz/wiki/Installation-and-Usage) for some useful information when exporting your svg that contains images. 
