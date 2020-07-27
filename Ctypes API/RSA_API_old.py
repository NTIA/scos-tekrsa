from ctypes import *
from SDR_Error import SDR_Error

# Currently, ALL SDR_Error codes thrown are arbitrary placeholders

""" LOAD RSA DRIVER """
RTLD_LAZY = 0x0001
LAZYLOAD = RTLD_LAZY | RTLD_GLOBAL
rsa = CDLL('./drivers/libRSA_API.so', LAZYLOAD)
usbapi = CDLL('./drivers/libcyusb_shared.so', LAZYLOAD)

""" CONSTANTS """
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
FREQREF_SOURCE = ("FRS_INTERNAL", "FRS_EXTREF", "FRS_GNSS", "FRS_USER")

""" CONNECTION METHODS """
def connect():
    """
    Search for and connect to a Tektronix RSA device. 
    
    More than 10 devices cannot be found at once. Search criteria are
    not implemented, and connection only occurs if exactly one device is
    found. Preset configuration is loaded upon connection. This results
    in: trigger mode set to Free Run, center frequency to 1.5 GHz, span
    to 40 MHz, IQ record length to 1024 samples, and reference level to
    0 dBm.

    Returns
    -------
    None

    Raises
    ------
    SDR_Error
        If no matching device is found, if more than one matching
        devices are found, or if a single device is found but connection
        fails.
    """
    numFound = c_int(0)
    devIDs = (c_int * MAX_NUM_DEVICES)()
    devSerial = ((c_char * MAX_NUM_DEVICES) * MAX_SERIAL_STRLEN)()
    devType = ((c_char * MAX_NUM_DEVICES) * MAX_DEVTYPE_STRLEN)()

    # Search for device
    rsa.DEVICE_Search(byref(numFound), devIDs, devSerial, devType)
    foundDevices = {ID: (devSerial[ID].value, devType[ID].value) for ID in \
        devIDs}

    # Ensure only a single device was found
    if numFound.value < 1:
        # Search criteria not yet implemented!!!
        raise SDR_Error(
            0,
            "Could not find a matching RSA306b",
            "Try being less restrictive in the search criteria"
        )

    if numFound.value > 1:
        err_body = "Please add/correct identifying information.\r\n"
        # Add list of found devices to error body text
        for (ID, key) in foundDevices.items():
            err_body += "\r\n{}\r\n".format(str(ID) + ": " + str(key))
        raise SDR_Error(
            1,
            "Found {} devices matching search criteria, " +
            "need exactly 1".format(numFound.value),
            err_body
        )

    # Connect to RSA306b
    try:
        rsa.DEVICE_Connect(devIDs[0])
        set_preset() # Remove later?
    except Exception as e:
        # segment is borrowed from b210 file
        # but there are better/more specific ways to catch errors
        # UNTESTED: inclusion of "e" error message in SDR_Error
        raise SDR_Error(
            2,
            "Failed to connect to RSA306b",
            "Failed to finish the initialization routine during " +
            "connection to RSA306b... {}".format(e)
        )

def disconnect():
    """
    Disconnect from a Tektronix RSA device.

    Stops data acquisition and disconnects from the connected device.

    Returns
    -------
    None
    """
    rsa.DEVICE_Disconnect()

""" CONFIG METHODS """
def get_centerFreq():
    """
    Query the center frequency.

    Returns
    -------
    float
        The center frequency, measured in Hz.
    """
    cf = c_double()
    rsa.CONFIG_GetCenterFreq(byref(cf))
    return cf.value

def get_externalRefFreq():
    """
    Query the frequency of the external reference.

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
    src = get_freqReferenceSource()
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

def get_freqReferenceSource():
    """
    Query the frequency reference source.

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

def get_maxCenterFreq():
    """
    Query the maximum center frequency.

    Returns
    -------
    float
        The maximum center frequency, measured in Hz.
    """
    maxCF = c_double()
    rsa.CONFIG_GetMaxCenterFreq(byref(maxCF))
    return maxCF.value

