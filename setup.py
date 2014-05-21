try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


setup(name='svg2tikz',
      version='1.0.0dev',
      description='An SVG to TikZ converter',
      author='Kjell Magne Fauske',
      author_email='kjellmf@gmail.com',
      url="https://github.com/kjellmf/svg2tikz",
      packages=['svg2tikz', 'svg2tikz.extensions', 'svg2tikz.inkexlib'],

      scripts=['scripts/svg2tikz'],
      classifiers=[
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
      install_requires=['lxml'],
      entry_points={
          'console_scripts': [
              'svg2tikz = svg2tikz.extensions.tikz_export:main_cmdline',
          ]
      }
)
