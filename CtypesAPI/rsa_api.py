"""
Notes:
- Currently, ALL SDR_Error codes thrown are arbitrary placeholders
- Method "Raises" are only documented if specifically implemented
    - Catch-all err_check() feeds internal API errors into SDR_Error
        - These do not uniquely appear in the docstrings
- ANYTHING that can't run on a 306B is completely untested
    - would need an RSA 500/600 series device to fully test this API wrapper
- Some methods are given default parameter values which aren't
    specified in the original API. This is done for convenience for
    certain methods.
- Some methods require string input. These are currently case sensitive
    - Docstrings clarifies usage

To Do's / Ideas:
- Support multiple devices?
    - currently the search method errors if more than one is found
    - could allow for selection by user input among multiple devices
- Check usage of global constants
    - FreqRefUserSettingString method
"""
from ctypes import *
from sdr_error import SDR_Error
from enum import Enum
import numpy as np

""" LOAD RSA DRIVER """
RTLD_LAZY = 0x0001
LAZYLOAD = RTLD_LAZY | RTLD_GLOBAL
rsa = CDLL('./drivers/libRSA_API.so', LAZYLOAD)
usbapi = CDLL('./drivers/libcyusb_shared.so', LAZYLOAD)

""" GLOBAL CONSTANTS """
MAX_NUM_DEVICES = 10 # Max num. of devices that could be found
MAX_SERIAL_STRLEN = 8 # Bytes allocated for serial number string
MAX_DEVTYPE_STRLEN = 8 # Bytes allocated for device type string
FPGA_VERSION_STRLEN = 6 # Bytes allocated for FPGA version number string
FW_VERSION_STRLEN = 6 # Bytes allocated for FW version number string
HW_VERSION_STRLEN = 4 # Bytes allocated for HW version number string
NOMENCLATURE_STRLEN = 8 # Bytes allocated for device nomenclature string
API_VERSION_STRLEN = 8 # Bytes allocated for API version number string
DEVINFO_MAX_STRLEN = 100 # Bytes for date/time string

""" CUSTOM ENUMERATION TYPES """
# These are defined as tuples, in which the index of each item corresponds
# to the integer value for the item as defined in the API manual
AUDIO_DEMOD_MODE = ('FM_8KHZ', 'FM_13KHZ', 'FM_75KHZ', 'FM_200KHZ',
   'AM_8KHZ', 'NONE')
FREQREF_SOURCE = ("INTERNAL", "EXTREF", "GNSS", "USER")
GFR_MODE = ("OFF", "FREQTRACK", "PHASETRACK", "HOLD")
GFR_STATE = ('OFF', 'ACQUIRING', 'FREQTRACKING', 'PHASETRACKING', 'HOLDING')
GFR_QUALITY = ('INVALID', 'LOW', 'MEDIUM', 'HIGH')
DEVEVENT = ("OVERRANGE", "TRIGGER", "1PPS")
GNSS_SATSYS = ('GPS_GLONASS', 'GPS_BEIDOU', 'GPS', 'GLONASS', 'BEIDOU')
SPECTRUM_WINDOWS = ('Kaiser', 'Mil6dB', 'BlackmanHarris', 'Rectangular',
    'FlatTop', 'Hann')
SPECTRUM_VERTICAL_UNITS = ('dBm', 'Watt', 'Volt', 'Amp', 'dBmV')
SPECTRUM_DETECTORS = ('PosPeak', 'NegPeak', 'AverageVRMS', 'Sample')
IQSOUTDEST = ("CLIENT", "FILE_TIQ", "FILE_SIQ", "FILE_SIQ_SPLIT")
IQSOUTDTYPE = ("SINGLE", "INT32", "INT16", "SINGLE_SCALE_INT32")
REFTIME_SRC = ('NONE', 'SYSTEM', 'GNSS', 'USER')
TRIGGER_MODE = ("freeRun", "Triggered")
TRIGGER_SOURCE = ("External", "IFPowerLevel")
TRIGGER_TRANSITION = ("LH", "HL", "Either")

class ReturnStatus(Enum):
    noError = 0

    # Connection
    errorNotConnected = 101
    errorIncompatibleFirmware = 102
    errorBootLoaderNotRunning = 103
    errorTooManyBootLoadersConnected = 104
    errorRebootFailure = 105

    # POST
    errorPOSTFailureFPGALoad = 201
    errorPOSTFailureHiPower = 202
    errorPOSTFailureI2C = 203
    errorPOSTFailureGPIF = 204
    errorPOSTFailureUsbSpeed = 205
    errorPOSTDiagFailure = 206

    # General Msmt
    errorBufferAllocFailed = 301
    errorParameter = 302
    errorDataNotReady = 304

    # Spectrum
    errorParameterTraceLength = 1101
    errorMeasurementNotEnabled = 1102
    errorSpanIsLessThanRBW = 1103
    errorFrequencyOutOfRange = 1104

    # IF streaming
    errorStreamADCToDiskFileOpen = 1201
    errorStreamADCToDiskAlreadyStreaming = 1202
    errorStreamADCToDiskBadPath = 1203
    errorStreamADCToDiskThreadFailure = 1204
    errorStreamedFileInvalidHeader = 1205
    errorStreamedFileOpenFailure = 1206
    errorStreamingOperationNotSupported = 1207
    errorStreamingFastForwardTimeInvalid = 1208
    errorStreamingInvalidParameters = 1209
    errorStreamingEOF = 1210

    # IQ streaming
    errorIQStreamInvalidFileDataType = 1301
    errorIQStreamFileOpenFailed = 1302
    errorIQStreamBandwidthOutOfRange = 1303

    # -----------------
    # Internal errors
    # -----------------
    errorTimeout = 3001
    errorTransfer = 3002
    errorFileOpen = 3003
    errorFailed = 3004
    errorCRC = 3005
    errorChangeToFlashMode = 3006
    errorChangeToRunMode = 3007
    errorDSPLError = 3008
    errorLOLockFailure = 3009
    errorExternalReferenceNotEnabled = 3010
    errorLogFailure = 3011
    errorRegisterIO = 3012
    errorFileRead = 3013

    errorDisconnectedDeviceRemoved = 3101
    errorDisconnectedDeviceNodeChangedAndRemoved = 3102
    errorDisconnectedTimeoutWaitingForADcData = 3103
    errorDisconnectedIOBeginTransfer = 3104
    errorOperationNotSupportedInSimMode = 3015

    errorFPGAConfigureFailure = 3201
    errorCalCWNormFailure = 3202
    errorSystemAppDataDirectory = 3203
    errorFileCreateMRU = 3204
    errorDeleteUnsuitableCachePath = 3205
    errorUnableToSetFilePermissions = 3206
    errorCreateCachePath = 3207
    errorCreateCachePathBoost = 3208
    errorCreateCachePathStd = 3209
    errorCreateCachePathGen = 3210
    errorBufferLengthTooSmall = 3211
    errorRemoveCachePath = 3212
    errorGetCachingDirectoryBoost = 3213
    errorGetCachingDirectoryStd = 3214
    errorGetCachingDirectoryGen = 3215
    errorInconsistentFileSystem = 3216

    errorWriteCalConfigHeader = 3301
    errorWriteCalConfigData = 3302
    errorReadCalConfigHeader = 3303
    errorReadCalConfigData = 3304
    errorEraseCalConfig = 3305
    errorCalConfigFileSize = 3306
    errorInvalidCalibConstantFileFormat = 3307
    errorMismatchCalibConstantsSize = 3308
    errorCalConfigInvalid = 3309

    # flash
    errorFlashFileSystemUnexpectedSize = 3401,
    errorFlashFileSystemNotMounted = 3402
    errorFlashFileSystemOutOfRange = 3403
    errorFlashFileSystemIndexNotFound = 3404
    errorFlashFileSystemReadErrorCRC = 3405
    errorFlashFileSystemReadFileMissing = 3406
    errorFlashFileSystemCreateCacheIndex = 3407
    errorFlashFileSystemCreateCachedDataFile = 3408
    errorFlashFileSystemUnsupportedFileSize = 3409
    errorFlashFileSystemInsufficentSpace = 3410
    errorFlashFileSystemInconsistentState = 3411
    errorFlashFileSystemTooManyFiles = 3412
    errorFlashFileSystemImportFileNotFound = 3413
    errorFlashFileSystemImportFileReadError = 3414
    errorFlashFileSystemImportFileError = 3415
    errorFlashFileSystemFileNotFoundError = 3416
    errorFlashFileSystemReadBufferTooSmall = 3417
    errorFlashWriteFailure = 3418
    errorFlashReadFailure = 3419
    errorFlashFileSystemBadArgument = 3420
    errorFlashFileSystemCreateFile = 3421

    # Aux monitoring
    errorMonitoringNotSupported = 3501,
    errorAuxDataNotAvailable = 3502

    # battery
    errorBatteryCommFailure = 3601
    errorBatteryChargerCommFailure = 3602
    errorBatteryNotPresent = 3603

    # EST
    errorESTOutputPathFile = 3701
    errorESTPathNotDirectory = 3702
    errorESTPathDoesntExist = 3703
    errorESTUnableToOpenLog = 3704
    errorESTUnableToOpenLimits = 3705

    # Revision information
    errorRevisionDataNotFound = 3801

    # alignment
    error112MHzAlignmentSignalLevelTooLow = 3901
    error10MHzAlignmentSignalLevelTooLow = 3902
    errorInvalidCalConstant = 3903
    errorNormalizationCacheInvalid = 3904
    errorInvalidAlignmentCache = 3905

    # acq status
    errorADCOverrange = 9000
    errorOscUnlock = 9001

    errorNotSupported = 9901

    errorPlaceholder = 9999
    notImplemented = -1

""" CUSTOM DATA STRUCTURES """
class FREQREF_USER_INFO(Structure):
    _fields_ = [('isvalid', c_bool),
                ('dacValue', c_int),
                ('datetime', c_char * DEVINFO_MAX_STRLEN),
                ('temperature', c_double)]

class DEVICE_INFO(Structure):
    _fields_ = [('nomenclature', c_char_p),
                ('serialNum', c_char_p),
                ('apiVersion', c_char_p),
                ('fwVersion', c_char_p),
                ('fpgaVersion', c_char_p),
                ('hwVersion', c_char_p)]

class POWER_INFO(Structure):
    _fields_ = [('externalPowerPresent', c_bool),
                ('batteryPresent', c_bool),
                ('batteryChargeLevel', c_double),
                ('batteryCharging', c_bool),
                ('batteryOverTemperature', c_bool),
                ('batteryHardwareError', c_bool)]

class SPECTRUM_LIMITS(Structure):
    _fields_ = [('maxSpan', c_double),
                ('minSpan', c_double),
                ('maxRBW', c_double),
                ('minRBW', c_double),
                ('maxVBW', c_double),
                ('minVBW', c_double),
                ('maxTraceLength', c_int),
                ('minTraceLength', c_int)]

class SPECTRUM_SETTINGS(Structure):
    _fields_ = [('span', c_double),
                ('rbw', c_double),
                ('enableVBW', c_bool),
                ('vbw', c_double),
                ('traceLength', c_int),
                ('window', c_int),
                ('verticalUnit', c_int),
                ('actualStartFreq', c_double),
                ('actualStopFreq', c_double),
                ('actualFreqStepSize', c_double),
                ('actualRBW', c_double),
                ('actualVBW', c_double),
                ('actualNumIQSamples', c_double)]

class SPECTRUM_TRACEINFO(Structure):
    _fields_ = [('timestamp', c_int64),
                ('acqDataStatus', c_uint16)]

class IQBLK_ACQINFO(Structure):
    _fields_ = [('sample0Timestamp', c_uint64),
                ('triggerSampleIndex', c_uint64),
                ('triggerTimestamp', c_uint64),
                ('acqStatus', c_uint32)]

class IQSTREAM_File_Info(Structure):
    _fields_ = [('numberSamples', c_uint64),
                ('sample0Timestamp', c_uint64),
                ('triggerSampleIndex', c_uint64),
                ('triggerTimestamp', c_uint64),
                ('acqStatus', c_uint32),
                ('filenames', c_wchar_p)]

""" HELPER METHODS """

# This error checker throws any internal API errors to SDR_Error.
# It passes through the error code ("return status") from the API.
# - Could easily be made to give return status number as SDR error code
# - For now, all will give SDR_Error code 200
def err_check(rs):
    if ReturnStatus(rs) != ReturnStatus.noError:
        raise SDR_Error(0, "Error running API command.",
            "RSA API ReturnStatus {}: ".format(str(rs))
            + ReturnStatus(rs).name
        )

def search_connect(loadPreset=True, verbose=False):
    """
    Search for and connect to a Tektronix RSA device. 
    
    More than 10 devices cannot be found at once. Search criteria are
    not implemented, and connection only occurs if exactly one device is
    found. It may be more convenient to simply use DEVICE_Connect(),
    however this helper method is useful if preset configuration is
    desired or if problems are encountered when searching for or
    connecting to a device. 

    Preset configuration is optionally loaded upon connection. This
    results in: trigger mode set to Free Run, center frequency to 1.5
    GHz, span to 40 MHz, IQ record length to 1024 samples, and
    reference level to 0 dBm. Preset functionality is enabled by
    default.

    Parameters
    ----------
    loadPreset : bool
        Whether to load the preset configuration upon connection.
    verbose : bool
        Whether to print the steps of the process as they happen.

    Raises
    ------
    SDR_Error
        If no matching device is found, if more than one matching
        device are found, or if a single device is found but connection
        fails.
    """
    if verbose:
        print("Searching for devices...")

    foundDevices = DEVICE_Search()
    numFound = len(foundDevices)

    if numFound == 1:
        foundDevString = "The following device was found:"
    elif numFound > 1:
        foundDevString = "The following devices were found:"
    for (ID, key) in foundDevices.items():
        foundDevString += '\r\n{}'.format(str(ID) + ': ' + str(key))

    if verbose:
        print("Device search completed.\n")
        print(foundDevString + '\n')

    # Zero devices found case handled within DEVICE_Search()
    # Multiple devices found case:
    if numFound > 1:
        raise SDR_Error(0,
            "Found {} devices, need exactly 1.".format(numFound),
            foundDevString)
    else:
        if verbose:
            print("Connecting to device...")
        DEVICE_Connect()
        if verbose:
            print("Device connected.\n")

    if loadPreset:
        if verbose:
            print("Loading device preset configuration...")
        CONFIG_Preset()
        if verbose:
            print("Device preset configuration loaded.\n")

