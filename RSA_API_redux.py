"""

Notes/To Do's

Currently, ALL SDR_Error codes thrown are arbitrary placeholders
If no returns are specified in a method's docstring, it returns None

error handling:
possibly should add general catch-all's for all commands which could
return an error from the API. For example, look at reset() command
if doing this^, include it in "Raises" part of docstring? Don't think
this is necessary.
alternatively, implement "RSA_Error" for these types and use internal
API error codes

Support multiple devices? search/connect could allow for selection 
among multiple

"""
from ctypes import *
from SDR_Error import SDR_Error

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

""" CUSTOM ENUMERATION TYPES """
# These are defined as tuples, in which the index of each item corresponds
# to the integer value for the item as defined in the API manual
FREQREF_SOURCE = ("INTERNAL", "EXTREF", "GNSS", "USER")
DEVEVENT = ("OVERRANGE", "TRIGGER", "1PPS")
IQSOUTDEST = ("CLIENT", "FILE_TIQ", "FILE_SIQ", "FILE_SIQ_SPLIT")
IQSOUTDTYPE = ("SINGLE", "INT32", "INT16", "SINGLE_SCALE_INT32")
TRIGGER_MODE = ("freeRun", "Triggered")
TRIGGER_SOURCE = ("External", "IFPowerLevel")
TRIGGER_TRANSITION = ("LH", "HL", "Either")

""" CUSTOM DATA STRUCTURES """
class IQSTRMFILEINFO(Structure):
    _fields_ = [('numberSamples', c_uint64),
                ('sample0Timestamp', c_uint64),
                ('triggerSampleIndex', c_uint64),
                ('triggerTimestamp', c_uint64),
                ('acqStatus', c_uint32),
                ('filenames', c_wchar_p)]

""" AGGREGATE/HIGH-LEVEL METHODS """
def search_connect(loadPreset=True):
    """
    Search for and connect to a Tektronix RSA device. 
    
    More than 10 devices cannot be found at once. Search criteria are
    not implemented, and connection only occurs if exactly one device is
    found.

    Preset configuration is optionally loaded upon connection. This
    results in: trigger mode set to Free Run, center frequency to 1.5
    GHz, span to 40 MHz, IQ record length to 1024 samples, and
    reference level to 0 dBm. Preset functionality is enabled by
    default.

    Parameters
    ----------
    loadPreset : bool
        Whether to load the preset configuration upon connection.

    Raises
    ------
    SDR_Error
        If no matching device is found, if more than one matching
        device are found, or if a single device is found but connection
        fails.
    """
    foundDevices = search()
    numFound = len(foundDevices)

    # Zero devices found case handled within search()
    # Multiple devices found case:
    if numFound > 1:
        err_body = "The following devices were found:"
        # Add list of found devices to error body text
        for (ID, key) in foundDevices.items():
            err_body += "\r\n{}".format(str(ID) + ": " + str(key))
        raise SDR_Error(
            0,
            "Found {} devices, need exactly 1.".format(numFound),
            err_body
        )

    connect()

    if loadPreset:
        preset()

""" CONFIG METHODS """

# Naming: CONFIG_SomeCommand() --> someCommand()

def getCenterFreq():
    """Return the current center frequency in Hz."""
    cf = c_double()
    rsa.CONFIG_GetCenterFreq(byref(cf))
    return cf.value