def get_minCenterFreq():
    """
    Query the minimum center frequency of the connected device.

    Returns
    -------
    float
        The minimum center frequency, measured in Hz.
    """
    minCF = c_double()
    rsa.CONFIG_GetMinCenterFreq(byref(minCF))
    return minCF.value

def get_referenceLevel():
    """
    Query the reference level.

    The reference level is measured in dBm, and must fall within the
    range of -130 dBm to 30 dBm.

    Returns
    -------
    float
        The reference level, measured in dBm.
    """
    refLevel = c_double()
    rsa.CONFIG_GetReferenceLevel(byref(refLevel))
    return refLevel.value

def set_preset():
    """
    Set the connected device to preset values.

    This method sets the trigger mode to Free Run, the center frequency
    to 1.5 GHz, the span to 40 MHz, the IQ record length to 1024 
    samples, and the reference level to 0 dBm.

    Returns
    -------
    None
    """
    rsa.CONFIG_Preset()

def set_centerFreq(cf):
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
    float
        New center frequency after configuration, as read from the device.
        Only returns if successful.

    Raises
    ------
    SDR_Error
        If desired center frequency is not in the allowed range.
    """
    minCF = get_minCenterFreq()
    maxCF = get_maxCenterFreq()

    if minCF <= cf <= maxCF:
        rsa.CONFIG_SetCenterFreq(c_double(cf))
        newCF = get_centerFreq()
        return newCF
    else:
        # Error has placeholder numerical ID. Update later.
        raise SDR_Error(
            0,
            "Desired center frequency not in range.",
            "Please choose a value between {} and {} Hz.".format(minCF.value,
                maxCF.value)
        )

def set_externalRefEnable(exRefEn):
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

def set_freqReferenceSource(src):
    """
    Select the device frequency reference source.

    Valid setting are FRS_INTERNAL, FRS_EXTREF, FRS_GNSS, or FRS_USER.
    Note that the RSA306 and RSA306b support only INTERNAL and EXTREF
    sources. The INTERNAL source is always a valid selection, and is
    never switched out of automatically. The EXTREF source uses the
    signal input to the Ref In connector as frequency reference for
    the internal oscillators. If EXTREF is selected without a valid
    signal connected to Ref In, the source automatically switches to
    USER if available, or to INTERNAL otherwise. The GNSS source uses
    the internal GNSS receiver to adjust the internal reference oscill-
    ator. If GNSS source is selected, the GNSS receiver must be enabled.
    If the GNSS receiver is not enabled, the source selection remains
    GNSS, but no frequency correction is done. GNSS adjusting only 
    occurs when the GNSS receiver has navigation lock. When the receiver
    is unlocked, the adjustment setting is retained unchanged until
    receiver lock is achieved or the source is switched to another
    selection. If USER source is selected, the previously set USER
    setting is used. if the USER setting has not been set, the source
    switches automatically to INTERNAL.

    Parameters
    ----------
    src : string
        Frequency reference source selection. Must be FRS_INTERNAL,
        FRS_EXTREF, FRS_GNSS, or FRS_USER.

    Returns
    -------
    None

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
            ("Please input one of: FRS_INTERNAL, FRS_EXTREF, FRS_GNSS, "
            + "or FRS_USER."))