def config_spectrum(cf, refLevel, span, rbw, verbose=False):
    """
    Performs spectrum configurations.
    """
    SPECTRUM_SetEnable(True)
    CONFIG_SetCenterFreq(cf)
    CONFIG_SetReferenceLevel(refLevel)
    SPECTRUM_SetDefault()
    (spnVal, rbwVal, enVBW, vbw, trcLn, win, vrtUnt) = SPECTRUM_GetSettings()
    spnVal = span
    win = 'Kaiser'
    vrtUnt = 'dBm'
    rbwVal = rbw
    SPECTRUM_SetSettings(spnVal, rbwVal, enVBW, vbw, trcLn, win, vrtUnt)
    if verbose:
        (spnVal, rbwVal, enVBW, vbw, trcLn, win, vrtUnt) = SPECTRUM_GetSettings()
        print(f"Span: {spnVal}\n RBW: {rbwVal}\nVBW Enable: {enVBW}\nVBW: {vbw}\n"
        + f"Trace Length: {trcLn}\nWindow: {win}\nVertical Unit: {vrtUnt}")

def config_iqblk(cf, refLevel, iqBw, recordLength):
    """Configure device for IQ block collecion"""
    CONFIG_SetCenterFreq(cf)
    CONFIG_SetReferenceLevel(refLevel)
    IQBLK_SetIQBandwidth(iqBw)
    IQBLK_SetIQRecordLength(recordLength)

def iqblk_collect(recordLength=1024, timeoutMsec=100):
    # Acquire and return IQ Block data
    # !! Configure device BEFORE calling this method
    # Input: Record length [num. of samples]
    # Returns single complex IQ numpy array

    # Begin data acquisition
    DEVICE_Run()
    IQBLK_AcquireIQData()

    # Wait for device to be ready to send data
    ready = False
    while not ready:
        # Default 100ms timeout
        ready = IQBLK_WaitForIQDataReady(timeoutMsec)

    # Retrieve data
    (iData, qData, outLen) = IQBLK_GetIQDataDeinterleaved(recordLength)

    # Stop device before exiting
    DEVICE_Stop()

    return iData + 1j * qData

""" ALIGNMENT METHODS """

def ALIGN_GetAlignmentNeeded():
    """
    Determine if an alignment is needed or not.

    This is based on the difference between the current temperature
    and the temperature from the last alignment.

    Returns
    -------
    bool
        True indicates an alignment is needed, False for not needed.
    """
    needed = c_bool()
    err_check(rsa.ALIGN_GetAlignmentNeeded(byref(needed)))
    return needed.value

def ALIGN_GetWarmupStatus():
    """
    Report device warm-up status.

    Devices start in the "warm-up" state after initial power up until
    the internal temperature stabilizes. The warm-up interval is
    different for different devices.

    Returns
    -------
    bool
        True indicates device warm-up interval reached.
        False indicates warm-up has not been reached
    """
    warmedUp = c_bool()
    err_check(rsa.ALIGN_GetWarmupStatus(byref(warmedUp)))
    return warmedUp.value

def ALIGN_RunAlignment():
    """Run the device alignment process."""
    err_check(rsa.ALIGN_RunAlignment())

""" AUDIO METHODS """

def AUDIO_SetFrequencyOffset(freqOffsetHz):
    """
    Set the audio carrier frequency offset from the center frequency.

    This method allows the audio demodulation carrier frequency to be
    offset from the device's center frequency. This allows tuning
    different carrier frequencies without changing the center
    frequency. The audio demodulation is performed at a carrier
    frequency of (center frequency + freqOffsetHz). The freqOffsetHz is
    set to an initial value of 0 Hz at the time the device is connected.

    Parameters
    ----------
    freqOffsetHz : float
        Amount of frequency offset from the center frequency, in Hz.
        Range: -20e6 <= freqOffsetHz <= 20e6
    """
    err_check(rsa.AUDIO_SetFrequencyOffset(c_double(freqOffsetHz)))

def AUDIO_GetFrequencyOffset():
    """
    Query the audio carrier frequency offset from the center frequency.

    Returns
    -------
    float
        Current audio frequency offset from the center frequency in Hz.
    """
    freqOffsetHz = c_double()
    err_check(rsa.AUDIO_GetFrequencyOffset(byref(freqOffsetHz)))
    return freqOffsetHz.value

def AUDIO_GetEnable():
    """
    Query the audio demodulation run state.

    Returns
    -------
    bool
        True indicates audio demodulation is running.
        False indicates it is stopped.
    """
    enable = c_bool()
    err_check(rsa.AUDIO_GetEnable(byref(enable)))
    return enable.value

def AUDIO_GetData(inSize):
    """
    Return audio sample data in a user buffer.

    Parameters
    ----------
    inSize : int
        Maximum amount of audio data samples allowed.

    Returns
    -------
    data : int array
        Contains an array of audio data.
    outSize : int
        Amount of audio data samples stored in the data array.
    """
    data = (c_int16 * inSize)()
    outSize = c_uint16()
    err_check(rsa.AUDIO_GetData(byref(data), c_uint16(inSize), byref(outSize)))
    # The line below requires numpy to be imported as np
    return np.ctypeslib.as_array(data), outSize.value

def AUDIO_GetMode():
    """
    Query the audio demodulation mode.

    The audio demodulation mode must be set manually before querying.

    Returns
    -------
    str
        The audio demodulation mode. Valid results:
            FM_8KHZ, FM_13KHZ, FM_75KHZ, FM_200KHZ, AM_8KHZ, or NONE.

    Raises
    ------
    SDR_Error
        If the audio demodulation mode has not yet been set.
    """
    mode = c_int()
    err_check(rsa.AUDIO_GetMode(byref(mode)))
    if mode.value > 5 or mode.value < 0:
        raise SDR_Error(0, "Failed to get audio demodulation mode.",
            "Set the demodulation mode with AUDIO_SetMode before querying.")
    return AUDIO_DEMOD_MODE[mode.value]

def AUDIO_GetMute():
    """
    Query the status of the mute operation.

    The status of the mute operation does not stop the audio processing
    or data callbacks.

    Returns
    -------
    bool
        The mute status of the output speakers. True indicates output
            is muted, False indicates output is not muted.
    """
    mute = c_bool()
    err_check(rsa.AUDIO_GetMute(byref(mute)))
    return mute.value

def AUDIO_GetVolume():
    """Query the volume, which must be a real value from 0 to 1."""
    volume = c_float()
    err_check(rsa.AUDIO_GetVolume(byref(volume)))
    return volume.value

def AUDIO_SetMode(mode):
    """
    Set the audio demodulation mode.

    Parameters
    ----------
    mode : str
        Desired audio demodulation mode. Valid settings:
            FM_8KHZ, FM_13KHZ, FM_75KHZ, FM_200KHZ, AM_8KHZ, NONE

    Raises
    ------
    SDR_Error
        If the input string does not match one of the valid settings.
    """
    if mode in AUDIO_DEMOD_MODE:
        value = c_int(AUDIO_DEMOD_MODE.index(mode))
        err_check(rsa.AUDIO_SetMode(value))
    else:
        raise SDR_Error(0,
            "Input string does not match one of the valid settings.",
            "Please input one of: FM_8KHZ, FM_13KHZ, FM_75KHZ, FM_200KHZ,"
            + "AM_8KHZ, or NONE."
        )

def AUDIO_SetMute(mute):
    """
    Set the mute status.

    Does not affect the data processing or callbacks.

    Parameters
    ----------
    mute : bool
        Mute status. True mutes the output, False restores the output.
    """
    err_check(rsa.AUDIO_SetMute(c_bool(mute)))

def AUDIO_SetVolume(volume):
    """
    Set the volume value.

    Input must be a real number ranging from 0 to 1. If the value is
    outside of the specified range, clipping occurs.

    Parameters
    ----------
    volume : float
        Volume value. Range: 0.0 to 1.0.
    """
    err_check(rsa.AUDIO_SetVolume(c_float(volume)))

def AUDIO_Start():
    """Start the audio demodulation output generation."""
    err_check(rsa.AUDIO_Start())

def AUDIO_Stop():
    """Stop the audio demodulation output generation."""
    err_check(rsa.AUDIO_Stop())

""" CONFIG METHODS """

def CONFIG_GetCenterFreq():
    """Return the current center frequency in Hz."""
    cf = c_double()
    err_check(rsa.CONFIG_GetCenterFreq(byref(cf)))
    return cf.value

def CONFIG_GetExternalRefEnable():
    """
    Return the state of the external reference.

    This method is less useful than CONFIG_GetFrequencyReferenceSource(),
    because it only indicates if the external reference is chosen or
    not. The CONFIG_GetFrequencyReferenceSource() method indicates all
    available sources, and should often be used in place of this one.

    Returns
    -------
    bool
        True means external reference is enabled, False means disabled.
    """
    exRefEn = c_bool()
    err_check(rsa.CONFIG_GetExternalRefEnable(byref(exRefEn)))
    return exRefEn.value

def CONFIG_GetExternalRefFrequency():
    """
    Return the frequency, in Hz, of the external reference.

    The external reference input must be enabled for this method to
    return useful results.

    Returns
    -------
    float
        The external reference frequency, measured in Hz.

    Raises
    ------
    SDR_Error
        If there is no external reference input in use.
    """
    src = CONFIG_GetFrequencyReferenceSource()
    if src == FREQREF_SOURCE[0]:
        raise SDR_Error(0,
            "External reference input is not in use.",
            "The external reference input must be enabled for useful results."
        )
    else:
        extFreq = c_double()
        err_check(rsa.CONFIG_GetExternalRefFrequency(byref(extFreq)))
        return extFreq.value

def CONFIG_GetFrequencyReferenceSource():
    """
    Return a string representing the frequency reference source.

    Note: The RSA306 and RSA306B support only INTERNAL and EXTREF
    sources.

    Returns
    -------
    string
        Name of the frequency reference source. Valid results:
            INTERNAL : Internal frequency reference.
            EXTREF : External (Ref In) frequency reference.
            GNSS : Internal GNSS receiver reference
            USER : Previously set USER setting, or, if none, INTERNAL.
    """
    src = c_int()
    err_check(rsa.CONFIG_GetFrequencyReferenceSource(byref(src)))
    return FREQREF_SOURCE[src.value]

def CONFIG_GetMaxCenterFreq():
    """Return the maximum center frequency in Hz."""
    maxCF = c_double()
    err_check(rsa.CONFIG_GetMaxCenterFreq(byref(maxCF)))
    return maxCF.value

def CONFIG_GetMinCenterFreq():
    """Return the minimum center frequency in Hz."""
    minCF = c_double()
    err_check(rsa.CONFIG_GetMinCenterFreq(byref(minCF)))
    return minCF.value

def CONFIG_GetModeGnssFreqRefCorrection():
    """
    Return the operating mode of the GNSS freq. reference correction.

    Note: This method is for RSA500A/600A series instruments only.

    Please refer to the CONFIG_SetModeGnssFreqRefCorrection()
    documentation for an explanation for the various operating modes.

    Returns
    -------
    string
        The GNSS frequency reference operating mode. Valid results:
            OFF : GNSS source is not selected. 
            FREQTRACK : FREQTRACK mode enabled.
            PHASETRACK : PHASETRACK mode enabled.
            HOLD : HOLD mode enabled.
    """
    mode = c_int()
    err_check(rsa.CONFIG_GetModeGnssFreqRefCorrection(byref(mode)))
    if mode.value != 0:
        return GFR_MODE[mode.value + 1]
    else:
        return GFR_MODE[mode.value]

def CONFIG_GetReferenceLevel():
    """Return the current reference level, measured in dBm."""
    refLevel = c_double()
    err_check(rsa.CONFIG_GetReferenceLevel(byref(refLevel)))
    return refLevel.value

def CONFIG_Preset():
    """
    Set the connected device to preset values.

    This method sets the trigger mode to Free Run, the center frequency
    to 1.5 GHz, the span to 40 MHz, the IQ record length to 1024 
    samples, and the reference level to 0 dBm.
    """
    err_check(rsa.CONFIG_Preset())

def CONFIG_SetCenterFreq(cf):
    """
    Set the center frequency value, in Hz.

    When using the tracking generator, be sure to set the tracking
    generator output level before setting the center frequency.

    Parameters
    ----------
    cf : float or int
        Value to set center frequency, in Hz.

    Raises
    ------
    SDR_Error
        If the desired center frequency is outside the allowed range.
    """
    minCF = CONFIG_GetMinCenterFreq()
    maxCF = CONFIG_GetMaxCenterFreq()
    if minCF <= cf <= maxCF:
        err_check(rsa.CONFIG_SetCenterFreq(c_double(cf)))
    else:
        raise SDR_Error(0,
            "Desired center frequency not in range.",
            "Please enter a value between {} and {} Hz.".format(minCF, maxCF)
        )

def CONFIG_DecodeFreqRefUserSettingString(i_usstr):
    """
    Decodes a formatted User setting string into component elements.

    Note: This method is for RSA500A/600A series instruments only.

    Parameters
    ----------
    i_usstr : string
        Formatted User setting string.

    Returns
    -------
    isvalid : bool
        True if User setting string has valid data, False if not.
        If False, the remaining elements below are invalid.
    dacValue : int
        Control DAC value.
    datetime : string
        String of date+time the User setting was created. Format:
        "YYYY-MM-DDThh:mm:ss".
    temperature : float
        Device temperature when the User setting data was created.
    """
    i_usstr = c_char_p(i_usstr)
    o_fui = FREQREF_USER_INFO()
    err_check(rsa.CONFIG_DecodeFreqRefUserSettingString(byref(i_usstr),
        byref(o_fui)))
    return (o_fui.isvalid.value, o_fui.dacValue.value, o_fui.datetime.value,
        o_fui.temperature.value)

def CONFIG_GetEnableGnssTimeRefAlign():
    """
    Return the setting of time ref. alignment from the GNSS receiver.

    Note: This method is for RSA500A/600A series instruments only.

    The GNSS receiver must be enabled to use this method.

    Returns
    -------
    bool
        True means the time reference setting is enabled. False means
        the time reference setting is disabled.
    """
    enable = c_bool()
    err_check(rsa.CONFIG_GetEnableGnssTimeRefAlign(byref(enable)))
    return enable.value

def CONFIG_SetEnableGnssTimeRefAlign(enable=True):
    """
    Control the time ref. alignment from the internal GNSS receiver.

    Note: This method is for RSA500A/600A series instruments only.

    The GNSS receiver must be enabled to use this method.

    The default control setting of True enables the API time reference
    system to be aligned precisely to UTC time from the GNSS navigation
    message and 1PPS signal. The GNSS receiver must achieve navigation
    lock for the time reference alignment to occur. While GNSS is
    locked, the time reference is updated every 10 seconds to keep
    close synchronization with GNSS time. Setting the control to False
    disables the time reference updating from GNSS, but retains the
    current time reference setting. This control allows the user
    application to independently set the time reference, or simply
    prevent time updates from the GNSS.

    Parameters
    ----------
    enable : bool
        True enables setting time reference. False disables setting
        time reference. Defaults to True.
    """
    err_check(rsa.CONFIG_SetEnableGnssTimeRefAlign(c_bool(enable)))

