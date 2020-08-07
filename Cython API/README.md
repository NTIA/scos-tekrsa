Cython API
==========

Note: Currently, this version of the API compiles the importable module successfully, however a segmentation fault occurs when importing the compiled module. It is recommended to use the [Ctypes API](https://github.com/NTIA/scos_tekrsa/tree/master/Ctypes%20API) instead.

This allows for the RSA API to be used in Python without having to think about data type conversion for compatibility. Generally, you'll import the `.so` file which is built by Cython, and then make any API calls as normal, but without worrying about converting to C data types! API functions are renamed as their original name with a `_py` appended: `API_SomeFunction()` --> `API_SomeFunction_py()`.

This code is originally forked from [tektronix/RSA_API](https://github.com/tektronix/RSA_API/tree/master/Python/Cython%20Version). Most of the functions available in the RSA API are implemented here (exceptions/notes listed below). In addition, a few helper methods are added which wrap multiple functions in order to make common acquisitions a little easier. Currently, this code is made for use on Ubuntu with the Linux API from Tektronix, and would require some modification to run properly on Windows.

Usage
-----
1. Compile the `.so` file by running `python3 setup.py build_ext --inplace`.
2. Import the compiled file from Python as needed: `import rsa_api`

Requirements
------------
- Python 3.6+, Cython, and NumPy
- The RSA API for Linux files:
	- `libRSA_API.so`
	- `RSA_API.h` 
- File path for `libRSA_API.so` added to `$LD_LIBRARY_PATH`

To Do
-----
- Route `RSAError`'s to `SDR_Error`
- Implement Tracking Generator functions (low priority, RSA500/600 only)

General Notes
-------------
- API throws errors to `RSAError` class defined in `RSA_API.pyx`
	- Can easily route these to `SDR_Error`
- Cython builds from `.pyx` and `.pxd` files
	- Creates either a `.so` (Unix) or `.pyd` (Windows) file
	- Could affect compatibility/usage down the line

Specific Function Notes
-----------------------
- All `TRKGEN` functions
	- Completely missing with no explanation
- `CONFIG_DecodeFreqRefUserSettingString`
	- Commented out, no explanation
	- Required FREQREF_USER_INFO struct commented out
	- Can't test, RSA500/600 only
- `IQBLK_GetIQDataCplx`
	- Commented out, not working
- `DPX_Configure`
	- Incorporated into `DPX_SetParameters_py()`
	- Not implemented by itself
- `DPX_FinishFrameBuffer`
	- Incorporated into `DPX_GetFrameBuffer_py()`
	- Not implemented by itself
- `AUDIO_GetData`
	- Comment says error checking not working
- `IFSTREAM_SetDiskFileMode`
	- Commented out for being "Legacy"
	- Use `IFSTREAM_SetOutputConfiguration_py()` instead
- `IFSTREAM_GetEQParameters`
	- Commented out, not working
- `IFSTREAM_GetIFFFrames`
	- Commented out, not working
- `IQSTREAM_GetDiskFileInfo`
	- Commented out, no explanation
	- Required `IQSTRMFILEINFO` struct appears to be implemented
- `REFTIME_GetReferenceTimeSource()`
	- Completely missing, no explanation

Helper Methods
--------------
- `IQBLK_Acquire_py()`
- `SPECTRUM_Acquire_py()`
- `DPX_AcquireFB_py()`