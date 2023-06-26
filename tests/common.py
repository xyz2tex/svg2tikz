"""Common SVG between tests"""

SVG_2_PATH = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="4in" height="2in"
     viewBox="0 0 4000 2000" version="1.1"
     xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="Triangle"
      viewBox="0 0 10 10" refX="0" refY="5"
      markerUnits="strokeWidth"
      markerWidth="4" markerHeight="3"
      orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" />
    </marker>
  </defs>
  <path id="pathA" d="M 1000 750 L 2000 750 L 2500 1250"
        fill="none" stroke="black" stroke-width="100" color="red" opacity="0.8"
        transform="translate(-9.08294, -40.2406)"
        marker-end="url(#Triangle)"  />

 <path id="pathB" d="M 1000 750 L 2000 750 L 2500 1250"
        fill="none" stroke="blue" stroke-width="50"
        marker-end="url(#Triangle)" marker-start="url(#Triangle)" />
</svg>"""


SVG_2_RECT = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="12cm" height="4cm" viewBox="0 0 1200 400"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <desc>Example rect01 - rectangle with sharp corners</desc>
  <!-- Show outline of canvas using 'rect' element -->
  <rect x="1" y="1" width="1198" height="398" id="rect1"
        fill="none" stroke="blue" stroke-width="2"/>
  <rect x="400" y="100" width="400" height="200" id="rect2"
        fill="yellow" stroke="navy" stroke-width="10"  />
</svg>
"""

SVG_3_RECT = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="12cm" height="4cm" viewBox="0 0 1200 400"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <desc>Example rect01 - rectangle with sharp corners</desc>
  <!-- Show outline of canvas using 'rect' element -->
  <rect x="1" y="1" width="1198" height="398" id="rect1"
        fill="none" stroke="blue" stroke-width="2"/>
  <rect x="400" y="100" width="400" height="200" id="rect2"
        fill="yellow" stroke="navy" stroke-width="10"  />
  <rect x="400" y="100" width="400" height="200" id="rect3"
        fill="none" stroke="green" stroke-width="10"  />
</svg>
"""

SVG_4_RECT = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="12cm" height="4cm" viewBox="0 0 1200 400"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <desc>Example rect01 - rectangle with sharp corners</desc>
  <!-- Show outline of canvas using 'rect' element -->
  <rect x="1" y="1" width="1198" height="398" id="rect1"
        fill="none" stroke="blue" stroke-width="2"/>
  <rect x="400" y="100" width="400" height="200" id="rect2"
        fill="yellow" stroke="navy" stroke-width="10"  />
  <rect x="400" y="100" width="400" height="200" id="rect3"
        fill="none" stroke="green" stroke-width="10"  />
  <rect x="400" y="100" width="400" height="200" id="rect4"
        fill="none" stroke="green" stroke-width="10"  />
</svg>
"""

SVG_EMPTY = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="12cm" height="4cm" viewBox="0 0 1200 400"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
</svg>
"""


SVG_TEXT = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="12cm" height="4cm" viewBox="0 0 1200 400"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <desc>Example rect01 - rectangle with sharp corners</desc>
      <text
       xml:space="preserve"
       transform="scale(0.26458333)"
       id="textNode"
       style="font-size:40px;line-height:1.25;font-family:Montserrat;-inkscape-font-specification:Montserrat;white-space:pre;shape-inside:url(#rect3686)"><tspan
         x="16.890625"
         y="57.177803"
         id="tspan7035">Test Text</tspan></text>
</svg>
"""

SVG_TEXT_BLUE = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="10cm" height="3cm" viewBox="0 0 1000 300"
     xmlns="http://www.w3.org/2000/svg" version="1.1">
  <desc>Example text01 - 'Hello, out there' in blue</desc>

  <text x="250" y="150">a%b</text>
</svg>"""

SVG_ARROW = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="4in" height="2in"
     viewBox="0 0 4000 2000" version="1.1"
     xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="Triangle"
      viewBox="0 0 10 10" refX="0" refY="5"
      markerUnits="strokeWidth"
      markerWidth="4" markerHeight="3"
      orient="auto">
      <path d="M 0 0 L 10 5 L 0 10 z" />
    </marker>
  </defs>
  <path d="M 1000 750 L 2000 750 L 2500 1250"
        fill="none" stroke="black" stroke-width="100"
        marker-end="url(#Triangle)"  />
</svg>"""

SVG_PAINT = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="12cm" height="4cm" viewBox="0 0 1200 400"
     xmlns="http://www.w3.org/2000/svg" version="1.1"
     fill="red">
  <desc>Example rect01 - rectangle with sharp corners</desc>
  <!-- Show outline of canvas using 'rect' element -->
  <rect x="1" y="1" width="1198" height="398"
     stroke="blue" stroke-width="2"/>
</svg>
"""

SVG_DEFS = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg width="10cm" height="3cm" viewBox="0 0 100 30" version="1.1"
     xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
  <desc>Example Use01 - Simple case of 'use' on a 'rect'</desc>
  <defs>
    <rect width="60" height="10"/>
    <circle id = "s1" cx = "200" cy = "200" r = "200" fill = "yellow" stroke = "black" stroke-width = "3"/>
    <ellipse id = "s2" cx = "200" cy = "150" rx = "200" ry = "150" fill = "salmon" stroke = "black" stroke-width = "3"/>
  </defs>
  <rect x=".1" y=".1" width="99.8cm" height="29.8"
        fill="none" stroke="blue" stroke-width=".2" />
</svg>"""

SVG_NO_HEIGHT = r"""<?xml version="1.0" standalone="no"?>
<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"
  "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">
<svg xmlns="http://www.w3.org/2000/svg" version="1.1">
  <rect x=".01cm" y=".01cm" width="4.98cm" height="4.98cm"
        fill="none" stroke="blue" stroke-width=".02cm"/>
</svg>"""