def CONFIG_SetExternalRefEnable(exRefEn):
    """
    Enable or disable the external reference.

    When the external reference is enabled, an external reference
    signal must be connected to the "Ref In" port. The signal must have
    a frequency of 10 MHz with a +10 dBm maximum amplitude. This signal
    is used by the local oscillators to mix with the input signal.

    When the external reference is disabled, an internal reference
    source is used.

    Parameters
    ----------
    exRefEn : bool
        True enables the external reference. False disables it.
    """
    err_check(rsa.CONFIG_SetExternalRefEnable(c_bool(exRefEn)))

def CONFIG_SetFrequencyReferenceSource(src):
    """
    Select the device frequency reference source.

    Note: RSA306B and RSA306 support only INTERNAL and EXTREF sources.

    The INTERNAL source is always a valid selection, and is never
    switched out of automatically.

    The EXTREF source uses the signal input to the Ref In connector as
    frequency reference for the internal oscillators. If EXTREF is
    selected without a valid signal connected to Ref In, the source
    automatically switches to USER if available, or to INTERNAL
    otherwise. If lock fails, an error status indicating the failure is
    returned.

    The GNSS source uses the internal GNSS receiver to adjust the
    internal reference oscillator. If GNSS source is selected, the GNSS
    receiver must be enabled. If the GNSS receiver is not enabled, the
    source selection remains GNSS, but no frequency correction is done.
    GNSS disciplining only occurs when the GNSS receiver has navigation
    lock. When the receiver is unlocked, the adjustment setting is
    retained unchanged until receiver lock is achieved or the source is
    switched to another selection

    If USER source is selected, the previously set USER setting is
    used. If the USER setting has not been set, the source switches
    automatically to INTERNAL.

    Parameters
    ----------
    src : string
        Frequency reference source selection. Valid settings:
            INTERNAL : Internal frequency reference.
            EXTREF : External (Ref In) frequency reference.
            GNSS : Internal GNSS receiver reference
            USER : Previously set USER setting, or, if none, INTERNAL.

    Raises
    ------
    SDR_Error
        If the input string does not match one of the valid settings.
    """
    if src in FREQREF_SOURCE:
        value = c_int(FREQREF_SOURCE.index(src))
        err_check(rsa.CONFIG_SetFrequencyReferenceSource(value))
    else:
        raise SDR_Error(
            0,
            "Input string does not match one of the valid settings.",
            "Please input one of: INTERNAL, EXTREF, GNSS, or USER."
        )

def CONFIG_GetStatusGnssFreqRefCorrection():
    """
    Return the status of the GNSS frequency reference correction.

    Note: This method is for RSA500A/600A series instruments only.

    The GNSS receiver must be enabled and selected as the frequency
    reference source ("GNSS") to use this method.

    The "state" value indicates the current internal state of the GNSS
    frequency reference adjustment system. The states mostly correspond
    to the possible control modes, but also indicate how initialization
    and/or tracking is going.

    When GNSS source is selected, the frequency reference adjustment
    system enters the ACQUIRING state, until it achieves navigation
    lock. Until the receiver locks, no frequency adjustments are done.
    It continues in this state until oscillator adjustments bring the
    internal oscillator frequency within +/- 1 ppm of the ideal GNSS
    1PPS frequency.

    In the FREQTRACKING state, only small adjustments are allowed. The
    adjustments attempt to minimize the difference between the 1PPS
    pulse frequency and the internal oscillator frequency.

    In the PHASETRACKING state, only small adjustments are allowed. The
    adjustments attempt to maintain the sample timing at a consistent
    relationship to the 1PPS signal interval. If the timing cannot be
    maintained within +/- 100 microsecond range, the state will
    transition to FREQTRACKING.

    The HOLDING state may be caused by intentionally setting the mode
    to HOLD (see setModeGnssFreqRefCorrection()). It may also occur if
    GNSS navigation lock is lost. During the unlock interval, the
    HOLDING state is in effect and the most recent adjustment setting
    is maintained.

    The "quality" value indicates how well the frequency adjustment is
    performing. It is valid only when "state" is FREQTRACKING or
    PHASETRACKING. Otherwise, it returns INVALID. See below for more
    specific information about each possible returned value.

    Returns
    -------
    state : string
        GNSS frequency reference correction state. Valid results:
            OFF : GNSS not selected as frequency reference source.
            ACQUIRING : Initial synchronization and alignment of the
                oscillator is occurring.
            FREQTRACKING : Fine adjustment of the reference oscillator
                is occurring. See above for more info.
            PHASETRACKING : Fine adjustment of the reference oscillator
                is occurring. See above for more info.
            HOLDING : Frequency adjustments are disabled.
    quality : string
        Quality of frequency adjustment performance. Valid results:
            INVALID : 
            LOW : Frequency error is > 0.2 ppm
            MEDIUM : 0.2 ppm > Frequency error > 0.025 ppm
            HIGH : Frequency error < 0.025 ppm

    Raises
    ------
    SDR_Error
        If the frequency source is not set to GNSS.
    """
    if CONFIG_GetFrequencyReferenceSource() == 'GNSS':
        state = c_int()
        quality = c_int()
        err_check(rsa.CONFIG_GetStatusGnssFreqRefCorrection(byref(state),
            byref(quality)))
        return GFR_STATE[state.value], GFR_QUALITY[quality.value]
    else:
        raise SDR_Error(0, "Frequency reference source not set to GNSS.",
            "Unable to get correction status for non-GNSS sources."
        )

def CONFIG_SetModeGnssFreqRefCorrection(mode):
    """
    Control the operating mode of GNSS frequency reference correction.

    Note: This method is for RSA500A/600A series instruments only.

    The GNSS receiver must be enabled and selected as the frequency
    reference source ("GNSS") to use this method.

    When the GNSS source is selected, the mode is always initially set
    to FREQTRACK. Other modes must be explicitly set after selecting
    the GNSS source. If the GNSS source is deselected and later re-
    selected, the mode is set to FREQTRACK. There is no memory of
    previous mode settings. The mode setting may be changed at any time
    while GNSS is selected. However, control changes may take up to 50
    msec to be processed, so should not be posted at a high rate. If
    multiple control changes are posted quickly, the method will
    "stall" after the first one until each change is accepted and
    processed, taking 50 msec per change.

    FREQTRACK mode uses the GNSS internal 1PPS pulse as a high-accuracy
    frequency source to correct the internal reference oscillator
    frequency. It adjusts the oscillator to minimize the frequency
    difference between it and the 1PPS signal. This is the normal
    operating mode, and can usually be left in this mode unless special
    conditions call for switching to the other modes. When need for the
    other modes is over, FREQTRACK mode should be restored.

    PHASETRACK mode is similar to FREQTRACK mode, as it adjusts the
    reference oscillator based on the 1PPS signal. However, it attempts
    to maintain, on average, a consistent number of oscillator cycles
    within a 1PPS interval. This is useful when recording long IF or IQ
    data records, as it keeps the data sample timing aligned over the
    record, to within +/- 100 nsec of the 1PPS time location when the
    mode is initiated. PHASETRACK mode does more oscillator adjustments
    than FREQTRACK mode, so it should only be used when specifically
    needed for long-term recording. When GNSS source is first selected,
    FREQTRACK mode should be selected until the tracking quality has
    reached MEDIUM, before using PHASETRACK mode.

    HOLD mode pauses the oscillator adjustments without stopping the
    GNSS monitoring. This can be used to prevent oscillator adjustments
    during acquisitions. Remember that the mode change can take up to
    50 msec to be accepted.

    Parameters
    ----------
    mode : string
        The GNSS frequency reference operating mode. Valid settings:
            FREQTRACK : Set to FREQTRACK; more detail given above.
            PHASETRACK : Set to PHASETRACK; more detail given above.
            HOLD : Set to HOLD; more detail given above.

    Raises
    ------
    SDR_Error
        If the input string does not match one of the valid settings.
    """
    if mode in GFR_MODE and mode is not 'OFF':
        value = GFR_MODE.index(mode) + 1
        err_check(rsa.CONFIG_SetModeGnssFreqRefCorrection(c_int(value)))
    else:
        raise SDR_Error(0,
            "Input string does not match one of the valid settings.",
            "Please input one of: FREQTRACK, PHASETRACK, or HOLD.")

def CONFIG_GetStatusGnssTimeRefAlign():
    """
    Get status of API time reference alignment from the GNSS receiver.

    Note: This method is for RSA500A/600A series instruments only.

    The GNSS receiver must be enabled to use this method. If GNSS
    time ref. setting is disabled (see getEnableGnssTimeRefAlign()),
    this method returns False even if the time reference was previously
    set from the GNSS receiver.

    Returns
    -------
    bool
        True if time ref. was set from GNSS receiver, False if not.
    """
    aligned = c_bool()
    err_check(rsa.CONFIG_GetStatusGnssTimeRefAlign(byref(aligned)))

def CONFIG_GetFreqRefUserSetting():
    """
    Get the frequency reference User-source setting value.

    Note: This method is for RSA500A/600A series instruments only.

    This method is normally used when creating a User setting string
    for external non-volatile storage. It can also be used to query the
    current User setting data incase the ancillary information is
    desired. The CONFIG_DecodeFreqRefUserSettingString() method can
    then be used to extract the individual items.

    The format of the returned string is: "$FRU,<devType>,<devSN>,
    <dacVal>,<dateTime>,<devTemp>*<CS>", where:
        <devType> : device type.
        <devSN> : device serial number.
        <dacVal> integer DAC value.
        <dateTime> : date/time of creation (fmt: YYYY-MM-DDThh:mm:ss).
        <devTemp> : device temperature (deg. C) at creation.
        <CS> : integer checksum of chars before '*' char

    Ex: "$FRU,RSA503A,Q000098,2062,2016-06-06T18:11:08,51.41*87"

    If the User setting is not valid, the user string result returns
    the string "Invalid User Setting".

    Returns
    -------
    string
        Formatted user setting string. See above for details.
    """
    # This data type handling is likely incorrect
    # But I can't test it to find out for sure
    o_usstr = c_char_p()
    err_check(rsa.CONFIG_GetFreqRefUserSetting(byref(o_usstr)))
    return o_usstr.value

def CONFIG_SetFreqRefUserSetting(i_usstr):
    """
    Set the frequency reference User-source setting value.

    Note: This method is for RSA500A/600A series instruments only.

    The user setting string input must be formatted correctly, as per
    the CONFIG_GetFreqRefUserSetting() method. If it is valid (format
    decodes correctly and matches the device), it is used to set the
    User setting memory. If the string is invalid, the User setting is
    not changed.

    This method is provided to support store and recall of User
    frequency reference setting. This method only sets the User
    setting value used during the current device connected session. The
    value is lost when disconnected.

    With a NULL input, this method causes the current frequency
    reference control setting to be copied to the internal User setting
    memory. Then the User setting can be retrieved as a formatted
    string by using the CONFIG_GetFreqRefUserSetting() method, for
    storage by the user application. These operations are normally done
    only after GNSS frequency reference correction has been used to
    produce an improved frequency reference setting which the user
    wishes to use in place of the default INTERNAL factory setting.
    After using CONFIG_SetFreqRefUserSetting(),
    CONFIG_SetFrequencyReferenceSource() can be used to select the new
    User setting for use as the frequency reference.

    This method can be used to set the internal User setting memory to
    the values in a valid previously-generated formatted string
    argument. This allows applications to recall previously stored User
    frequency reference settings as desired. The USER source should
    then  be selected with the CONFIG_SetFrequencyReferenceSource()
    method.

    The formatted user setting string is specific to the device it was
    generated on and will not be accepted if input to this method on
    another device.

    Parameters
    ----------
    i_usstr : string
        A string as formatted by the CONFIG_GetFreqRefUserSetting() method.
    """
    i_usstr = c_char(i_usstr)
    err_check(rsa.CONFIG_SetFreqRefUserSetting(byref(i_usstr)))

def CONFIG_SetReferenceLevel(refLevel):
    """
    Set the reference level

    The reference level controls the signal path gain and attenuation
    settings. The value should be set to the maximum expected signal
    power level in dBm. Setting the value too low may result in over-
    driving the signal path and ADC, while setting it too high results
    in excess noise in the signal.

    Parameters
    ----------
    refLevel : float or int
        Reference level, in dBm. Valid range: -130 dBm to 30 dBm.

    Raises
    ------
    SDR_Error
        If the desired reference level is outside the allowed range.
    """
    minRefLev = -130 # dBm
    maxRefLev = 30 # dBm
    if minRefLev <= refLevel <= maxRefLev:
        err_check(rsa.CONFIG_SetReferenceLevel(c_double(refLevel)))
    else:
        raise SDR_Error(0,
            "Desired reference level not in range.",
            "Please choose a value between {} and {} dBm.".format(minRefLev,
                maxRefLev)
        )

def CONFIG_GetAutoAttenuationEnable():
    """
    Return the signal path auto-attenuation enable state.

    Note: This method is for RSA500A/600A series instruments only.

    This method returns the enable state value set by the last call to
    CONFIG_SetAutoAttenuationEnable(), regarless of whether it has been
    applied to the hardware yet.

    Returns
    -------
    bool
        True indicates auto-attenuation enabled, False for disabled.
    """
    enable = c_bool()
    err_check(rsa.CONFIG_GetAutoAttenuationEnable(byref(enable)))
    return enable.value

def CONFIG_SetAutoAttenuationEnable(enable):
    """
    Set the signal path auto-attenuation enable state.

    Note: This method is for RSA500A/600A series instruments only.

    When auto-attenuation operation is enabled, the RF input attenuator
    is automatically configured to an optimal value which accomodates
    input signal levels up to the reference level. Auto-attenuation
    operation bases the attenuator setting on the current reference
    level, center frequency, and RF preamplifier state. When the RF
    preamplifier is enabled, the RF attenuator setting is adjusted to
    account for the additional gain. Note that auto-attenuation state
    does not affect the RF preamplifier state.

    The device Run state must be re-applied to apply the new state
    value to the hardware. At device connect time, the auto-attenuation
    state is initialized to enabled (True).

    Parameters
    ----------
    enable : bool
        True enabled auto-attenuation operation. False disables it.
    """
    err_check(rsa.CONFIG_SetAutoAttenuationEnable(c_bool(enable)))

def CONFIG_GetRFPreampEnable():
    """
    Return the state of the RF preamplifier.

    Note: This method is for RSA500A/600A series instruments only.

    This method returns the RF preamplifier enable state value set by
    the last call to CONFIG_SetRFPreampEnable(), regardless of whether
    it has been applied to the hardware yet.

    Returns
    -------
    bool
        True indicates RF preamp is enabled, False indicates disabled.
    """
    enable = c_bool()
    err_check(rsa.CONFIG_GetRFPreampEnable(byref(c_bool)))