def getExternalRefFrequency():
    """
    Return the frequency, in Hz, of the external reference"

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
    src = getFrequencyReferenceSource()
    if src == FREQREF_SOURCE[0]:
        raise SDR_Error(
            0,
            "External reference input is not in use.",
            "The external reference input must be enabled for useful results."
        )
    else:
        extFreq = c_double()
        rsa.CONFIG_GetExternalRefFrequency(byref(extFreq))
        return extFreq.value

def getFrequencyReferenceSource():
    """
    Return a string representing the frequency reference source.

    Valid results are FRS_INTERNAL, FRS_EXTREF, FRS_GNSS, and FRS_USER.
    Note that the RSA306 and RSA306b support only the FRS_INTERNAL and
    FRS_EXTREF sources.

    Returns
    -------
    string
        A representative name of the frequency reference source.
    """
    src = c_int()
    rsa.CONFIG_GetFrequencyReferenceSource(byref(src))
    return FREQREF_SOURCE[src.value]

def getMaxCenterFreq():
    """Return the maximum center frequency in Hz."""
    maxCF = c_double()
    rsa.CONFIG_GetMaxCenterFreq(byref(maxCF))
    return maxCF.value

def getMinCenterFreq():
    """Return the minimum center frequency in Hz."""
    minCF = c_double()
    rsa.CONFIG_GetMinCenterFreq(byref(minCF))
    return minCF.value

def getReferenceLevel():
    """
    Return the current reference level in dBm.

    The reference level must fall between -130 dBm and +30 dBm.

    Returns
    -------
    float
        The reference level, measured in dBm.
    """
    refLevel = c_double()
    rsa.CONFIG_GetReferenceLevel(byref(refLevel))
    return refLevel.value

def preset():
    """
    Set the connected device to preset values.

    This method sets the trigger mode to Free Run, the center frequency
    to 1.5 GHz, the span to 40 MHz, the IQ record length to 1024 
    samples, and the reference level to 0 dBm.
    """
    rsa.CONFIG_Preset()

def setCenterFreq(cf):
    """
    Set the center frequency value.

    A check is performed to ensure that the desired value is within the
    allowed range. When using the tracking generator, be sure to set the
    tracking generator output level before setting the center frequency.

    Parameters
    ----------
    cf : float or int
        Value to set center frequency, in Hz.

    Returns
    -------
    None

    Raises
    ------
    SDR_Error
        If desired center frequency is not in the allowed range.
    """
    minCF = getMinCenterFreq()
    maxCF = getMaxCenterFreq()

    if minCF <= cf <= maxCF:
        rsa.CONFIG_SetCenterFreq(c_double(cf))
    else:
        # Error has placeholder numerical ID. Update later.
        raise SDR_Error(
            0,
            "Desired center frequency not in range.",
            "Please choose a value between {} and {} Hz.".format(minCF,
                maxCF)
        )

def setExternalRefEnable(exRefEn):
    """
    Enable or disable the external reference.

    When the external reference is enabled, an external reference signal must
    be connected to the "Ref In" port. The signal must have a frequency of 10
    MHz with a +10 dBm maximum amplitude. This signal is used by the local
    oscillators to mix with the input signal. When the external reference is
    disabled, an internal reference source is used.

    Parameters
    ----------
    exRefEn : bool
        True enables the external reference. False disables it.

    Returns
    -------
    None
    """
    rsa.CONFIG_SetExternalRefEnable(c_bool(exRefEn))

def setFrequencyReferenceSource(src="INTERNAL"):
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
        If the input string is not a valid setting listed above.
    """
    if src in FREQREF_SOURCE:
        value = c_int(FREQREF_SOURCE.index(src))
        rsa.CONFIG_SetFrequencyReferenceSource(value)
    else:
        raise SDR_Error(
            0,
            "Input string does not match one of the valid settings.",
            "Please input one of: INTERNAL, EXTREF, GNSS, or USER."
        )

def setReferenceLevel(refLevel):
    """
    Set the reference level

    A check is performed to ensure that the desired value is within the
    allowed range. The reference level controls the signal path gain and
    attenuation settings. The value should be set to the maximum expected
    signal power level in dBm. Setting the value too low may result in over-
    driving the signal path and ADC, while setting it too high results in
    excess noise in the signal.

    Parameters
    ----------
    refLevel : float or int
        Reference level measured in dBm. Range: -130 dBm to 30 dBm.

    Returns
    -------
    None

    Raises
    ------
    SDR_Error
        If desired reference level is not in the allowed range.
    """
    minRefLev = -130 # Min. value, dBm
    maxRefLev = 30 # Max. value, dBm
    if minRefLev <= refLevel <= maxRefLev:
        rsa.CONFIG_SetReferenceLevel(c_double(refLevel))
    else:
        # Error has placeholder numerical ID. Update later.
        raise SDR_Error(
            0,
            "Desired reference level not in range.",
            "Please choose a value between {} and {} dBm.".format(minRefLev,
                maxRefLev)
        )

