
Ctypes API
==========

This allows for the RSA API to be used in Python without having to think about data type conversion for compatibility. Generally, you'll import the `RSA_API.py` module, and then make any API calls as normal, but without worrying about converting to C data types! API functions are all named exactly as they appear in the RSA API reference manual for ease of use, and most of the information from that manual is included in docstring format along with the relevant Python functions.

Due to the RSA API's use of custom C data structures and enumeration types, some of the Python versions of these API functions work slightly differently. All the information you need about inputs and outputs is contained within the docstring for each function.

Most of the functions available in the RSA API are implemented here (exceptions/notes listed below). In addition, a few helper methods are added which wrap multiple functions in order to make common tasks a little easier.

Usage
-----
1. Import the module into your Python script: `import RSA_API`

Requirements
------------
- Python 3.6+, ctypes, and enum
- The [RSA API](https://www.tek.com/spectrum-analyzer/rsa306-software/rsa-application-programming-interface--api-for-64bit-linux--v100014) for Linux:
	- Install according to documentation included in download
	- Place the following files in a folder called `drivers`, in the same directory as `RSA_API.py`:
		- `libRSA_API.so`
		- `libcyusb_shared.so` 

The following sections are incomplete:

To Do
-----
- Implement remaining API functions
- Finish testing implemented functions
- Make functions which require string inputs case-insensitive
- Create IQ block and IQ stream acquisition helper methods

General Notes
-------------


Specific Function Notes
-----------------------


Helper Methods
--------------
- `search_connect()`
- `config_spectrum()`