def CONFIG_SetRFPreampEnable(enable):
    """
    Set the RF preamplifier enable state.

    Note: This method is for RSA500A/600A series instruments only.

    This method provides direct control of the RF preamplifier. The
    preamplifier state is independent of the auto-attenuation state or
    RF attenuator setting.

    The preamplifier provides nominally 25 dB of gain when enabled,
    with gain varying over the device RF frequency range (refer to the
    device data sheet for detailed preamp response specifications).
    When the preamplifier is enabled, the device reference level
    setting should be –15 dBm or lower to avoid saturating internal
    signal path components.

    The device Run state must be re-applied to cause a new state value
    to be applied to the hardware.

    Parameters
    ----------
    enable : bool
        True enables the RF preamplifier. False disables it.

    Raises
    ------
    SDR_Error
        If the reference level is set above -15 dBm, which could cause
        saturation of internal signal path components.
    """
    if CONFIG_GetReferenceLevel() > -15:
        raise SDR_Error(0,
            "Reference level too high for preamp usage.",
            "Set the reference level <= -15 dBm to avoid saturation."
        )
    else:
        err_check(rsa.CONFIG_SetRFPreampEnable(c_bool(enable)))

def CONFIG_GetRFAttenuator():
    """
    Return the setting of the RF input attenuator.

    Note: This method is for RSA500A/600A series instruments only.

    If auto-attenuation is enabled, the returned value is the current
    RF attenuator hardware configuration. If auto-attenuation is
    disabled (manual attenuation mode), the returned value is the last
    value set by CONFIG_SetRFAttenuator(), regardless of whether it has
    been applied to the hardware.

    Returns
    -------
    float
        The RF input attenuator setting value in dB.
    """
    value = c_double()
    err_check(rsa.CONFIG_GetRFAttenuator(byref(value)))
    return value.value

def CONFIG_SetRFAttenuator(value):
    """
    Set the RF input attenuator value manually.

    Note: This method is for RSA500A/600A series instruments only.

    This method allows direct control of the RF input attenuator
    setting. The attenuator can be set in 1 dB steps, over the range
    -51 dB to 0 dB. Input values outside the range are converted to the
    closest allowed value. Input values with fractional parts are
    rounded to the nearest integer value, giving 1 dB steps.

    The device auto-attenuation state must be disabled for this control
    to have effect. Setting the attenuator value with this method does
    not change the auto-attenuation state. To change the auto-
    attenuation state, use the CONFIG_SetAutoAttenuationEnable() method.

    The device Run state must be re-applied to cause a new setting
    value to be applied to the hardware.

    Improper manual attenuator setting may cause signal path saturation
    resulting in degraded performance. This is particularly true if the
    RF preamplifier state is changed. When making significant changes
    to the attenuator or preamp settings, it is recommended to use
    auto-attenuation mode to set the initial RF attenuator level for a
    desired reference level, then query the attenuator setting to
    determine reasonable values for further manual control.

    Parameters
    ----------
    value : float or int
        Setting to configure the RF input attenuator, in dB units.
    """
    err_check(rsa.CONFIG_SetRFAttenuator(c_double(value)))

""" DEVICE METHODS """

def DEVICE_Connect(deviceID=0):
    """
    Connect to a device specified by the deviceID parameter.

    If a single device is attached, no parameter needs to be given. If
    multiple devices are attached, a deviceID value must be given to
    identify which device is the target for connection.

    The deviceID value can be found using the search() method.

    Parameters
    ----------
    deviceID : int
        The deviceID of the target device.
    """
    err_check(rsa.DEVICE_Connect(c_int(deviceID)))

def DEVICE_Disconnect():
    """Stop data acquisition and disconnect from connected device."""
    err_check(rsa.DEVICE_Disconnect())

def DEVICE_GetEnable():
    """
    Query the run state.

    The device only produces data results when in the run state, when
    signal samples flow from the device to the host API.

    Returns
    -------
    bool
       True indicates the device is in the run state. False indicates
       that it is in the stop state.
    """
    enable = c_bool()
    err_check(rsa.DEVICE_GetEnable(byref(enable)))
    return enable.value

# def DEVICE_GetErrorString():

def DEVICE_GetFPGAVersion():
    """
    Retrieve the FPGA version number.

    The FPGA version has the form "Vmajor.minor" - for example, "V3.4"
    indicates a major version of 3, and a minor version of 4. The
    maximum total string length supported is 6 characters.

    Returns
    -------
    string
        The FPGA version number, formatted as described above.
    """
    fpgaVersion = (c_char * FPGA_VERSION_STRLEN)()
    err_check(rsa.DEVICE_GetFPGAVersion(byref(fpgaVersion)))
    return fpgaVersion.value.decode('utf-8')

def DEVICE_GetFWVersion():
    """
    Retrieve the firmware version number.

    The firmware version number has the form: "Vmajor.minor". For
    example: "V3.4", for major version 3, minor version 4. The
    maximum total string length supported is 6 characters.

    Returns
    -------
    string
        The firmware version number, formatted as described above.
    """
    fwVersion = (c_char * FW_VERSION_STRLEN)()
    err_check(rsa.DEVICE_GetFWVersion(byref(fwVersion)))
    return fwVersion.value.decode('utf-8')

def DEVICE_GetHWVersion():
    """
    Retrieve the hardware version number.

    The firmware version number has the form: "VversionNumber". For
    example: "V3". The maximum string length supported is 4 characters.

    Returns
    -------
    string
        The hardware version number, formatted as described above.
    """
    hwVersion = (c_char * HW_VERSION_STRLEN)()
    err_check(rsa.DEVICE_GetHWVersion(byref(hwVersion)))
    return hwVersion.value.decode('utf-8')

def DEVICE_GetNomenclature():
    """
    Retrieve the name of the device.

    The nomenclature has the form "RSA306B", for example. The maximum
    string length supported is 8 characters.

    Returns
    -------
    string
        Name of the device.
    """
    nomenclature = (c_char * NOMENCLATURE_STRLEN)()
    err_check(rsa.DEVICE_GetNomenclature(byref(nomenclature)))
    return nomenclature.value.decode('utf-8')

# def DEVICE_GetNomenclatureW():

def DEVICE_GetSerialNumber():
    """
    Retrieve the serial number of the device.

    The serial number has the form "B012345", for example. The maximum
    string length supported is 8 characters.

    Returns
    -------
    string
        Serial number of the device.
    """
    serialNum = (c_char * MAX_SERIAL_STRLEN)()
    err_check(rsa.DEVICE_GetSerialNumber(byref(serialNum)))
    return serialNum.value.decode('utf-8')

def DEVICE_GetAPIVersion():
    """
    Retrieve the API version number.

    The API version number has the form: "major.minor.revision", for
    example: "3.4.0145", for major version 3, minor version 4, and
    revision 0145. The maximum string length supported is 8 characters.

    Returns
    -------
    string
        The API version number, formatted as described above.
    """
    apiVersion = (c_char * API_VERSION_STRLEN)()
    err_check(rsa.DEVICE_GetAPIVersion(byref(apiVersion)))
    return apiVersion.value.decode('utf-8')

def DEVICE_PrepareForRun():
    """
    Put the system in a known state, ready to stream data.

    This method does not actually initiate data transfer. During file
    playback mode, this is useful to allow other parts of your
    application to prepare to receive data before starting the
    transfer. See DEVICE_StartFrameTransfer(). This is in comparison to
    the DEVICE_Run() method, which immediately starts data streaming
    without waiting for a "go" signal.
    """
    err_check(rsa.DEVICE_PrepareForRun())

def DEVICE_GetInfo():
    """
    Retrieve multiple device and information strings.

    Obtained information includes: device nomenclature, serial number,
    firmware versionn, FPGA version, hardware version, and API version.

    Returns
    -------
    dict
        All of the above listed information, labeled.
    """
    nomenclature = DEVICE_GetNomenclature()
    serialNum = DEVICE_GetSerialNumber()
    fwVersion = DEVICE_GetFWVersion()
    fpgaVersion = DEVICE_GetFPGAVersion()
    hwVersion = DEVICE_GetHWVersion()
    apiVersion = DEVICE_GetAPIVersion()
    info = {
        "Nomenclature" : nomenclature,
        "Serial Number" : serialNum,
        "FW Version" : fwVersion,
        "FPGA Version" : fpgaVersion,
        "HW Version" : hwVersion,
        "API Version" : apiVersion
    }
    return info

def DEVICE_GetOverTemperatureStatus():
    """
    Query device for over-temperature status.

    This method allows clients to monitor the device's internal
    temperature status when operating in high-temperature environments.
    If the over-temperature condition is detected, the device should be
    powered down or moved to a lower temperature area.

    Returns
    -------
    bool
        Over-temperature status. True indicates device above nominal
        safe operating range, and may result in reduced accuracy and/
        or damage to the device. False indicates device temperature is
        within the safe operating range.
    """
    overTemp = c_bool()
    err_check(rsa.DEVICE_GetOverTemperatureStatus(byref(overTemp)))
    return overTemp.value

def DEVICE_Reset(deviceID=-1):
    """
    Reboot the specified device.

    If a single device is attached, no parameter needs to be given. If
    multiple devices are attached, a deviceID value must be given to
    identify which device to reboot.

    Parameters
    ----------
    deviceID : int
        The deviceID of the target device.

    Raises
    ------
    SDR_Error
        If multiple devices are found but no deviceID is specified.
    """
    DEVICE_Disconnect()
    foundDevices = DEVICE_Search()
    numFound = len(foundDevices)
    if numFound == 1:
        deviceID = 0
    elif numFound > 1 and deviceID == -1:
        raise SDR_Error(0,
            "Multiple devices found, but no ID specified.",
            "Please give a deviceID to specify which device to reboot."
        )
    err_check(rsa.DEVICE_Reset(c_int(deviceID)))   

def DEVICE_Run():
    """Start data acquisition."""
    err_check(rsa.DEVICE_Run()) 

def DEVICE_Search():
    """
    Search for connectable devices.

    Returns a dict with an entry containing the device ID number,
    serial number, and device type information for each device found.
    An example of this would be: {0 : ('B012345', 'RSA306B')}, when a 
    single RSA306B is found, with serial number 'B012345'.

    Valid deviceType strings are "RSA306", "RSA306B", "RSA503A",
    "RSA507A", "RSA603A", and "RSA607A".

    Returns
    -------
    dict
        Found devices: {deviceID : (deviceSerial, deviceType)}.
            deviceID : int
            deviceSerial : string
            deviceType : string

    Raises
    ------
    SDR_Error
        If no devices are found.
    """
    numFound = c_int()
    devIDs = (c_int * MAX_NUM_DEVICES)()
    devSerial = ((c_char * MAX_NUM_DEVICES) * MAX_SERIAL_STRLEN)()
    devType = ((c_char * MAX_NUM_DEVICES) * MAX_DEVTYPE_STRLEN)()

    err_check(rsa.DEVICE_Search(byref(numFound), byref(devIDs),devSerial,
        devType))

    foundDevices = {
        ID : (devSerial[ID].value.decode(), devType[ID].value.decode()) \
        for ID in devIDs
    }

    # If there are no devices, there is still a dict returned
    # with a device ID, but the other elements are empty.
    if foundDevices[0] == ('',''):
        raise SDR_Error(0,
            "Could not find a matching Tektronix RSA device.",
            "Please check the connection and try again."
        )
    else:
        return foundDevices

def DEVICE_StartFrameTransfer():
    """
    Start data transfer.

    This is typically used as the trigger to start data streaming after
    a call to DEVICE_PrepareForRun(). If the system is in the stopped
    state, this call places it back into the run state with no changes
    to any internal data or settings, and data streaming will begin
    assuming there are no errors.
    """
    err_check(rsa.DEVICE_StartFrameTransfer())

def DEVICE_Stop():
    """
    Stop data acquisition.

    This method must be called when changes are made to values that
    affect the signal.
    """
    err_check(rsa.DEVICE_Stop())

def DEVICE_GetEventStatus(eventID):
    """
    Return global device real-time event status.

    The device should be in the Run state when this method is called.
    Event information is only updated in the Run state, not in the Stop
    state.

    Overrange event detection requires no additional configuration to
    activate. The event indicates that the ADC input signal exceeded
    the allowable range, and signal clipping has likely occurred. The
    reported timestamp value is the most recent USB transfer frame in
    which a signal overrange was detected.

    Trigger event detection requires the appropriate HW trigger
    settings to be configured. These include trigger mode, source,
    transition, and IF power level (if IF power trigger is selected).
    The event indicates that the trigger condition has occurred. The
    reported timestamp value is of the most recent sample instant when
    a trigger event was detected. The forceTrigger() method can be used
    to simulate a trigger event.

    1PPS event detection (RSA500AA/600A only) requires the GNSS receiver
    to be enabled and have navigation lock. The even indicates that the
    1PPS event has occurred. The reported timestamp value is of the
    most recent sample instant when the GNSS Rx 1PPS pulse rising edge
    was detected.

    Querying an event causes the information for that event to be
    cleared after its state is returned. Subsequent queries will
    report "no event" until a new one occurs. All events are cleared
    when the device state transitions from Stop to Run.

    Parameters
    ----------
    eventID : string
        Identifier for the event status to query. Valid settings:
            OVERRANGE : Overrange event detection.
            TRIGGER : Trigger event detection.
            1PPS : 1PPS event detection (RSA500AA/600A only).

    Returns
    -------
    occurred : bool
        Indicates whether the event has occurred.
    timestamp : int
        Event occurrence timestamp. Only valid if occurred is True.

    Raises
    ------
    SDR_Error
        If the input string does not match one of the valid settings.
    """
    occurred  = c_bool()
    timestamp = c_uint64()
    if eventID in DEVEVENT:
        value = c_int(DEVEVENT.index(eventID))
    else:
        raise SDR_Error(0,
            "Input string does not match one of the valid settings.",
            "Please input one of: OVERRANGE, TRIGGER, or 1PPS."
        )
    err_check(rsa.DEVICE_GetEventStatus(value, byref(occurred),
        byref(timestamp)))
    return occurred.value, timestamp.value

""" DPX METHODS """

# Not yet implemented

""" GNSS METHODS """

def GNSS_ClearNavMessageData():
    """
    Clear the navigation message data queue.

    Note: This method is for RSA500A/600A series instruments only.

    The data queue which holds GNSS navigation message character
    strings is emptied by this method.
    """
    err_check(rsa.GNSS_ClearNavMessageData())

