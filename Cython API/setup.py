# Usage: python3 setup.py build_ext --inplace
import sys
import os
import shutil
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import numpy as np

api_h_loc = '/usr/local/lib/RSA_API' # Location of RSA_API.h
api_lib_loc = '/usr/local/lib/RSA_API' # location of libRSA_API.so

# clean previous build
for root, dirs, files in os.walk(".", topdown=False):
	for name in files:
		if (name.startswith('rsa_api') and not(name.endswith(".pyx") or name.endswith(".pxd"))):
			os.remove(os.path.join(root, name))
	for name in dirs:
		if (name == "build"):
			shutil.rmtree(name)

setup(ext_modules=cythonize(
	[Extension('rsa_api',
		['rsa_api.pyx'],
		libraries=['RSA_API'],
		extra_compile_args=['-g', '-Wall'],
		define_macros=[("NPY_NO_DEPRECATED_API", "NPY_1_7_API_VERSION")],
		include_dirs=[api_h_loc, np.get_include()],
		library_dirs=[api_lib_loc])],
		compiler_directives={'language_level':'3'})
)