""" DEVICE METHODS """

# Tested ? F

# Naming: DEVICE_SomeCommand --> someCommand()

#      Omitted method     |    Reason for omission
#  ---------------------  | -------------------------
#  DEVICE_GetErrorString  | Not currently using Tek's error codes
# DEVICE_GetNomenclatureW | Implemented getNomenclature() instead

def connect(deviceID=0):
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
    try:
        rsa.DEVICE_Connect(c_int(deviceID))
    except Exception as e:
        raise SDR_Error(
            0,
            "Failed to connect to device.",
            e
        )

def disconnect():
    """Stop data acquisition and disconnect from connected device."""
    rsa.DEVICE_Disconnect()

def getEnable():
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
    rsa.DEVICE_GetEnable(byref(enable))
    return enable.value

def getFPGAVersion():
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
    rsa.DEVICE_GetFPGAVersion(byref(fpgaVersion))
    return fpgaVersion.value.decode('utf-8')

def getFWVersion():
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
    rsa.DEVICE_GetFWVersion(byref(fwVersion))
    return fwVersion.value.decode('utf-8')

def getHWVersion():
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
    rsa.DEVICE_GetHWVersion(byref(hwVersion))
    return hwVersion.value.decode('utf-8')

def getNomenclature():
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
    rsa.DEVICE_GetNomenclature(byref(nomenclature))
    return nomenclature.value.decode('utf-8')

def getSerialNumber():
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
    rsa.DEVICE_GetSerialNumber(byref(serialNum))
    return serialNum.value.decode('utf-8')

def getAPIVersion():
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
    rsa.DEVICE_GetAPIVersion(byref(apiVersion))
    return apiVersion.value.decode('utf-8')

def prepareForRun():
    """
    Put the system in a known state, ready to stream data.

    This method does not actually initiate data transfer. During file
    playback mode, this is useful to allow other parts of your
    application to prepare to receive data before starting the
    transfer. See startFrameTransfer(). This is in comparison to the
    run() function, which immediately starts data streaming without
    waiting for a "go" signal.

    Returns
    -------
    None
    """
    rsa.DEVICE_PrepareForRun()

def getInfo():
    """
    Retrieve multiple device and information strings.

    Obtained information includes: device nomenclature, serial number,
    firmware versionn, FPGA version, hardware version, and API version.

    Returns
    -------
    dict
        All of the above listed information, labeled.
    """
    nomenclature = getNomenclature()
    serialNum = getSerialNumber()
    fwVersion = getFWVersion()
    fpgaVersion = getFPGAVersion()
    hwVersion = getHWVersion()
    apiVersion = getAPIVersion()

    info = {
        "Nomenclature" : nomenclature,
        "Serial Number" : serialNum,
        "FW Version" : fwVersion,
        "FPGA Version" : fpgaVersion,
        "HW Version" : hwVersion,
        "API Version" : apiVersion
    }

    return info

def getOverTemperatureStatus():
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
    overTemperature = c_bool()
    rsa.DEVICE_GetOverTemperatureStatus(byref(overTemperature))
    return overTemperature.value

