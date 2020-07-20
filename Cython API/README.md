Cython API
==========

This allows for the RSA API to be used in Python without having to think about data type conversion for compatibility. Generally, you'll import either the `.so` or `.pyd` file which is built by Cython, and then make any API calls as normal, but without worrying about converting to C data types! API functions are renamed as their original name with a `_py` appended: `API_SomeFunction()` --> `API_SomeFunction_py()`.

This code is originally forked from [tektronix/RSA_API](https://github.com/tektronix/RSA_API/tree/master/Python/Cython%20Version). Most of the functions available in the RSA API are implemented here (exceptions/notes listed below). In addition, a few helper methods are added which wrap multiple functions in order to make common acquisitions a little easier.

Usage
-----
1. Compile the `.pyd` or `.so` file by running `python setup.py build_ext --inplace`.
2. Import the compiled file from Python as needed: `import RSA_API`

To Do
-----
- Route RSAError's to SDR_Error
- Implement Tracking Generator functions (low priority, RSA500/600 only)

General Notes
-------------
- API throws errors to RSAError class defined in RSA_API.pyx
	- Can easily route these to SDR_Error
- Cython builds from .pyx and .pxd files
	- Creates either a .so (unix) or .pyd (Windows) file
	- Could affect compatibility/usage down the line

Specific Function Notes
-----------------------
- All TRKGEN functions
	- Completely missing with no explanation
- CONFIG_DecodeFreqRefUserSettingString
	- Implementation commented out [1.481]
	- Required struct commented out [2.301]
	- Can't test, RSA500/600 only
- IQBLK_GetIQDataCplx
	- Commented out, not working [1.753]
- DPX_Configure
	- Incorporated into DPX_SetParameters_py() [1.916]
	- Not implemented by itself
- DPX_FinishFrameBuffer
	- Incorporated into DPX_GetFrameBuffer_py() [1.986]
	- Not implemented by itself
- AUDIO_GetData
	- Comment says error checking not working [1.1136]
- IFSTREAM_SetDiskFileMode
	- Commented out, "Legacy" [1.1167]
	- Use IFSTREAM_SetOutputConfiguration_py() instead
- IFSTREAM_GetEQParameters
	- Commented out, not working [1.1216]
- IFSTREAM_GetIFFFrames
	- Commented out, not working [1.1253]
- IQSTREAM_GetDiskFileInfo
	- Commented, no explanation [1.1376]
	- Data structure needed appears to be implemented [2.754]
- REFTIME_GetReferenceTimeSource()
	- Completely missing, no explanation

Helper Methods
--------------
- IQBLK_Acquire_py() [1.761]
- SPECTRUM_Acquire_py() [1.867]
- DPX_AcquireFB_py() [1.1017]

Code References
---------------
[1] RSA_API.pyx
[2] RSA_API_h.pxd