def GNSS_Get1PPSTimestamp():
    """
    Return the timestamp of the most recent internal 1PPS timing pulse.

    Note: This method is for RSA500A/600A series instruments only.

    The internal GNSS receiver must be enabled and have navigation lock
    for this method to return the internal timestamp of the 1PPS pulse.
    1PPS pulses occur each second, so the user application should call
    this method at least once per second to retrieve the 1PPS
    information correctly.

    The 1PPS timestamp along with the decoded UTC time from the
    navigation messages can be used to set the API system time to GNSS-
    accurate time reference. See REFTIME_SetReferenceTime() for more
    information on setting reference time based on these values.

    Returns
    -------
    int
        Timestamp of the most recent 1PPS pulse.

    Raises
    ------
    SDR_Error
        If GNSS receiver is disabled, doesn't have navigation lock, or
        no internal 1PPS pulse is detected.
    """
    if GNSS_GetEnable() and GNSS_GetStatusRxLock:
        isValid = c_bool()
        timestamp1PPS = c_uint64()
        err_check(rsa.GNSS_Get1PPSTimestamp(byref(isValid),
            byref(timestamp1PPS)))
        if isValid.value:
            return timestamp1PPS.value
        else:
            raise SDR_Error(0, "Failed to get 1PPS timestamp.",
                "No internal 1PPS pulse detected. ")
    else:
        raise SDR_Error(0, "Failed to query 1PPS timestamp.",
            "Internal GNSS receiver must be enabled and have navigation lock.")

def GNSS_GetAntennaPower():
    """
    Return the GNSS antenna power output state.

    Note: This method is for RSA500A/600A series instruments only.

    Returned value indicates the state set by GNSS_SetAntennaPower(),
    although the actual output state may be different. See the entry
    for GNSS_SetAntennaPower() for more information on GNSS antenna
    power control.

    Returns
    -------
    bool
        True for GNSS antenna power output enabled, False for disabled.
    """
    powered = c_bool()
    err_check(rsa.GNSS_GetAntennaPower(byref(powered)))
    return powered.value

def GNSS_GetEnable():
    """
    Return the internal GNSS receiver enable state.

    Note: This method is for RSA500A/600A series instruments only.

    Returns
    -------
    bool
        True indicates GNSS receiver is enabled, False for disabled.
    """
    enable = c_bool()
    err_check(rsa.GNSS_GetEnable(byref(enable)))
    return enable.value

def GNSS_GetHwInstalled():
    """
    Return whether internal GNSS receiver hardware is installed.

    GNSS hardware is only installed in RSA500AA and RSA600A devices.
    All other devices will indicate no hardware installed.

    Returns
    -------
    bool
        True indicates GNSS receiver HW installed, False otherwise.
    """
    installed = c_bool()
    err_check(rsa.GNSS_GetHwInstalled(byref(installed)))
    return installed.value

def GNSS_GetNavMessageData():
    """
    Return navigation message data.

    Note: This method is for RSA500A/600A Series instruments only.

    The internal GNSS receiver must be enabled for this method to
    return useful data, otherwise it will always return msgLen = 0,
    indicating no data. The message output consists of contiguous
    segments of the ASCII character serial stream from the GNSS
    receiver, following the NMEA 0183 Version 3.0 standard. The
    character output rate is approximately 1000 character per second,
    originating from an internal 9600 baud serial interface.

    The GNSS navigation message output includes RMC, GGA, GSA, GSV, and
    other NMEA sentence types. The two character Talker Identifier
    following the starting "$" character may be "GP", "GL", "BD", or
    "GN" depending on the configuration of the receiver. The method
    does not decode the NMEA sentences. It passes them through in raw
    form, including all characters in the original serial stream.

    The message queue holding the message chars may overflow if this
    method is not called often enough to keep up with the data
    generation by the GNSS receiver. It is recommended to retrieve
    message data at least 4 times per second to avoid this overflow.

    Returns
    -------
    msgLen : int
        Number of characters in the message buffer. Can be zero.
    message : string
        Navigation message.
    """
    msgLen = c_int()
    message = c_char_p()
    err_check(rsa.GNSS_GetNavMessageData(byref(msgLen), byref(message)))
    return msgLen.value, message.value

def GNSS_GetSatSystem():
    """
    Return the GNSS satellite system selection.

    Note: This method is for RSA500A/600A series instruments only.

    This method should only be called when the GNSS receiver is
    enabled.

    Returns
    -------
    string
        The GNSS satellite system selection. Valid results:
            GPS_GLONASS : GPS + Glonass systems used.
            GPS_BEIDOU : GPS + Beidou systems used.
            GPS : Only GPS system used.
            GLONASS : Only Glonass system used.
            BEIDOU : Only Beidou system used.
    """
    satSystem = c_int()
    err_check(rsa.GNSS_GetSatSystem(byref(satSystem)))
    return GNSS_SATSYS[satSystem.value - 1]

def GNSS_GetStatusRxLock():
    """
    Return the GNSS receiver navigation lock status.

    Note: This method is for RSA500A/600A series instruments only.

    The lock status changes only once per second at most. GNSS-derived
    time reference and frequency reference alignments are only applied
    with the GNSS receiver is locked.

    Returns
    -------
    bool
        True for enabled and locked, False for disabled or not locked.
    """
    locked = c_bool()
    err_check(rsa.GNSS_GetStatusRxLock(byref(locked)))
    return locked.value

def GNSS_SetAntennaPower(powered):
    """
    Set the GNSS antenna power output state.

    Note: This method is for RSA500A/600A series instruments only.

    The GNSS receiver must be enabled for antenna power to be output.
    If the receiver is disabled, the antenna power output is also
    disabled, even when set to the enabled state by this method. When
    antenna power is enabled, 3.0 V DC is switched to the antenna
    center conductor  line for powering  an external antenna. When
    disabled, the voltage source is disconnected from the antenna.

    Parameters:
    -----------
    powered : bool
        True to enable antenna power output, False to disable it.
    """
    err_check(rsa.GNSS_SetAntennaPower(c_bool(powered)))

def GNSS_SetEnable(enable):
    """
    Enable or disable the internal GNSS receiver operation.

    Note: This method is for RSA500A/600A series instruments only.

    If the GNSS receiver functions are not needed, it should be
    disabled to conserve battery power.

    Parameters
    ----------
    enable : bool
        True enabled the GNSS receiver. False disables it.
    """
    err_check(rsa.GNSS_SetEnable(c_bool(enable)))

def GNSS_SetSatSystem(satSystem):
    """
    Set the GNSS satellite system selection.

    Note: This method is for RSA500A/600A series instruments only.

    The satellite system selection limits the GNSS receiver to using
    only signals from the specified system(s). Only the choices listed
    below are valid; entering multiple strings to get combinations not
    listed will not work.

    Each time the GNSS receiver is enabled, the satellite system
    selection is set to the default value of GPS_GLONASS. Satellite
    system selections are not persistent or recallable, even within the
    same connection session. Any non-default setting must be explicitly
    applied after each receiver enable operation.

    The setting can only be changed when the GNSS receiver is enabled.
    If the method is called when the receiver is disabled, the
    selection is ignored and an error is returned.

    If the selected system(s) do not provide sufficient signal coverage
    at the antenna location, the GNSS receiver will not be able to
    acquire navigation lock. In most cases, the default selection
    provides the best coverage.

    Parameters
    ----------
    satSystem : string
        The GNSS satellite system selection. Valid settings:
            GPS_GLONASS : GPS + Glonass systems used.
            GPS_BEIDOU : GPS + Beidou systems used.
            GPS : Only GPS system used.
            GLONASS : Only Glonass system used.
            BEIDOU : Only Beidou system used.

    Raises
    ------
    SDR_Error
        If the input string does not match one of the valid settings.
    """
    if satSystem in GNSS_SATSYS:
        value = GNSS_SATSYS.index(satSystem) + 1
        err_check(rsa.GNSS_SetSatSystem(c_int(value)))
    else:
        raise SDR_Error(0,
            "Input string does not match one of the valid settings.",
            "Select from: GPS_GLONASS, GPS_BEIDOU, GPS, GLONASS, or BEIDOU.")

""" IF STREAMING METHODS """

# Not yet implemented

""" IQ BLOCK METHODS """

def IQBLK_GetIQAcqInfo():
    """
    Return IQ acquisition status info for the most recent IQ block.

    IQBLK_GetIQAcqInfo() may be called after an IQ block record is
    retrieved with IQBLK_GetIQData(), IQBLK_GetIQDataInterleaved(), or
    IQBLK_GetIQDataComplex(). The returned information applies to the
    IQ record returned by the "GetData" methods.

    The acquisition status bits returned by this method are:
        Bit 0 : INPUT_OVERRANGE
            ADC input overrange during acquisition.
        Bit 1 : FREQREF_UNLOCKED
            Frequency reference unlocked during acquisition.
        Bit 2 : ACQ_SYS_ERROR
            Internal oscillator unlocked or power failure during
            acquisition.
        Bit 3 : DATA_XFER_ERROR
            USB frame transfer error detected during acquisition.

    A status bit value of 1 indicates that event occurred during the
    signal acquisition. A value of 0 indicates no occurrence.

    Returns
    -------
    sample0Timestamp : int
        Timestamp of the first sample of the IQ block record.
    triggerSampleIndex : int
        Index to the sample corresponding to the trigger point.
    triggerTimestamp : int
        Timestamp of the trigger sample.
    acqStatus : int
        "Word" with acquisition status bits. See above for details.
    """
    acqInfo = IQBLK_ACQINFO()
    err_check(rsa.IQBLK_GetIQAcqInfo(byref(acqInfo)))
    return (acqInfo.sample0Timestamp.value, acqInfo.triggerSampleIndex.value,
        acqInfo.triggerTimestamp.value, acqInfo.acqStatus.value)

def IQBLK_AcquireIQData():
    """
    Initiate an IQ block record acquisition.

    Calling this method initiates an IQ block record data acquisition.
    This method places the device in the Run state if it is not
    already in that state.

    Before calling this method, all device acquisition parameters must
    be set to valid states. These include Center Frequency, Reference
    Level, any desired Trigger conditions, and the IQBLK Bandwidth and
    Record Length settings.
    """
    err_check(rsa.IQBLK_AcquireIQData())

def IQBLK_GetIQBandwidth():
    """
    Query the IQ bandwidth value.

    Returns
    -------
    float
        The IQ bandwidth value.
    """
    iqBandwidth = c_double()
    err_check(rsa.IQBLK_GetIQBandwidth(byref(iqBandwidth)))
    return iqBandwidth.value

# def IQBLK_GetIQData():

# def IQBLK_GetIQDataCplx():

def IQBLK_GetIQDataDeinterleaved(reqLength):
    """
    Retrieve an IQ block data record in separate I and Q array format.

    When complete, the iData array is filled with I-data and the qData
    array is filled with Q-data. The Q-data is not imaginary.

    For example, with reqLength = N:
        iData: [I_0, I_1, ..., I_N]
        qData: [Q_0, Q_1, ..., Q_N]
        Actual IQ Data: [I_0 + i*Q_0, I_1 + i*Q_1, ..., I_N + i*Q_N]

    Parameters
    ----------
    reqLength : int
        Number of IQ samples requested to be returned in data arrays.
        The maximum value of reqLength is equal to the recordLength
        value set in IQBLK_SetIQRecordLength(). Smaller values of
        reqLength allow retrieving partial IQ records.

    Returns
    -------
    iData : Numpy array
        Array of I-data.
    qData : Numpy array
        Array of Q-data.
    outLength : int
        Actual number of I and Q sample values returned in data arrays.
    """
    iData = (c_float * reqLength)()
    qData = (c_float * reqLength)()
    outLength = c_int()
    err_check(rsa.IQBLK_GetIQDataDeinterleaved(byref(iData), byref(qData), 
        byref(outLength), c_int(reqLength)))
    return np.array(iData), np.array(qData), outLength.value

def IQBLK_GetIQRecordLength():
    """
    Query the IQ record length.

    The IQ record length is the number of IQ data samples to be
    generated with each acquisition.

    Returns
    -------
    int
        Number of IQ data samples to be generated with each acquisition.
        Range: 2 to 104.8576 M samples.
    """
    recordLength = c_int()
    err_check(rsa.IQBLK_GetIQRecordLength(byref(recordLength)))
    return recordLength.value

def IQBLK_GetIQSampleRate():
    """
    Query the IQ sample rate value.

    The IQ sample rate value depends on the IQ bandwidth value. Set the
    IQ bandwidth value before querying the sample rate.

    Returns
    -------
    float
        The IQ sampling frequency, in samples/second.
    """
    iqSampleRate = c_double()
    err_check(rsa.IQBLK_GetIQSampleRate(byref(iqSampleRate)))
    return iqSampleRate.value

def IQBLK_GetMaxIQBandwidth():
    """
    Query the maximum IQ bandwidth of the connected device.

    Returns
    -------
    float
        The maximum IQ bandwidth, measured in Hz.
    """
    maxBandwidth = c_double()
    err_check(rsa.IQBLK_GetMaxIQBandwidth(byref(maxBandwidth)))
    return maxBandwidth.value

def IQBLK_GetMaxIQRecordLength():
    """
    Query the maximum IQ record length.

    The maximum IQ record length is the maximum number of samples which
    can be generated in one IQ block record. The maximum IQ record
    length varies as a function of the IQ bandwidth - set the bandwidth
    before querying the maximum record length. You should not request
    more than the maximum number of IQ samples when setting the record
    length. The maximum record length is the maximum number of IQ sample
    pairs that can be generated at the requested IQ bandwidth and
    corresponding IQ sample rate from 2 seconds of acquired signal data.

    Returns
    -------
    int
        The maximum IQ record length, measured in samples.
    """
    maxIqRecLen = c_int()
    err_check(rsa.IQBLK_GetMaxIQRecordLength(byref(maxIqRecLen)))
    return maxIqRecLen.value

def IQBLK_GetMinIQBandwidth():
    """
    Query the minimum IQ bandwidth of the connected device.

    Returns
    -------
    float
        The minimum IQ bandwidth, measured in Hz.
    """
    minBandwidth = c_double()
    err_check(rsa.IQBLK_GetMinIQBandwidth(byref(minBandwidth)))
    return minBandwidth.value

def IQBLK_SetIQBandwidth(iqBandwidth):
    """
    Set the IQ bandwidth value.

    The IQ bandwidth must be set before acquiring data. The input value
    must be within a valid range, and the IQ sample rate is determined
    by the IQ bandwidth.

    Parameters
    ----------
    iqBandwidth : float or int
        IQ bandwidth value measured in Hz

    Raises
    ------
    SDR_Error
        If the desired IQ bandwidth is not in the allowed range.
    """
    if IQBLK_GetMinIQBandwidth() <= iqBandwidth <= IQBLK_GetMaxIQBandwidth():
        err_check(rsa.IQBLK_SetIQBandwidth(c_double(iqBandwidth)))
    else:
        raise SDR_Error(0,
            "Desired bandwidth not in allowed range.",
            "Please choose a value between {} and {} Hz.".format(
                minBandwidth, maxBandwidth)
        )