def reset(deviceID=-1):
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
        If multiple devices are attached and a deviceID is not given.
    """
    foundDevices = search()
    numFound = len(foundDevices)

    if numFound == 1:
        deviceID = 0
    elif numFound > 1 and deviceID == -1:
        raise SDR_Error(
            0,
            "Multiple devices found, but no ID specified.",
            "Please give a deviceID to specify which device to reboot."
        )

    try:
        rsa.DEVICE_Reset(c_int(deviceID))
    except Exception as e:
        raise SDR_Error(
            0,
            "Failed to reboot device.",
            e
        )      

def run():
    """Start data acquisition."""
    rsa.DEVICE_Run() 

def search():
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

    rsa.DEVICE_Search(byref(numFound), byref(devIDs), devSerial, devType)
    foundDevices = {
        ID : (devSerial[ID].value.decode(), devType[ID].value.decode()) \
        for ID in devIDs
    }

    # If there are no devices, there is still a dict returned
    # with a device ID, but the other elements are empty.
    if foundDevices[0] == ('',''):
        raise SDR_Error(
            0,
            "Could not find a matching Tektronix RSA device.",
            "Please check the connection and try again."
        )
    else:
        return foundDevices

def startFrameTransfer():
    """
    Start data transfer.

    This is typically used as the trigger to start data streaming after
    a call to prepareForRun(). If the system is in the stopped state,
    this call places it back into the run state with no changes to any
    internal data or settings, and data streaming will begin assuming
    there are no errors.
    """
    rsa.DEVICE_StartFrameTransfer()

def stop():
    """
    Stop data acquisition.

    This method must be called when changes are made to values that
    affect the signal."""
    rsa.DEVICE_Stop()

# NOT WORKING (I think?)
def getEventStatus(eventID):
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

    1PPS event detection (RSA500A/600A only) requires the GNSS receiver
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
            1PPS : 1PPS event detection (RSA500A/600A only).

    Returns
    -------
    occurred : bool
        Indicates whether the event has occurred.
    timestamp : int
        Event occurrence timestamp. Only valid if occurred is True.
    """
    occurred  = c_bool()
    timestamp = c_uint64()
    if eventID in DEVEVENT:
        value = c_int(DEVEVENT.index(eventID))
    else:
        raise SDR_Error(
            0,
            "Input string does not match one of the valid settings.",
            "Please input one of: OVERRANGE, TRIGGER, or 1PPS."
        )
    try:
        rsa.DEVICE_GetEventStatus(byref(value), byref(occurred), byref(timestamp))
        return occurred.value, timestamp.value
    except Exception as e:
        raise SDR_Error(
            0,
            "Failed to get event status.",
            e
        )

""" IQ BLOCK METHODS """

# Naming: identical to official API names
# possibly remove IQBLK_ later? assure no conflicts
# or possible confusion

# def IQBLK_GetIQAcqInfo():
# def IQBLK_AcquireIQData():

def IQBLK_GetIQBandwidth():
    """
    Query the IQ bandwidth value.

    Returns
    -------
    float
        The IQ bandwidth value.
    """
    iqBandwidth = c_double()
    rsa.IQBLK_GetIQBandwidth(byref(iqBandwidth))
    return iqBandwidth.value

# def IQBLK_GetIQData():
# def IQBLK_GetIQDataCplx():
# def IQBLK_GetIQDataDeinterleaved():

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
    rsa.IQBLK_GetIQRecordLength(byref(recordLength))
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
    rsa.IQBLK_GetIQSampleRate(byref(iqSampleRate))
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
    rsa.IQBLK_GetMaxIQBandwidth(byref(maxBandwidth))
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
    rsa.IQBLK_GetMaxIQRecordLength(byref(maxIqRecLen))
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
    rsa.IQBLK_GetMinIQBandwidth(byref(minBandwidth))
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

    Returns
    -------
    None

    Raises
    ------
    SDR_Error
        If desired IQ bandwidth is not in the allowed range.
    """
    minBandwidth = IQBLK_GetMinIQBandwidth()
    maxBandwidth = IQBLK_GetMaxIQBandwidth()

    if minBandwidth <= iqBandwidth <= maxBandwidth:
        rsa.IQBLK_SetIQBandwidth(c_double(iqBandwidth))
    else:
        raise SDR_Error(
            0,
            "Desired bandwidth not in range.",
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

    Returns
    -------
    None

    Raises
    ------
    SDR_Error
        If desired IQ record length is not in the allowed range.
    """
    minIqRecLen = int(2)
    maxIqRecLen = IQBLK_GetMaxIQRecordLength()

    if minIqRecLen <= recordLength <= maxIqRecLen:
        rsa.IQBLK_SetIQRecordLength(c_int(recordLength))
    else:
        raise SDR_Error(
            0,
            "Desired record length not in range.",
            "Please choose a value between {} and {} samples.".format(
                minIqRecLen, maxIqRecLen)
        )

