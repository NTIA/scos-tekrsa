
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

Helper Methods
--------------
- `search_connect()`
- `config_spectrum()`

To Do
-----
- Make functions which require string inputs case-insensitive
- Create IQ block and IQ stream acquisition helper methods
- Add 'verbose' option to helper methods
- Test all functions that can be tested with RSA306b


Testing Needed (Can Test with RSA306b)
--------------------------------------
- All `IQBLK` methods
- All `IQSTREAM` methods
- All `SPECTRUM` methods
- All `TIME` methods
- ALL `TRIG` methods

Currently Not Working
---------------------
- `AUDIO_GetData()`
	- Returns all zeros instead of data as expected.
	- Low priority functionality.
- `CONFIG_SetExternalRefEnable()`
	- Can't set to anything other than internal.
- `CONFIG_SetFrequencyReferenceSource()`
	- Can't set to anything other than internal.
- `CONFIG_GetExternalRefFrequency()`
	- Probably works, but can't test due to above two commands being broken.

Testing Needed (RSA500A/600A Only)
----------------------------------
	- These functions would require an RSA500/600A device to test
		- `CONFIG_GetModeGnssFreqRefCorrection()`
		- `CONFIG_DecodeFreqRefUserSettingString()`
		- `CONFIG_GetEnableGnssTimeRefAlign()`
		- `CONFIG_SetEnableGnssTimeRefAlign()`
		- Some options for `CONFIG_SetFrequencyReferenceSource()`
		- Some options for `CONFIG_GetFrequencyReferenceSource()`
		- `CONFIG_GetStatusGnssFreqRefCorrection()`
		- `CONFIG_SetModeGnssFreqRefCorrection()`
		- `CONFIG_GetStatusGnssTimeRefAlign()`
		- `CONFIG_GetFreqRefUserSetting()`
		- `CONFIG_SetFreqRefUserSetting()`
		- `CONFIG_GetAutoAttenuationEnable()`
		- `CONFIG_SetAutoAttenuationEnable()`
		- `CONFIG_GetRFPreampEnable()`
		- `CONFIG_SetRFPreampEnable()`
		- `CONFIG_GetRFAttenuator()`
		- `CONFIG_SetRFAttenuator()`
		- Some options for `DEVICE_GetEventStatus()`
		- All `GNSS` functions
		- `POWER_GetStatus()`
		- All `TRKGEN` functions

Functions Omitted from API Wrapper
----------------------------------
- `DEVICE_GetErrorString()`
	- Using `err_check()` and `SDR_Error` to handle and identify errors.
	- This would be useful to have but the string decoding isn't working right now.
- `DEVICE_GetNomenclatureW()`
	- Using `DEVICE_GetNomenclature()` instead.
	- No reason to implement; redundant.
- All `DPX` functions
	- Low priority functionality, but could be added later.
- All `IFSTREAM` functions
	- Low priority functionality, but could be added later.
- `IQBLK_GetIQData()` and `IQBLK_GetIQDataCplx()`
	- Using `IQBLK_GetIQDataDeinterleaved()` instead.
	- Could add these for even more flexibility, but ultimately unnecessary.
- `IQSTREAM_GetIQData()`, `IQSTREAM_GetIQDataBufferSize()`, `IQSTREAM_SetIQDataBufferSize()`
	- These are only useful if directly receiving IQ data from the IQ Streaming processing, rather than writing IQ Streaming data to file.
	- Currently not necessary, but could be added later.
- `IQSTREAM_SetDiskFilenameBaseW()`
	- Using `IQSTREAM_SetDiskFilenameBase()` instead.
	- No reason to implement; redundant.
- `PLAYBACK_OpenDiskFile()`
	- Low priority functionality, but could be added later.