def IQBLK_SetIQRecordLength(recordLength):
    """
    Set the number of IQ samples generated by each IQ block acquisition.

    A check is performed to ensure that the desired value is within the
    allowed range. For best results in FFT analysis, choose a multiple
    of 2. The maximum allowed value is determined by the IQ bandwidth;
    set that first.

    Parameters
    ----------
    recordLength : int
        IQ record length, measured in samples. Minimum value of 2.

    Raises
    ------
    SDR_Error
        If the desired IQ record length is not in the allowed range.
    """
    if 2 <= recordLength <= IQBLK_GetMaxIQRecordLength():
        err_check(rsa.IQBLK_SetIQRecordLength(c_int(recordLength)))
    else:
        raise SDR_Error(0,
            "Desired record length not in allowed range.",
            "Please choose a value between {} and {} samples.".format(
                minIqRecLen, maxIqRecLen)
        )

def IQBLK_WaitForIQDataReady(timeoutMsec):
    """
    Wait for the data to be ready to be queried.

    Parameters
    ----------
    timeoutMsec : int
        Timeout value measured in ms.

    Returns
    -------
    bool
        True indicates data is ready for acquisition. False indicates
        the data is not ready and the timeout value is exceeded.
    """
    ready = c_bool()
    err_check(rsa.IQBLK_WaitForIQDataReady(c_int(timeoutMsec), byref(ready)))
    return ready.value

""" IQ STREAM METHODS """

def IQSTREAM_GetMaxAcqBandwidth():
    """
    Query the maximum IQ bandwidth for IQ streaming.

    The IQ streaming bandwidth should be set to a value no larger than
    the value returned by this method.

    Returns
    -------
    float
        The maximum IQ bandwidth supported by IQ streaming, in Hz.
    """
    maxBandwidthHz = c_double()
    err_check(rsa.IQSTREAM_GetMaxAcqBandwidth(byref(maxBandwidthHz)))
    return maxBandwidthHz.value

def IQSTREAM_GetMinAcqBandwidth():
    """
    Query the minimum IQ bandwidth for IQ streaming.

    The IQ streaming bandwidth should be set to a value no smaller than
    the value returned by this method.

    Returns
    -------
    float
        The minimum IQ bandwidth supported by IQ streaming, in Hz.
    """
    minBandwidthHz = c_double()
    err_check(rsa.IQSTREAM_GetMinAcqBandwidth(byref(minBandwidthHz)))
    return minBandwidthHz.value

def IQSTREAM_ClearAcqStatus():
    """
    Reset the "sticky" status bits of the acqStatus info element during
    an IQ streaming run interval.

    This is effective for both client and file destination runs.
    """
    err_check(rsa.IQSTREAM_ClearAcqStatus())

def IQSTREAM_GetAcqParameters():
    """
    Retrieve the processing parameters of IQ streaming output bandwidth
    and sample rate, resulting from the user's requested bandwidth.

    Call this method after calling IQSTREAM_SetAcqBandwidth() to set
    the requested bandwidth. See IQSTREAM_SetAcqBandwidth() docstring
    for details of how requested bandwidth is used to select output
    bandwidth and sample rate settings.

    Returns
    -------
    float: bwHz_act
        Actual acquisition bandwidth of IQ streaming output data in Hz.
    float: srSps
        Actual sample rate of IQ streaming output data in Samples/sec.
    """
    bwHz_act = c_double()
    srSps = c_double()
    err_check(rsa.IQSTREAM_GetAcqParameters(byref(bwHz_act), byref(srSps)))
    return bwHz_act.value, srSps.value

def IQSTREAM_GetDiskFileInfo():
    """
    Retrieve information about the previous file output operation.

    This information is intended to be queried after the file output
    operation has completed. It can be queried during file writing as
    an ongoing status, but some of the results may not be valid at that
    time.

    Note: This method does not return the filenames parameter as shown
    in the official API documentation.

    IQSTREAM_ClearAcqStatus() can be called to clear the "sticky" bits
    during the run if it is desired to reset them.

    Note: If acqStatus indicators show "Output buffer overflow", it is
    likely that the disk is too slow to keep up with writing the data
    generated by IQ stream processing. Use a faster disk (SSD is
    recommended), or a smaller acquisition bandwidth which generates
    data at a lower rate.

    Returns
    -------
    numberSamples : int
        Number of IQ sample pairs written to the file.
    sample0Timestamp : int
        Timestamp of the first sample written to file.
    triggerSampleIndex : int
        Sample index where the trigger event occurred. This is only
        valid if triggering has been enabled. Set to 0 otherwise.
    triggerTimestamp : int
        Timestamp of the trigger event. This is only valid if
        triggering has been enabled. Set to 0 otherwise.
    filenames : strings
    acqStatus : int
        Acquisition status flags for the run interval. Individual bits
        are used as indicators as follows:
            Individual Internal Write Block Status (Bits 0-15, starting
            from LSB):
                Bits 0-15 indicate status for each internal write block,
                    so may not be very useful. Bits 16-31 indicate the
                    entire run status up to the time of query.
                Bit 0 : 1 = Input overrange.
                Bit 1 : 1 = USB data stream discontinuity.
                Bit 2 : 1 = Input buffer > 75% full (IQStream
                    processing heavily loaded).
                Bit 3 : 1 = Input buffer overflow (IQStream processing
                    overloaded, data loss has occurred).
                Bit 4 : 1 = Output buffer > 75% full (File output
                    falling behind writing data).
                Bit 5 : 1 = Output buffer overflow (File output too
                    slow, data loss has occurred).
                Bit 6 - Bit 15 : Unused, always 0.
            Entire Run Summary Status ("Sticky Bits"):
                The bits in this range are essentially the same as Bits
                    0-15, except once they are set (to 1) they remain
                    set for the entire run interval. They can be used to
                    determine if any of the status events occurred at
                    any time during the run.
                Bit 16 : 1 = Input overrange.
                Bit 17 : 1 = USB data stream discontinuity.
                Bit 18 : 1 = Input buffer > 75% full (IQStream
                    processing heavily loaded).
                Bit 19 : 1 = Input buffer overflow (IQStream processing
                    overloaded, data loss has occurred).
                Bit 20 : 1 = Output buffer > 75% full (File output
                    falling behind writing data).
                Bit 21 : 1 = Output buffer overflow (File output too
                    slow, data loss has occurred).
                Bit 22 - Bit 31 : Unused, always 0.
    """
    fileinfo = IQSTREAM_File_Info()
    err_check(rsa.IQSTREAM_GetDiskFileInfo(byref(fileinfo)))
    return (fileinfo.numberSamples, fileinfo.sample0Timestamp,
        fileinfo.triggerSampleIndex, fileinfo.triggerTimestamp,
        fileinfo.filenames, fileinfo.acqStatus)
        
def IQSTREAM_GetDiskFileWriteStatus():
    """
    Allow monitoring the progress of file output.

    The returned values indicate when the file output has started and
    completed. These become valid after IQSTREAM_Start() is called,
    with any file output destination selected.

    For untriggered configuration, isComplete is all that needs to be
    monitored. When it switches from false -> true, file output has
    completed. Note that if "infinite" file length is selected, then
    isComplete only changes to true when the run is stopped by running
    IQSTREAM_Stop().

    If triggering is used, isWriting can be used to determine when a
    trigger has been received. The client application can monitor this
    value, and if a maximum wait period has elapsed while it is still
    false, the output operation can be aborted. isWriting behaves the
    same for both finite and infinite file length settings.

    The [isComplete, isWriting] sequence is as follows (assumes a finite
    file length setting):
        Untriggered operation:
            IQSTREAM_Start()
                => File output in progress: [False, True]
                => File output complete: [True, True]
        Triggered operation:
            IQSTREAM_Start()
                => Waiting for trigger, file writing not started:
                    [False, False]
                => Trigger event detected, file writing in progress:
                    [False, True]
                => File output complete: [True, True]

    Returns
    -------
    bool: isComplete
        Whether the IQ stream file output writing is complete.
    bool: isWriting
        Whether the IQ stream processing has started writing to file.
    """
    isComplete = c_bool()
    isWriting = c_bool()
    err_check(rsa.IQSTREAM_GetDiskFileWriteStatus(byref(isComplete),
        byref(isWriting)))
    return isComplete.value, isWriting.value

def IQSTREAM_GetEnable():
    """
    Retrieve the current IQ stream processing state.

    Returns
    -------
    bool
        The current IQ stream processing enable status. True if active,
        False if inactive.
    """
    enabled = c_bool()
    err_check(rsa.IQSTREAM_GetEnable(byref(enabled)))
    return enabled.value

# def IQSTREAM_GetIQData():

# def IQSTREAM_GetIQDataBufferSize():

def IQSTREAM_SetAcqBandwidth(bwHz_req):
    """
    Request the acquisition bandwidth of the output IQ stream samples.

    The requested bandwidth should only be changed when the instrument
    is in the global stopped state. The new BW setting does not take
    effect until the global system state is cycled from stopped to
    running.

    The range of requested bandwidth values can be queried using
    IQSTREAM_GetMaxAcqBandwidth() and IQSTREAM_GetMinAcqBandwidth().

    The following table shows the mapping of requested bandwidth to
    output sample rate for all allowed bandwidth settings.

    Requested BW                      Output Sample Rate
    ----------------------------------------------------
    20.0 MHz < BW <= 40.0 MHz         56.000 MSa/s
    10.0 MHz < BW <= 20.0 MHz         28.000 MSa/s
    5.0 MHz < BW <= 10.0 MHz          14.000 MSa/s
    2.50 MHz < BW <= 5.0 MHz          7.000 MSa/s
    1.25 MHz < BW <= 2.50 MHz         3.500 MSa/s
    625.0 kHz < BW <= 1.25 MHz        1.750 MSa/s
    312.50 kHz < BW <= 625.0 kHz      875.000 kSa/s
    156.250 kHz < BW <= 312.50 kHz    437.500 kSa/s
    78125.0 Hz < BW <= 156.250 kHz    218.750 kSa/s
    39062.5 Hz < BW <= 78125.0 Hz     109.375 kSa/s
    19531.25 Hz < BW <= 39062.5 Hz    54687.5 Sa/s
    9765.625 Hz < BW <= 19531.25 Hz   24373.75 Sa/s
    BW <= 9765.625 Hz                 13671.875 Sa/s

    Parameters
    ----------
    bwHz_req : float
        Requested acquisition bandwidth of IQ streaming data, in Hz.

    Raises
    ------
    SDR_Error
        If the requested acq. bandwidth is not in the allowed range.
    """
    minAcBW = IQSTREAM_GetMinAcqBandwidth()
    maxAcBW = IQSTREAM_GetMaxAcqBandwidth()
    if minAcBW <= bwHz_req <= maxAcBW:
        err_check(rsa.IQSTREAM_SetAcqBandwidth(c_double(bwHz_req)))
        newCF = CONFIG_GetCenterFreq()
        return newCF
    else:
        raise SDR_Error(0,
            "Requested bandwidth not in range.",
            "Please choose a value between {} and {} Hz.".format(minAcBW,
                maxAcBW)
        )

def IQSTREAM_SetDiskFileLength(msec):
    """
    Set the time length of IQ data written to an output file.

    See IQSTREAM_GetDiskFileWriteStatus to find out how to monitor file
    output status to determine when it is active and completed.

    Msec Value    File Store Behavior
    ----------------------------------------------------------------
    0             No time limit on file output. File storage is
                  terminated when IQSTREAM_Stop() is called.
    > 0           File output ends after this number of milliseconds
                  of samples stored. File storage can be terminated
                  early by calling IQSTREAM_Stop().

    Parameters
    ----------
    msec : int
        Length of time in milliseconds to record IQ samples to file.

    Raises
    ------
    SDR_Error
        If input is a negative value.
    """
    if msec >= 0:
        err_check(rsa.IQSTREAM_SetDiskFileLength(c_int(msec)))
    else:
        raise SDR_Error(0,
            "Cannot set file length to a negative time value.",
            "Please input an integer greater than or equal to zero."
        )

def IQSTREAM_SetDiskFilenameBase(filenameBase):
    """
    Set the base filename for file output.

    Input can include the drive/path, as well as the common base
    filename portion of the file. It should not include a file
    extension, as the file writing operation will automatically append
    the appropriate one for the selected file format.

    The complete output filename has the format:
    <filenameBase><suffix><.ext>, where <filenameBase is set by this
    method, <suffix> is set by IQSTREAM_SetDiskFilenameSuffix(), and
    <.ext> is set by IQSTREAM_SetOutputConfiguration(). If separate data
    and header files are generated, the same path/filename is used for
    both, with different extensions to indicate the contents.

    Parameters
    ----------
    filenameBase : string
        Base filename for file output.
    """
    err_check(rsa.IQSTREAM_SetDiskFilenameBaseW(c_wchar_p(filenameBase)))

# def IQSTREAM_SetDiskFilenameBaseW(filenameBaseW):

def IQSTREAM_SetDiskFilenameSuffix(suffixCtl):
    """
    Set the control that determines the appended filename suffix.

    suffixCtl Value    Suffix Generated
    -------------------------------------------------------------------
    -2                 None. Base filename is used without suffix. Note
                       that the output filename will not change automa-
                       tically from one run to the next, so each output
                       file will overwrite the previous one unless the
                       filename is explicitly changed by calling the
                       Set method again.
    -1                 String formed from file creation time. Format:
                       "-YYYY.MM.DD.hh.mm.ss.msec". Note this time is
                       not directly linked to the data timestamps, so
                       it should not be used as a high-accuracy time-
                       stamp of the file data!
    >= 0               5 digit auto-incrementing index, initial value =
                       suffixCtl. Format: "-nnnnn". Note index auto-
                       increments by 1 each time IQSTREAM_Start() is
                       invoked with file data destination setting.

    Parameters
    ----------
    suffixCtl : int
        The filename suffix control value.

    Raises
    ------
    SDR_Error
        If the input value is less than -2.
    """
    if suffixCtl >= -2:
        err_check(rsa.IQSTREAM_SetDiskFilenameSuffix(c_int(suffixCtl)))
    else:
        raise SDR_Error(0,
            "Desired suffix control value is invalid.",
            "Please input an integer >= -2. Refer to documentation"
            + " for more information."
        )

# def IQSTREAM_SetIQDataBufferSize(reqSize):

