from distutils.core import setup
#from setuptools import setup

setup(name='svg2tikz',
      version='0.1.0dev',
      description = 'An SVG to TikZ converter',
      author = 'Kjell Magne Fauske',
      author_email = 'kjellmf@gmail.com',
      url = "http://code.google.com/p/inkscape2tikz/",
      download_url = "http://code.google.com/p/inkscape2tikz/downloads/",
      packages = ['svg2tikz','svg2tikz.extensions', 'svg2tikz.inkexlib'],

      scripts=['scripts/svg2tikz'],
      classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent'
        'Programming Language :: Python',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Text Processing :: Markup :: LaTeX',
        'Topic :: Utilities',
       ],
)
