#!python

import os
from distutils.core import setup, Extension

if os.name == 'morphos':
    defines = [('__MORPHOS_SHAREDLIBS', None)]
    link_opt = ['GL', 'GLU', 'GLUT', 'm', 'syscall', 'debug' ]
elif os.name == 'posix':
    defines = []
    link_opt = ['GL', 'GLU']

link_opt = ['-l'+x for x in link_opt]

setup(name='lowlevel',
      author='Guillaume Roguez',
      platforms=['morphos'],
      ext_modules = [ Extension('lowlevel', 
                                [ 'src/geometry.c',
                                  'src/lowlevel.c' ],
                                define_macros=defines,
                                extra_link_args=link_opt)
                      ])