def IQSTREAM_SetOutputConfiguration(dest, dtype):
    """
    Set the output data destination and IQ data type.

    The destination can be the client application, or files of different
    formats. The IQ data type can be chosen independently of the file
    format. IQ data values are stored in interleaved I/Q/I/Q order
    regardless of the destination or data type.

    Note: TIQ format files only allow INT32 or INT16 data types.

    Note: Midas 2.0 format files (.cdif, .det extensions) are not
    implemented.

    Parameters
    ----------
    dest : string
        Destination (sink) for IQ sample output. Valid settings:
            CLIENT : Client application
            FILE_TIQ : TIQ format file (.tiq extension)
            FILE_SIQ : SIQ format file with header and data combined in
                one file (.siq extension)
            FILE_SIQ_SPLIT : SIQ format with header and data in separate
                files (.siqh and .siqd extensions)
    dtype : string
        Output IQ data type. Valid settings:
            SINGLE : 32-bit single precision floating point (not valid
                with TIQ file destination)
            INT32 : 32-bit integer
            INT16 : 16-bit integer
            SINGLE_SCALE_INT32 : 32-bit single precision float, with
                data scaled the same as INT32 data type (not valid with
                TIQ file destination)

    Raises
    ------
    SDR_Error
        If inputs are not valid settings, or if single data type is 
        selected along with TIQ file format.
    """
    if dest in IQSOUTDEST:
        if dtype in IQSOUTDTYPE:
            if dest == "FILE_TIQ" and "SINGLE" in dtype:
                raise SDR_Error(0,
                    "Invalid selection of TIQ file and Single data type"
                    + "together",
                    "TIQ format files allow only INT32 or INT16 data types."
                )
            else:
                val1 = c_int(IQSOUTDEST.index(dest))
                val2 = c_int(IQSOUTDTYPE.index(dtype))
                err_check(rsa.IQSTREAM_SetOutputConfiguration(val1, val2))
        else:
            raise SDR_Error(0,
                "Input data type string does not match a valid setting.",
                "Please input one of: SINGLE, INT32, INT16, or " 
                + "SINGLE_SCALE_INT32."
            )
    else:
        raise SDR_Error(0,
            "Input destination string does not match a valid setting.",
            "Please input one of: CLIENT, FILE_TIQ, FILE_SIQ, or "
            + "FILE_SIQ_SPLIT."
        )

def IQSTREAM_Start():
    """
    Initialize IQ stream processing and initiate data output.

    If the data destination is file, the output file is created, and if
    triggering is not enabled, data starts to be written to the file
    immediately. If triggering is enabled, data will not start to be
    written to the file until a trigger event is detected.
    TRIG_ForceTrigger() can be used to generate a trigger even if the
    specified one does not occur.

    If the data destination is the client application, data will become
    available soon after this method is called. Even if triggering is
    enabled, the data will begin flowing to the client without need for
    a trigger event. The client must begin retrieving data as soon
    after IQSTREAM_Start() as possible.
    """
    err_check(rsa.IQSTREAM_Start())

def IQSTREAM_Stop():
    """
    Terminate IQ stream processing and disable data output.

    If the data destination is file, file writing is stopped and the
    output file is closed.
    """
    err_check(rsa.IQSTREAM_Stop())

def IQSTREAM_WaitForIQDataReady(timeoutMsec):
    """
    Block while waiting for IQ Stream data output.

    This method blocks while waiting for the IQ Streaming processing to
    produce the next block of IQ data. If data becomes available during
    the timeout interval, the method returns True immediately. If the
    timeout interval expires without data being ready, the method
    returns False. A timeoutMsec value of 0 checks for data ready, and
    returns immediately without waiting.

    Parameters
    ----------
    timeoutMsec : int
        Timeout interval in milliseconds.

    Returns
    -------
    bool
        Ready status. True if data is ready, False if data not ready.
    """
    ready = c_bool()
    err_check(rsa.IQSTREAM_WaitForIQDataReady(c_int(timeoutMsec),
        byref(ready)))
    return ready.value

""" PLAYBACK FUNCTIONS """

# def PLAYBACK_OpenDiskFile(filename, startPercentage, stopPercentage,
#                           skipTimeBetweenFullAcquisitions, loopAtEndOfFile,
#                           emulateRealTime):

def PLAYBACK_GetReplayComplete():
    """
    Determine if a replaying file has reached the end of file contents.

    Note that in loop back mode, a file will never report True from a
    call to PLAYBACK_GetReplayComplete().

    Returns
    -------
    bool
        True indicates playback completed. False indicates incomplete.
    """
    complete = c_bool()
    err_check(rsa.PLAYBACK_GetReplayComplete(byref(complete)))
    return complete.value

""" POWER FUNCTIONS """

def POWER_GetStatus():
    """
    Return the device power and battery status information.

    Note: This method is for the RSA500A series instruments only.

    If the returned value batteryPresent is False, the following
    battery-related status indicators which are returned are invalid
    and should be ignored.

    During charge, the over temp alarm can be set if the pack exceeds
    45 deg C. The charger should stop charging when the alarm is set.
    If charging doesn't stop, the pack will open a resettable
    protection FET.

    During discharge, the over temp alarm will set if the pack exceeds
    60 deg C. The pack will set the alarm bit, but if the temperature
    doesn't decrease, the pack will open a resettable protection FET
    and shut down the device.

    RSA600A series devices can also return a result from this method.
    However, since they do not have an internal battery, they will
    always report a status of externalPowerPresent = True, and
    batteryPresent = False, and the following returned values being
    invalid.

    Returns
    -------
    externalPowerPresent : bool
        True for external power connected, False for no external power.
    batteryPresent : bool
        True for batter installed, False for no battery installed.
    batteryChargeLevel : float
        Battery charge level in percent (100.0 indicating full charge).
    batteryOverTemperature : bool
        True if battery pack over temperature. More details above.
    bateryHardwareError : bool
        True when battery controller has detected a battery HW error.
        False when the battery HW is operating normally.
    """
    pwrInfo = POWER_INFO()
    err_check(rsa.POWER_GetStatus(byref(pwrInfo)))
    return (pwrInfo.externalPowerPresent.value,
        pwrInfo.batteryPresent.value, pwrInfo.batteryChargeLevel.value,
        pwrInfo.batteryOverTemperature.value,
        pwrInfo.batteryHardwareError.value)

""" SPECTRUM METHODS """

def SPECTRUM_AcquireTrace():
    """
    Initiate a spectrum trace acquisition.

    Before calling this method, all acquisition parameters must be set
    to valid states. These include center frequency, reference level,
    any desired trigger conditions, and the spectrum configuration
    settings.
    """
    err_check(rsa.SPECTRUM_AcquireTrace())

def SPECTRUM_GetEnable():
    """
    Return the spectrum measurement enable status.

    Returns
    -------
    bool
        True if spectrum measurement enabled, False if disabled.
    """
    enable = c_bool()
    err_check(rsa.SPECTRUM_GetEnable(byref(enable)))
    return enable.value

def SPECTRUM_GetLimits():
    """
    Return the limits of the spectrum settings.

    Returns
    -------
    maxSpan : float
        Maximum span (device dependent).
    minSpan : float
        Minimum span.
    maxRBW : float
        Maximum resolution bandwidth.
    minRBW : float
        Minimum resolution bandwidth.
    maxVBW : float
        Maximum video bandwidth.
    minVBW : float
        Minimum video bandwidth.
    maxTraceLength : int
        Maximum trace length.
    minTraceLength : int
        Minimum trace length.
    """
    limits = SPECTRUM_LIMITS()
    err_check(rsa.SPECTRUM_GetLimits(byref(limits)))
    return (limits.maxSpan.value, limits.minSpan.value,
            limits.maxRBW.value, limits.minRBW.value,
            limits.maxVBW.value, limits.maxTraceLength.value,
            limits.minTraceLength.value)

def SPECTRUM_GetSettings():
    """
    Return the spectrum settings.

    In addition to user settings, this method also returns some
    internal setting values.

    Returns
    -------
    span : float
        Span measured in Hz.
    rbw : float
        Resolution bandwidth measured in Hz.
    enableVBW : bool
        True for video bandwidth enabled, False for disabled.
    vbw : float
        Video bandwidth measured in Hz.
    traceLength : int
        Number of trace points.
    window : string
        Windowing method used for the transform.
    verticalUnit : string
        Vertical units.
    actualStartFreq : float
        Actual start frequency in Hz.
    actualStopFreq : float
        Actual stop frequency in Hz.
    actualFreqStepSize : float
        Actual frequency step size in Hz.
    actualRBW : float
        Actual resolution bandwidth in Hz.
    actualVBW : float
        Not used.
    actualNumIQSamples : int
        Actual number of IQ samples used for transform.
    """
    settings = SPECTRUM_SETTINGS()
    err_check(rsa.SPECTRUM_GetSettings(byref(sets)))
    return (sets.span, sets.rbw, sets.enableVBW, sets.vbw, sets.traceLength,
            SPECTRUM_WINDOWS[sets.window],
            SPECTRUM_VERTICAL_UNITS[sets.verticalUnit], sets.actualStartFreq,
            sets.actualStopFreq, sets.actualFreqStepSize, sets.actualRBW,
            sets.actualVBW, sets.actualNumIQSamples)

def SPECTRUM_GetTrace(trace, maxTracePoints):
    """
    Return the spectrum trace data.

    Parameters
    ----------
    trace : int
        Either 1, 2, or 3, corresponding to the desired spectrum trace.
    maxTracePoints : int
        Maximum number of trace points to retrieve. The traceData array
        should be at least this size.

    Returns
    -------
    traceData : float array
        Spectrum trace data, in the unit of verticalunit specified in
        the spectrum settings.
    outTracePoints : int
        Actual number of valid trace points in traceData array.
    """
    trace -= 1
    traceData = (c_float * maxTracePoints)()
    outTracePoints = c_int()
    err_check(rsa.SPECTRUM_GetTrace(c_int(trace), c_int(maxTracePoints),
                                    byref(traceData), byref(outTracePoints)))
    return traceData, outTracePoints.value

def SPECTRUM_GetTraceInfo():
    """
    Return the spectrum result information.

    Returns
    -------
    timestamp : int
        Timestamp. See REFTIME_GetTimeFromTimestamp() for converting
        from timestamp to time.
    acqDataStatus : int
        1 for adcOverrange, 2 for refFreqUnlock, and 32 for adcDataLost.
    """
    traceInfo = SPECTRUM_TRACEINFO()
    err_check(rsa.SPECTRUM_GetTraceInfo(byref(traceInfo)))
    return traceInfo.timestamp.value, traceInfo.acqDataStatus.value

def SPECTRUM_GetTraceType(trace):
    """
    Query the trace settings.

    Parameters
    ----------
    trace : int
        Either 1, 2, or 3 corresponding to the desired spectrum trace.

    Returns
    -------
    enable : bool
        Trace enable status. True for enabled, False for disabled.
    detector : string
        Detector type. Valid results are:
            PosPeak, NegPeak, AverageVRMS, or Sample.
    """
    trace -= 1
    enable = c_bool()
    detector = c_int()
    err_check(rsa.SPECTRUM_GetTraceType(c_int(trace), byref(enable),
                                        byref(detector)))
    return enable.value, SPECTRUM_DETECTORS[detector.value]

def SPECTRUM_SetDefault():
    """
    Set the spectrum settings to their default values.

    This does not change the spectrum enable status. The following are
    the default settings:
        Span : 40 MHz
        RBW : 300 kHz
        Enable VBW : False
        VBW : 300 kHz
        Trace Length : 801
        Window : Kaiser
        Vertical Unit : dBm
        Trace 0 : Enable, +Peak
        Trace 1 : Disable, -Peak
        Trace 2 : Disable, Average
    """
    err_check(rsa.SPECTRUM_SetDefault())

def SPECTRUM_SetEnable(enable):
    """
    Set the spectrum enable status.

    When the spectrum measurement is enabled, the IQ acquisition is
    disabled.

    Parameters
    ----------
    enable : bool
        True enables the spectrum measurement. False disables it.
    """
    err_check(rsa.SPECTRUM_SetEnable(c_bool(enable)))

def SPECTRUM_SetSettings(span, rbw, enableVBW, vbw, traceLength, window, verticalUnit):
    """
    Set the spectrum settings.

    Parameters
    ----------
    span : float
        Span measured in Hz.
    rbw : float
        Resolution bandwidth measured in Hz.
    enableVBW : bool
        True for video bandwidth enabled, False for disabled.
    vbw : float
        Video bandwidth measured in Hz.
    traceLength : int
        Number of trace points.
    window : string
        Windowing method used for the transform.
    verticalUnit : string
        Vertical units.
    
    Valid settings for window:
        Kaiser, Mil6dB, BlackmanHarris, Rectangular, FlatTop, or Hann.

    Valid settings for verticalUnit:
        dBm, Watt, Volt, Amp, or dBmV.

    Raises
    ------
    SDR_Error
        If window or verticalUnit string inputs are not one of the
        allowed settings.
    """
    if window in SPECTRUM_WINDOWS:
        if verticalUnit in SPECTRUM_VERTICAL_UNITS:
            settings = SPECTRUM_SETTINGS()
            settings.span = span
            settings.rbw = rbw
            settings.enableVBW = enableVBW
            settings.vbw = vbw
            settings.traceLength = traceLength
            settings.window = SPECTRUM_WINDOWS.index(window)
            settings.verticalUnit = SPECTRUM_VERTICAL_UNITS.index(verticalUnit)
            err_check(rsa.SPECTRUM_SetSettings(settings))
        else:
            raise SDR_Error(0, "Vertical Unit Input Invalid.",
                "Please enter one of: dBm, Watt, Volt, Amp, or dBmV.")
    else:
        raise SDR_Error(0, "Windowing Method Input Invalid.",
            "Please enter one of: Kaiser, Mil6dB, BlackmanHarris, Rectangular"
            + " FlatTop, or Hann.")

def SPECTRUM_SetTraceType(trace, enable, detector):
    """
    Set the trace settings.

    Parameters
    ----------
    trace : int
        One of the spectrum traces. Can be 1, 2, or 3.
    enable : bool
        True enables trace output. False disables it.
    detector : string
        Detector type. Valid settings:
            PosPeak, NegPeak, AverageVRMS, or Sample.

    Raises
    ------
    SDR_Error
        If the detector type input is not one of the valid settings.
    """
    trace -= 1
    if detector in SPECTRUM_DETECTORS:
        detVal = SPECTRUM_DETECTORS.index(detector)
        err_check(rsa.SPECTRUM_SetTraceType(c_int(trace), c_bool(enable),
                                            c_int(detVal)))
    else:
        raise SDR_Error(0, "Detector Type Input Invalid.",
            "Please enter one of: PosPeak, NegPeak, AverageVRMS, or Sample.")

def SPECTRUM_WaitForTraceReady(timeoutMsec):
    """
    Wait for the spectrum trace data to be ready to be queried.

    Parameters
    ----------
    timeoutMsec : int
        Timeout value in msec.

    Returns
    -------
    bool
        True indicates spectrum trace data is ready for acquisition.
        False indicates it is not ready, and timeout value is exceeded.
    """
    ready = c_bool()
    err_check(rsa.SPECTRUM_WaitForTraceReady(c_int(timeoutMsec),
                                             byref(ready)))
    return ready.value

