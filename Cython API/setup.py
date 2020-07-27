# Usage: python3 setup.py build_ext --inplace
import sys
import os
import shutil
from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
import numpy as np

# Location of RSA_API.h and libRSA_API.so
# 	Make sure to also add this path to your $LD_LIBRARY_PATH env. variable
# 	For example, add to ~/.bashrc:
# 	export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib/RSA_API
# 	And then run ldconfig
api_loc = '/usr/local/lib/RSA_API'

# Delete previously compiled files
for root, dirs, files in os.walk(".", topdown=False):
	for name in files:
		if (name.startswith('rsa_api') and not(name.endswith(".pyx") or name.endswith(".pxd"))):
			os.remove(os.path.join(root, name))

# Build Cython module
setup(ext_modules=cythonize(
	[Extension('rsa_api',
		['rsa_api.pyx'],
		libraries=['RSA_API'],
		extra_compile_args=['-Wall'], # Add extra gcc flags
		include_dirs=[api_loc, np.get_include()],
		library_dirs=[api_loc])],
		compiler_directives={'language_level':'3'})
)

# Delete build directory
for root, dirs, files in os.walk('.', topdown=False):
	for name in dirs:
		if (name == 'build'):
			shutil.rmtree(name)