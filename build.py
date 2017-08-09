from distutils.core import setup, Extension

setup(name='_acceleration',
      ext_modules=[Extension('_accelerate', sources=['_accelerate.c'],
                             include_dirs=['C:/Program Files (x86)/Windows Kits/10/Include/10.0.10240.0/ucrt',
                                           'C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/include',
                                           'C:/Program Files (x86)/Windows Kits/10/Include/10.0.10240.0/shared'],
                             library_dirs=['C:/Program Files (x86)/Microsoft Visual Studio 14.0/VC/lib',
                                           'C:/Program Files (x86)/Windows Kits/10/Lib/10.0.10240.0/um/x86',
                                           'C:/Program Files (x86)/Windows Kits/10/Lib/10.0.10240.0/ucrt/x86',
                                           ])])
