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