""" TIME METHODS """

def REFTIME_SetReferenceTime(refTimeSec, refTimeNsec, refTimestamp):
    """
    Set the RSA API time system association.

    This method sets the RSA API time system association between a
    "wall-clock" time value and the internal timestamp counter. The
    wall-clock time is composed of refTimeSec + refTimeNsec, which
    specify a UTC time to nanosecond precision.

    At device connection, the API automatically initializes the time
    system using this method to associate current OS time with the
    current value of the timestamp counter. This setting does not give
    high-accuracy time alignment due to the uncertainty in the OS time,
    but provides a basic time/timestamp association. The REFTIME
    methods then use this association for time calculations. To re-
    initialize the time system this way some time after connection,
    call the method with all arguments equal to 0.

    If a higher-precision time reference is available, such as GPS or
    GNSS receiver with 1PPS pulse output, or other precisely known time
    event, the API time system can be aligned to it by capturing the
    timestamp count of the event using the External trigger input. Then
    the timestamp value and corresponding wall-time value (sec+nsec)
    are associated using this method. This provides timestamp
    accuracy as good as the accuracy of the time + event alignment.

    If the user application calls this method to set the time
    reference, the REFTIME_GetReferenceTimeSource() method will return
    USER status.

    Parameters
    ----------
    refTimeSec : int
        Seconds component of time system wall-clock reference time.
        Format is number of seconds elapsed since midnight (00:00:00),
        Jan 1, 1970, UTC.
    refTimeNsec : int
        Nanosecond component of time system wall-clock reference time.
        Format is number of integer nanoseconds within the second
        specified in refTimeSec.
    refTimestamp : int
        Timestamp counter component of time system reference time.
        Format is the integer timestamp count corresponding to the time
        specified by refTimeSec + refTimeNsec.
    """
    err_check(rsa.REFTIME_SetReferenceTime(c_int(refTimeSec),
                                           c_int(refTimeNsec),
                                           c_int(refTimestamp)))

def REFTIME_GetReferenceTime():
    """
    Query the RSA API system time association.

    The refTimeSec value is the number of seconds elapsed since
    midnight (00:00:00), Jan 1, 1970, UTC.

    The refTimeNsec value is the number of nanoseconds offset into the
    refTimeSec second. refTimestamp is the timestamp counter value.
    These values are initially set automatically by the API system
    using OS time, but may be modified by the REFTIME_SetReferenceTime()
    method if a better reference time source is available.

    Returns
    -------
    refTimeSec : int
        Seconds component of reference time association.
    refTimeNsec : int
        Nanosecond component of reference time association.
    refTimestamp : int
        Counter timestamp of reference time association.
    """
    refTimeSec = c_int()
    refTimeNsec = c_int()
    refTimestamp = c_int()
    err_check(rsa.REFTIME_GetReferenceTime(byref(refTimeSec),
                                           byref(refTimeNsec),
                                           byref(refTimestamp)))
    return refTimeSec.value, refTimeNsec.value, refTimestamp.value

def REFTIME_GetCurrentTime():
    """
    Return the current RSA API system time.

    Returns second and nanosecond components, along with the
    corresponding current timestamp value.

    The o_TimeSec value is the number of seconds elapsed since midnight
    (00:00:00), Jan 1, 1970, UTC. The o_timeNsec value is the number of
    nanoseconds offset into the specified second. The time and
    timestamp values are accurately aligned with each other at the time
    of the method call.

    Returns
    -------
    o_timeSec : int
        Seconds component of current time.
    o_timeNsec : int
        Nanoseconds component of current time.
    o_timestamp : int
        Timestamp of current time.
    """
    o_timeSec = c_int()
    o_timeNsec = c_int()
    o_timestamp = c_int()
    err_check(rsa.REFTIME_GetCurrentTime(byref(o_timeSec), byref(o_timeNsec),
                                         byref(o_timestamp)))
    return o_timeSec.value, o_timeNsec.value, o_timestamp.value

def REFTIME_GetIntervalSinceRefTimeSet():
    """
    Return num. of sec's elapsed since time/timestamp association set.

    Returns
    -------
    float
        Seconds since the internal reference time/timestamp association
        was last set.
    """
    sec = c_double()
    err_check(rsa.REFTIME_GetIntervalSinceRefTimeSet(byref(sec)))
    return sec.value

def REFTIME_GetReferenceTimeSource():
    """
    Query the API time reference alignment source.

    The most recent source used to set the time reference is reported.
    During the API connect operation, the time reference source is set
    to SYSTEM, indicating the computer system time was used to
    initialize the time reference. Following connection, if the user
    application sets the time reference using REFTIME_SetReferenceTime(),
    the source value is set to USER.

    For RSA500/600A Series: If the GNSS receiver is enabled, achieves
    navigation lock and is enabled to align the reference time, the
    source value is set to GNSS after the first alignment occurs.

    Returns
    -------
    string
        Current time reference source. Valid results:
            NONE, SYSTEM, GNSS, or USER.
    """
    srcVal = c_int()
    err_check(rsa.REFTIME_GetReferenceTimeSource(byref(srcVal)))
    return REFTIME_SRC[srcVal.value]

def REFTIME_GetTimeFromTimestamp(i_timestamp):
    """
    Convert timestamp into equivalent time using current reference.

    The timeSec value is the number of seconds elapsed since midnight
    (00:00:00), Jan 1, 1970, UTC. The timeNsec value is the number of
    nanoseconds into the specified second.

    Parameters
    ----------
    i_timestamp : int
        Timestamp counter time to convert to time values.

    Returns
    -------
    o_timeSec : int
        Time value seconds component.
    o_timeNsec : int
        Time value nanoseconds component.
    """
    o_timeSec = c_int()
    o_timeNsec = c_int()
    err_check(rsa.REFTIME_GetTimeFromTimestamp(c_int(i_timestamp),
                                               byref(o_timeSec),
                                               byref(o_timeNsec)))
    return o_timeSec.value, o_timeNsec.value

def REFTIME_GetTimestampFromTime(i_timeSec, i_timeNsec):
    """
    Convert time into equivalent timestamp using current reference.

    Parameters
    ----------
    i_timeSec : int
        Seconds component to convert to timestamp.
    i_timeNsec : int
        Nanoseconds component to convert to timestamp.

    Returns
    -------
    int
        Equivalent timestamp value.
    """
    o_timestamp = c_int()    
    err_check(rsa.REFTIME_GetTimestampFromTime(c_int(i_timeSec),
                                               c_int(i_timeNsec),
                                               byref(o_timestamp)))
    return o_timestamp.value

def REFTIME_GetTimestampRate():
    """
    Return clock rate of the countinuously running timestamp counter.

    This method can be used for calculations on timestamp values.

    Returns
    -------
    int
        Timestamp counter clock rate.
    """
    refTimestampRate = c_int()
    err_check(rsa.REFTIME_GetTimestampRate(byref(refTimestampRate)))
    return refTimestampRate.value

""" TRACKING GENERATOR METHODS """

def TRKGEN_GetEnable():
    """
    Return the tracking generator enabled status.

    Note: This method is for RSA500A/600A series instruments only.

    Returns
    -------
    bool
        True for enabled and powered on. False for disabled and off.
    """
    enable = c_bool()
    err_check(rsa.TRKGEN_GetEnable(byref(enable)))
    return enable.value

def TRKGEN_GetHwInstalled():
    """
    Return the tracking generator hardware present status.

    Note: This method is for RSA500A/600A series instruments only.

    Returns
    -------
    bool
        True for trk. gen. HW is installed in the unit. False if not.
    """
    installed = c_bool()
    err_check(rsa.TRKGEN_GetHwInstalled(byref(installed)))
    return installed.value

def TRKGEN_GetOutputLevel():
    """
    Return the output level of the tracking generator.

    Note: This method is for RSA500A/600A series instruments only.

    Returns
    -------
    float
        Value of the tracking generator output level in dBm.
        Range: -43 dBm to -3 dBm
    """
    level = c_double()
    err_check(rsa.TRKGEN_GetOutputLevel(byref(level)))
    return level.value

def TRKGEN_SetEnable(enable):
    """
    Set the tracking generator enable status.

    Note: This method is for RSA500A/600A series instruments only.

    Parameters
    ----------
    enable : bool
        True to enable, False to disable
    """
    err_check(rsa.TRKGEN_SetEnable(c_bool(enable)))

def TRKGEN_SetOutputLevel(level):
    """
    Set the output power of the tracking generator in dBm.

    Note: This method is for RSA500A/600A series instruments only.

    The tracking generator output should be set prior to setting the
    center frequency. See the CONFIG_SetCenterFreq() and
    CONFIG_Preset() methods to set the center frequency.

    Parameters
    ----------
    level : float
        Requested output level of tracking generator in dBm.
        Range: -43 to -3 dBm.

    Raises
    ------
    SDR_Error
        If the desired output level is not in the allowed range.
    """
    if -43 <= level <= -3:
        err_check(rsa.TRKGEN_SetOutputLevel(c_double(level)))
    else:
        raise SDR_Error(0, "Input value is not within the valid range.",
            "Please enter a value between -43 and -3 dBm.")

""" TRIGGER METHODS """

def TRIG_ForceTrigger():
    """Force the device to trigger."""
    err_check(rsa.TRIG_ForceTrigger())

def TRIG_GetIFPowerTriggerLevel():
    """
    Return the trigger power level.

    Returns
    -------
    float
        Detection power level for the IF power trigger source
    """
    level = c_double()
    err_check(rsa.TRIG_GetIFPowerTriggerLevel(byref(level)))
    return level.value

def TRIG_GetTriggerMode():
    """
    Return the trigger mode (either freeRun or triggered).

    When the mode is set to freeRun, the signal is continually updated.

    When the mode is set to Triggered, the data is only updated when a trigger occurs.

    Returns
    -------
    string
        Either "freeRun" or "Triggered".
    """
    mode = c_int()
    err_check(rsa.TRIG_GetTriggerMode(byref(mode)))
    return TRIGGER_MODE[mode.value]

def TRIG_GetTriggerPositionPercent():
    """
    Return the trigger position percent.

    Note: The trigger position setting only affects IQ Block and
    Spectrum acquisitions.

    Returns
    -------
    float
        Trigger position percent value when the method completes.
    """
    trigPosPercent = c_double()
    err_check(rsa.TRIG_GetTriggerPositionPercent(byref(trigPosPercent)))
    return trigPosPercent.value

def TRIG_GetTriggerSource():
    """
    Return the trigger source.

    When set to external, acquisition triggering looks at the external
    trigger input for a trigger signal. When set to IF power level, the
    power of the signal itself causes a trigger to occur.

    Returns
    -------
    string
        The trigger source type. Valid results:
            External : External source.
            IFPowerLevel : IF power level source.
    """
    source = c_int()
    err_check(rsa.TRIG_GetTriggerSource(byref(source)))
    return TRIGGER_SOURCE[source.value]

def TRIG_GetTriggerTransition():
    """
    Return the current trigger transition mode.

    Returns
    -------
    string
        Name of the trigger transition mode. Valid results:
            LH : Trigger on low-to-high input level change.
            HL : Trigger on high-to-low input level change.
            Either : Trigger on either LH or HL transitions.
    """
    transition = c_int()
    err_check(rsa.TRIG_GetTriggerTransition(byref(transition)))
    return TRIGGER_TRANSITION[transition.value]

def TRIG_SetIFPowerTriggerLevel(level):
    """
    Set the IF power detection level.

    When set to the IF power level trigger source, a trigger occurs
    when the signal power level crosses this detection level.

    Parameters
     ----------
    level : float
        The detection power level setting for the IF power trigger
        source.
    """
    err_check(rsa.TRIG_SetIFPowerTriggerLevel(c_double(level)))

def TRIG_SetTriggerMode(mode):
    """
    Set the trigger mode.

    Parameters
    ----------
    mode : string
        The trigger mode. Valid settings:
            freeRun : to continually gather data
            Triggered : do not acquire new data unless triggered

    Raises
    ------
    SDR_Error
        If the input string is not one of the valid settings.
    """
    if mode in TRIGGER_MODE:
        modeValue = TRIGGER_MODE.index(mode)
        err_check(rsa.TRIG_SetTriggerMode(c_int(modeValue)))
    else:
        raise SDR_Error(0,
            "Invalid trigger mode input string.",
            "Input is case sensitive. Please input one of: freeRun, "
            + "Triggered."
        )

def TRIG_SetTriggerPositionPercent(trigPosPercent):
    """
    Set the trigger position percentage.

    This value determines how much data to store before and after a 
    trigger event. The stored data is used to update the signal's image
    when a trigger occurs. The trigger position setting only affects IQ
    Block and Spectrum acquisitions.

    Default setting is 50%.

    Parameters
    ----------
    trigPosPercent : float
        The trigger position percentage, from 1% to 99%.

    Raises
    ------
    SDR_Error
        If the input is not in the valid range from 1 to 99 percent.
    """
    if 1 <= trigPosPercent <= 99:
        err_check(rsa.TRIG_SetTriggerPositionPercent(c_double(trigPosPercent)))
    else:
        raise SDR_Error(0,
            "Input percentage invalid.",
            "Please enter a value in the range: 1 to 99 percent."
        )

def TRIG_SetTriggerSource(source):
    """
    Set the trigger source.

    Parameters
    ----------
    source : string
        A trigger source type. Valid settings:
            External : External source.
            IFPowerLevel: IF power level source.

    Raises
    ------
    SDR_Error
        If the input string does not match one of the valid settings.
    """
    if source in TRIGGER_SOURCE:
        sourceValue = TRIGGER_SOURCE.index(source)
        err_check(rsa.TRIG_SetTriggerSource(c_int(sourceValue)))
    else:
        raise SDR_Error(0,
            "Invalid trigger source input string.",
            "Please input either 'External' or 'IFPowerLevel'"
        )

def TRIG_SetTriggerTransition(transition):
    """
    Set the trigger transition detection mode.

    Parameters
    ----------
    transition : string
        A trigger transition mode. Valid settings:
            LH : Trigger on low-to-high input level change.
            HL : Trigger on high-to-low input level change.
            Either : Trigger on either LH or HL transitions.

    Raises
    ------
    SDR_Error
        If the input string does not match one of the valid settings.
    """
    if transition in TRIGGER_TRANSITION:
        transValue = TRIGGER_TRANSITION.index(transition)
        err_check(rsa.TRIG_SetTriggerTransition(c_int(transValue)))
    else:
        raise SDR_Error(0,
            "Invalid trigger transition mode input string.",
            "Please input either: 'LH', 'HL', or 'Either'"
        )