def set_refLevel(refLevel):
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
    float
        New reference level after configuration, as read from the device. Only
        returns if successful

    Raises
    ------
    SDR_Error
        If desired reference level is not in the allowed range.
    """
    minRefLev = -130 # Min. value, dBm
    maxRefLev = 30 # Max. value, dBm
    if minRefLev <= refLevel <= maxRefLev:
        rsa.CONFIG_SetReferenceLevel(c_double(refLevel))
        # Read setting from device to confirm/return value
        newRefLev = get_referenceLevel()
        return newRefLev
    else:
        # Error has placeholder numerical ID. Update later.
        raise SDR_Error(
            0,
            "Desired reference level not in range.",
            "Please choose a value between {} and {} dBm.".format(minRefLev, maxRefLev)
        )

""" DEVICE METHODS """
def get_enable():
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

def get_fpgaVersion():
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

def get_fwVersion():
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

def get_hwVersion():
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

def get_nomenclature():
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

def get_serialNumber():
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

def get_apiVersion():
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

def get_info():
    """
    Retrieve multiple device and information strings.

    Obtained information includes: device nomenclature, serial number,
    firmware versionn, FPGA version, hardware version, and API version.

    Returns
    -------
    dict
        All of the above listed information, labeled.
    """
    nomenclature = get_nomenclature()
    serialNum = get_serialNumber()
    fwVersion = get_fwVersion()
    fpgaVersion = get_fpgaVersion()
    hwVersion = get_hwVersion()
    apiVersion = get_apiVersion()

    info = {
        "Nomenclature" : nomenclature,
        "Serial Number" : serialNum,
        "FW Version" : fwVersion,
        "FPGA Version" : fpgaVersion,
        "HW Version" : hwVersion,
        "API Version" : apiVersion
    }

    return info

def get_overTempStatus():
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

""" IQ BLOCK METHODS """
def get_iqBandwidth():
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

def get_iqRecordLength():
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

def get_iqSampleRate():
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

def get_maxIqBandwidth():
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

def get_maxIqRecordLength():
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

def get_minIqBandwidth():
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

def set_iqBandwidth(iqBandwidth):
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
    float
        New IQ bandwidth after configuration, as read from the device.
        Only returns if successful.

    Raises
    ------
    SDR_Error
        If desired IQ bandwidth is not in the allowed range.
    """
    minBandwidth = get_minIqBandwidth()
    maxBandwidth = get_maxIqBandwidth()

    if minBandwidth <= iqBandwidth <= maxBandwidth:
        rsa.IQBLK_SetIQBandwidth(c_double(iqBandwidth))
        newBandwidth = get_iqBandwidth()
        return newBandwidth
    else:
        raise SDR_Error(
            0,
            "Desired bandwidth not in range.",
            "Please choose a value between {} and {} Hz.".format(
                minBandwidth, maxBandwidth)
        )

def set_iqRecordLength(recordLength):
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
    int
        New IQ record length after configuration, as read from the device.
        Only returns if successful.

    Raises
    ------
    SDR_Error
        If desired IQ record length is not in the allowed range.
    """
    recordLength = int(recordLength)
    minIqRecLen = int(2)
    maxIqRecLen = get_maxIqRecordLength()

    if minIqRecLen <= recordLength <= maxIqRecLen:
        rsa.IQBLK_SetIQRecordLength(c_int(recordLength))
        newRecLen = get_iqRecordLength()
        return newRecLen
    else:
        raise SDR_Error(
            0,
            "Desired record length not in range.",
            "Please choose a value between {} and {} samples.".format(
                minIqRecLen, maxIqRecLen)
        )

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
    minBandwidth = c_double()
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
    """
    bwHz_act = c_double()
    srSps = c_double()
    rsa.IQSTREAM_GetAcqParameters(byref(bwHz_act), byref(srSps))
    return bwHz_act.value, srSps.value

# def IQSTREAM_GetDiskFileInfo():

# def IQSTREAM_GetDiskFileWriteStatus():
    """
    Allow monitoring the progress of file output.

    The returned values indicate when the file output has started and
    completed. These become valid after IQSTREAM_Start() is called, with
    any file output destination selected.

    Returns
    -------
    bool: isComplete
        Whether the IQ stream file output writing is complete.
    bool: isWriting
        Whether the IQ stream processing has started writing to file.
    """
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

# def IQSTREAM_GetIQData():
    """
    Retrieve IQ data blocks generated by the IQ stream processing.

    ## More info needed

    Returns
    -------
    """

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

def IQSTREAM_SetAcqBandwidth():
    """
    Set the user requested acquisition bandwidth of the output IQ data stream
    """