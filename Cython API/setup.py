# Usage: python3 setup.py build_ext --inplace
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import numpy as np

setup(
    ext_modules=cythonize(
                [Extension('rsa_api',
                ['rsa_api.pyx'],
                libraries=['RSA_API'],
                include_dirs=['../TekAPI/', np.get_include()],
                library_dirs=['../TekAPI/'])])
)