# !!! def IQBLK_WaitForIQDataReady():

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
    rsa.IQSTREAM_GetMaxAcqBandwidth(byref(maxBandwidthHz))
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
    rsa.IQSTREAM_GetMinAcqBandwidth(byref(minBandwidthHz))
    return minBandwidthHz.value

def IQSTREAM_ClearAcqStatus():
    """
    Reset the "sticky" status bits of the acqStatus info element during
    an IQ streaming run interval.

    This is effective for both client and file destination runs.

    Returns
    -------
    None
    """
    rsa.IQSTREAM_ClearAcqStatus()

def IQSTREAM_GetAcqParameters():
    """
    Retrieve the processing parameters of IQ streaming output bandwidth
    and sample rate, resulting from the user's requested bandwidth.

    Call this function after calling IQSTREAM_SetAcqBandwidth() to set
    the requested bandwidth. See IQSTREAM_SetAcqBandwidth() docstring
    for details of how requested bandwidth is used to select output
    bandwidth and sample rate settings.

    Returns
    -------
    float: bwHz_act
        Actual acquisition bandwidth of IQ streaming output data in Hz.
    float: srSps
        Actual sample rate of IQ streaming output data in Samples/sec.

    Note: These floats are returned in a single tuple, in this order
    """
    bwHz_act = c_double()
    srSps = c_double()
    rsa.IQSTREAM_GetAcqParameters(byref(bwHz_act), byref(srSps))
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

    Note: If acqStatus indicators show "Output buffer overflow", it is
    likely that the disk is too slow to keep up with writing the data
    generated by IQ stream processing. Use a faster disk (SSD is
    recommended), or a smaller acquisition bandwidth which generates
    data at a lower rate.

    Returns
    -------
    dict

    """
    fileinfo = IQSTRMFILEINFO()
    rsa.IQSTREAM_GetDiskFileInfo(byref(fileinfo))
    # filenames omitted because of unicode ValueErrors
    dictRes =  {
        'numberSamples' : fileinfo.numberSamples,
        'sample0Timestamp' : fileinfo.sample0Timestamp,
        'triggerSampleIndex' : fileinfo.triggerSampleIndex,
        'triggerTimestamp' : fileinfo.triggerTimestamp,
        'acqStatus' : fileinfo.acqStatus,
        'filenames' : fileinfo.filenames.value.decode('utf-8')
    }
    return dictRes
        
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

    Returns
    -------
    bool: isComplete
        Whether the IQ stream file output writing is complete.
    bool: isWriting
        Whether the IQ stream processing has started writing to file.
    """
    isComplete = c_bool()
    isWriting = c_bool()
    rsa.IQSTREAM_GetDiskFileWriteStatus(byref(isComplete), byref(isWriting))
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
    rsa.IQSTREAM_GetEnable(byref(enabled))
    return enabled.value

# This doesn't seem necessary
# def IQSTREAM_GetIQData():

def IQSTREAM_GetIQDataBufferSize():
    """
    Retrieve the maximum number of IQ sample pairs returned by IQSTREAM_GetIQData().

    Returns
    -------
    int
        Maximum size IQ output data buffer required when using client IQ access.
        Size value is in IQ sample pairs.
    """
    maxSize = c_int()
    rsa.IQSTREAM_GetIQDataBufferSize(byref(maxSize))
    return maxSize.value

def IQSTREAM_SetAcqBandwidth(bwHz_req):
    """
    Request the acquisition bandwidth of the output IQ stream samples.

    The requested bandwidth should only be changed when the instrument
    is in the global stopped state. The new BW setting does not take
    effect until the global system state is cycled from stopped to
    running. A check is performed to ensure the requested bandwidth is
    within the valid range.

    Note: The requested bandwidth directly determines the sample rate.
    The actual bandwidth and sample rate values can be queried after
    setting by using IQSTREAM_GetAcqParameters().

    Note: The requested bandwidth will be rounded up to the nearest
    value among: 5 MHz, 10 MHz, 20 MHz, and 40 MHz.

    Parameters
    ----------
    bwHz_req : float
        Requested acquisition bandwidth of IQ streaming data, in Hz.

    Returns
    -------
    None

    Raises
    ------
    SDR_Error
        If requested acquisition bandwidth is not in the valid range.
    """
    minAcBW = IQSTREAM_GetMinAcqBandwidth()
    maxAcBW = IQSTREAM_GetMaxAcqBandwidth()

    if minAcBW <= bwHz_req <= maxAcBW:
        rsa.IQSTREAM_SetAcqBandwidth(c_double(bwHz_req))
        newCF = get_centerFreq()
        return newCF
    else:
        # Error has placeholder numerical ID. Update later.
        raise SDR_Error(
            0,
            "Requested bandwidth not in range.",
            "Please choose a value between {} and {} Hz.".format(minAcBW,
                maxAcBW)
        )

def IQSTREAM_SetDiskFileLength(msec):
    """
    Set the time length of IQ data written to an output file.

    File output ends after the specified number of milliseconds of
    samples are stored. File storage can be terminated early by calling
    IQSTREAM_Stop(). Inputting a value of 0 sets no time limit on file
    output. In that case, file storage is only terminated by calling
    IQSTREAM_STOP().

    Parameters
    ----------
    msec : int
        Length of time in milliseconds to record IQ samples to file.

    Returns
    -------
    None

    Raises
    ------
    SDR_Error
        If input is a negative value.
    """
    if msec >= 0:
        rsa.IQSTREAM_SetDiskFileLength(c_int(msec))
    else:
        # Error has placeholder numerical ID. Update later.
        raise SDR_Error(
            0,
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
    function, <suffix> is set by IQSTREAM_SetDiskFilenameSuffix(), and
    <.ext> is set by IQSTREAM_SetOutputConfiguration(). If separate data
    and header files are generated, the same path/filename is used for
    both, with different extensions to indicate the contents.

    Parameters
    ----------
    filenameBase : string
        Base filename for file output.

    Returns
    -------
    None
    """
    rsa.IQSTREAM_SetDiskFilenameBaseW(c_wchar_p(filenameBase))

def IQSTREAM_SetDiskFilenameSuffix(suffixCtl):
    """
    Set the control that determines the appended filename suffix.

    Default behavior: A value of -1 generates a string from the file
    creation time in the format: "-YYYY.MM.DD.hh.mm.ss.msec". Note that
    this time is not directly linked to the data timestamps, and should
    not be used as a high-accuracy timestamp of the file data.

    Passing a value of -2 causes the base filename to be used withouta
    suffix. In this case, the output filename will not change from one
    run to the next, so each output file will overwrite the previous
    one unless the filename is explicitly changed.

    Values >= 0 generate a 5 digit, autoincrementing index, with an initial
    value equal to the input suffixCtl value. Format: "-nnnnn". The index
    increments by 1 each time IQSTREAM_Start() is invoked with file data
    destination setting.

    Parameters
    ----------
    suffixCtl : int
        The filename suffix control value.

    Returns
    -------
    None

    Raises
    ------
    SDR_Error
        If the input value is less than -2.
    """
    suffixCtl = int(suffixCtl)
    if suffixCtl >= -2:
        rsa.IQSTREAM_SetDiskFilenameSuffix(c_int(suffixCtl))
    else:
        # Error has placeholder numerical ID. Update later.
        raise SDR_Error(
            0,
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
    regardless of the destination or data type. Defaults to combined
    SIQ file with INT32 data.

    Note: TIQ format files only allow INT32 or INT16 data types.

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

    Returns
    -------
    None

    Raises
    ------
    SDR_Error
        If inputs are not valid settings, or if single data type is 
        selected along with TIQ file format.
    """
    if dest in IQSOUTDEST:
        if dtype in IQSOUTDTYPE:
            if dest == "FILE_TIQ" and "SINGLE" in dtype:
                raise SDR_Error(
                    0,
                    "Invalid selection of TIQ file and Single data type together",
                    "TIQ format files allow only INT32 or INT16 data types."
                )
            else:
                val1 = c_int(IQSOUTDEST.index(dest))
                val2 = c_int(IQSOUTDTYPE.index(dtype))
                rsa.IQSTREAM_SetOutputConfiguration(val1, val2)
        else:
            raise SDR_Error(
                0,
                "Input data type string does not match a valid setting.",
                "Please input one of: SINGLE, INT32, INT16, or " 
                + "SINGLE_SCALE_INT32."
            )
    else:
        raise SDR_Error(
            0,
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
    forceTrigger() can be used to generate a trigger even if the 
    specified one does not occur.

    If the data destination is the client application, data will become
    available soon after this function is invoked. Even if triggering
    is enabled, the data will begin flowing to the client without need
    for a trigger event. The client must begin retrieving data as soon
    after IQSTREAM_Start() as possible.

    Returns
    -------
    None
    """
    rsa.IQSTREAM_Start()

def IQSTREAM_Stop():
    """
    Terminate IQ stream processing and disable data output.

    If the data destination is file, file writing is stopped and the
    output file is closed.

    Returns
    -------
    None
    """
    rsa.IQSTREAM_Stop()

# !!! def IQSTREAM_WaitForIQDataReady():

""" TRIGGER FUNCTIONS """

# All tested and functional

def forceTrigger():
    """Force the device to trigger."""
    rsa.TRIG_ForceTrigger()

def getIFPowerTriggerLevel():
    """
    Return the trigger power level.

    Returns
    -------
    float
        Detection power level for the IF power trigger source
    """
    level = c_double()
    rsa.TRIG_GetIFPowerTriggerLevel(byref(level))
    return level.value

def getTriggerMode():
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
    rsa.TRIG_GetTriggerMode(byref(mode))
    return TRIGGER_MODE[mode.value]

def getTriggerPositionPercent():
    """
    Return the trigger position percent.

    Note: The trigger position setting only affects IQ Block and
    Spectrum acquisitions.

    Returns
    -------
    float
        Trigger position percent value when the function completes.
    """
    trigPosPercent = c_double()
    rsa.TRIG_GetTriggerPositionPercent(byref(trigPosPercent))
    return trigPosPercent.value

def getTriggerSource():
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
    rsa.TRIG_GetTriggerSource(byref(source))
    return TRIGGER_SOURCE[source.value]

def getTriggerTransition():
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
    rsa.TRIG_GetTriggerTransition(byref(transition))
    return TRIGGER_TRANSITION[transition.value]

def setIFPowerTriggerLevel(level):
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
    rsa.TRIG_SetIFPowerTriggerLevel(c_double(level))

def setTriggerMode(mode):
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
        rsa.TRIG_SetTriggerMode(c_int(modeValue))
    else:
        raise SDR_Error(
            0,
            "Invalid trigger mode input string.",
            "Input is case sensitive. Please input one of: freeRun, "
            + "Triggered."
        )

def setTriggerPositionPercent(trigPosPercent):
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
        rsa.TRIG_SetTriggerPositionPercent(c_double(trigPosPercent))
    else:
        raise SDR_Error(
            0,
            "Input percentage invalid.",
            "Please enter a value in the range: 1 to 99 percent."
        )

def setTriggerSource(source):
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
        rsa.TRIG_SetTriggerSource(c_int(sourceValue))
    else:
        raise SDR_Error(
            0,
            "Invalid trigger source input string.",
            "Please input either 'External' or 'IFPowerLevel'"
        )

def setTriggerTransition(transition):
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
        rsa.TRIG_SetTriggerTransition(c_int(transValue))
    else:
        raise SDR_Error(
            0,
            "Invalid trigger transition mode input string.",
            "Please input either: 'LH', 'HL', or 'Either'"
        )