import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc as mpl_rc
from time import sleep, strftime
# The next import also loads the RSA driver and device
# It may be better to load the driver/device in this file instead
from RSA_API import *

""" PLOT FORMATTING STUFF """
mpl_rc('xtick', direction='in', labelsize='small')
mpl_rc('ytick', direction='in', labelsize='small')
mpl_rc('xtick.minor', visible=True)
mpl_rc('ytick.minor', visible=True)
mpl_rc('axes', grid=False)

""" DATA COLLECTION METHODS """

# Collect an IQ Block of data
def iqblk_collect(recordLength=1024):
    # Acquire and return IQ Block data
    # !! Configure device BEFORE calling this method
    # Input: Record length [num. of samples]
    # Returns numpy array of complex data: I+Qj

    # Record length must be an integer
    recordLength = int(recordLength)
    ready = c_bool(False)
    iqArray = c_float * recordLength
    iData = iqArray()
    qData = iqArray()
    outLength = c_int(0)

    # Begin data acquisition
    rsa.DEVICE_Run()
    rsa.IQBLK_AcquireIQData()

    # Wait for device to be ready to send data
    while not ready.value:
        # Currenty uses 100ms timeout
        rsa.IQBLK_WaitForIQDataReady(c_int(100), byref(ready))

    # Retrieve data
    rsa.IQBLK_GetIQDataDeinterleaved(byref(iData), byref(qData),
        byref(outLength), c_int(recordLength))

    # Stop device before exiting
    rsa.DEVICE_Stop()

    return np.array(iData) + 1j * np.array(qData)

# Plot an IQ data block
def iqblk_plot(time, IQ, show=True, save=False, path=".", filename="IQ_vs_Time_Plot"):
    # Plots IQ data
    # Input: Complex numpy array of (I + Qj) values

    fig = plt.figure()
    ax1 = plt.subplot(211)
    ax1.set_title('I and Q vs Time')
    ax1.plot(time, np.real(IQ), color='r')
    ax1.set_ylabel('I')
    ax1.set_xlim(0, time[-1])
    ax1.grid(which='major', axis='both', alpha=0.75)
    ax1.grid(which='minor', axis='both', alpha=0.25)
    ax2 = plt.subplot(212)
    ax2.plot(time, np.imag(IQ), color='c')
    ax2.set_ylabel('Q')
    ax2.set_xlabel('Time (s)')
    ax2.set_xlim(0, time[-1])
    ax2.grid(which='major', axis='both', alpha=0.75)
    ax2.grid(which='minor', axis='both', alpha=0.25)
    plt.tight_layout()

    # Save figure to file
    if save:
        fname = path + strftime("/%m%d%Y-%H%M%S_") + filename + '.png'
        fig.savefig(fname, dpi=300, bbox_inches='tight')

    if show:
        plt.show()

# Master function for IQ collection testing
def iqblk_master(cf=1e9, refLevel=0, iqBw=40e6, recordLength=1024, save=False,
    filename="IQ_Data", path='.', plot=False, savefig=False, figname="IQ_vs_Time_Plot"):
    # Inputs:
    # cf: Center frequency [Hz]
    # refLevel: Reference level [dBm]
    # iqBw: IQ Bandwidth [Hz] (determines sampling rate)
    # recordLength: IQ Block length [samples]
    # save: Boolean, determines if data is saved to file
    # filename: appended to timestap if saving file
    # path: prefixed to file name, use to set a path/folder
    # plot: Boolean, determines if data is plotted when 

    connect()

    # Set parameters
    set_centerFreq(cf)
    set_refLevel(refLevel)
    set_iqBandwidth(iqBw)
    set_iqRecordLength(recordLength)

    # Sample rate is determined by BW set above
    iqSampleRate = get_iqSampleRate()

    # Acquire data
    IQ = iqblk_collect(recordLength)

    disconnect()

    # Plotting
    if plot:
        # Create array of time data for plotting IQ vs time
        time = np.linspace(0, recordLength / iqSampleRate, recordLength)
        iqblk_plot(time, IQ, save=savefig, path=path, filename=figname)

    # Save data to file
    if save:
        headerInfo = ("IQ DATA FILE\nCF: " + str(cf) + " Hz, Ref. Level: "
            + str(refLevel) + " dBm, BW: " + str(iqBw) + " Hz, Rec. Length: " 
            + str(recordLength) + " samples, SR: " + str(iqSampleRate))
        fname = path + strftime("/%m%d%Y-%H%M%S_") + filename + '.txt'
        np.savetxt(fname, IQ, header=headerInfo)
    
    return IQ

# Investigation of BW vs SR
def char_sampleRate():
    connect()

    minBandwidth = get_minIqBandwidth()
    maxBandwidth = get_maxIqBandwidth()
    bwRange = np.linspace(minBandwidth, maxBandwidth, 2000)
    srRange = np.zeros_like(bwRange)

    for (i, bw) in enumerate(bwRange):
        set_iqBandwidth(bw)
        iqSr = get_iqSampleRate()
        srRange[i] = iqSr

    disconnect()

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(bwRange, srRange, 'k.')
    ax.set_xlabel("Bandwidth [Hz]")
    ax.set_ylabel("Sample Rate, [samples/s]")
    ax.set_title("IQ Sample Rate vs. Manually Set IQ Bandwidth")
    ax.grid(True, which='major', axis='both', alpha=0.75)
    ax.grid(True, which='minor', axis='both', alpha=0.25)
    plt.show()

# Take IQ Data FFT + Calculate M4S
def iq_fft(iqData):
    # iqData: IQ data array

    (numFFTs, recLength) = np.shape(iqData)

    # Take FFT and normalize
    complex_fft = np.fft.fftshift(np.fft.fft(iqData))

    # Convert to psuedo-power
    complex_fft = np.square(np.abs(complex_fft))
    
    # Create the detector result
    m4s_detected = np.zeros((5, recLength), dtype=np.float32)

    # Run detector
    m4s_detected[0] = np.min(complex_fft, axis=0)
    m4s_detected[1] = np.max(complex_fft, axis=0)
    m4s_detected[2] = np.mean(complex_fft, axis=0)
    m4s_detected[3] = np.median(complex_fft, axis=0)
    for i in range(recLength):
        m4s_detected[4][i] = complex_fft[np.random.randint(0, numFFTs)][i]

    # Convert to power
    impedance_factor = -10*np.log10(50)
    m4s_detected = 10*np.log10(m4s_detected) + impedance_factor + 30
    m4s_detected -= 3 # Account for double sided FFT

    # Normalize FFT
    fft_normalization_factor = -20*np.log10(len(m4s_detected[0]))
    m4s_detected += fft_normalization_factor

    return m4s_detected

# Generate frequency axis points for an FFT
def generate_spectrum(f0, sr, n):
    # Taken from scos_algorithm_test.lib.utils
    freqs = np.arange(n, dtype=float)
    freqs *= sr/len(freqs)
    freqs += f0 - (sr/2)
    return freqs

# WiFi Spectrum testing FFT Plotter
def fft_plot(freqData, fftData, title):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(freqData, fftData, color='r')
    ax.set_title(title)
    ax.set_ylabel('Power [dBm]')
    ax.set_xlabel('Frequency [Hz]')
    ax.set_xlim(freqData[0], freqData[-1])
    ax.grid(which='major', axis='both', alpha=0.75)
    ax.grid(which='minor', axis='both', alpha=0.25)
    plt.show()

# Master function for Wifi spectrum testing
def wifi_fft(cf=2.437e9, refLevel=-40, iqBw=40e6, recordLength=1024):
    # WIFI CHANNELS
    # 1: 2412 MHz
    # 6: 2437 MHz
    # 11: 2462 MHz

    numFFTs = 100
    iqArray = np.zeros((numFFTs, recordLength), dtype=complex)

    connect()

    print("Connected.\nTaking {} sets of IQ data...\n".format(numFFTs))

    set_centerFreq(cf)
    set_refLevel(refLevel)
    set_iqBandwidth(iqBw)
    set_iqRecordLength(recordLength)
    iqSampleRate = get_iqSampleRate()

    # Acquire Data:
    # Each row will be its own IQ data, each column its own data point
    for (num, vals) in enumerate(iqArray):
        iqArray[num] = iqblk_collect(recordLength)

    disconnect()

    print("Center Frequency: {} Hz\n".format(cf),
        "Reference Level: {} dBm\n".format(refLevel),
        "Bandwidth: {} Hz\n".format(iqBw),
        "Record Length: {} samples\n".format(recordLength),
        "Sample Rate: {} samples/sec\n".format(iqSampleRate))

    print("Constructing Mean FFT...")

    m4s_wifi = iq_fft(iqArray)
    freqPlotData = generate_spectrum(cf, iqSampleRate, recordLength)
    calcBw = freqPlotData[-1] - freqPlotData[0]
    print("Minimum Frequency: {}\n".format(freqPlotData[0]),
        "Maximum Frequency: {}\n".format(freqPlotData[-1]))
    print("Calculated BW: {}\n".format(calcBw))
    print("Full BW/Set BW: {}".format(calcBw/iqBw))
    fft_plot(freqPlotData, m4s_wifi[2], title="Mean FFT")

# Sample Rate Comparison Testing
def sr_test_plot(freqArr, meanFFTArr):
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title("Mean FFTs for Various IQ Bandwidths and Sample Rates")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Power [dBm]")
    ax.set_xlim(freqArr[-1, 0], freqArr[-1, -1])
    ax.grid(which="major", axis="both", alpha=0.75)
    ax.grid(which="minor", axis="both", alpha=0.25)
    for (i, FFT) in enumerate(meanFFTArr):
        if i == 0:
            ax.plot(freqArr[i, :], FFT, color='k', label="BW: {:.2e}, SR: {:.2e}".format(bwArray[i], srArray[i]))
        if i == 1:
            ax.plot(freqArr[i, :], FFT, color='c', label="BW: {:.2e}, SR: {:.2e}".format(bwArray[i], srArray[i]))
        if i == 2:
            ax.plot(freqArr[i, :], FFT, color='r', label="BW: {:.2e}, SR: {:.2e}".format(bwArray[i], srArray[i]))
    ax.legend(loc='best')
    plt.show()

# Master function for FFT SR investigating
def sr_test_fft(cf=2.437e9, refLevel=-60, recordLength=1024):
    #bwArray = np.array([342, 684, 1368, 2735, 5469, 10938, 21876,
    #    43760, 87600, 176000, 360000, 701000, 1.5e6, 2.9e6, 5.7e6, 1.13e7, 2.25e7])
    #bwArray = np.array([1.13e7, 1.63e7, 2.13e7])
    bwArray = np.array([5.7e6, 1.13e7, 2.25e7])
    srArray = np.zeros_like(bwArray)

    numFFTs = 1000
    meanFFTArr = np.zeros((len(bwArray), recordLength))
    freqArr = np.zeros_like(meanFFTArr)
    #iqArray = np.zeros((numFFTs, recordLength), dtype=complex)

    connect()

    set_centerFreq(cf)
    set_refLevel(refLevel)

    for (i, bw) in enumerate(bwArray):
        set_iqBandwidth(bw)
        set_iqRecordLength(recordLength)
        srArray[i] = get_iqSampleRate()
        iqArray = np.zeros((numFFTs, recordLength), dtype=complex)
        for (num, vals) in enumerate(iqArray):
            iqArray[num] = iqblk_collect(recordLength)
        m4s_temp = iq_fft(iqArray)
        meanFFTArr[i] = m4s_temp[2]
        freqArr[i] = generate_spectrum(cf, srArray[i], recordLength)

    disconnect()

    sr_test_plot(freqArr, meanFFTArr)

# FFT plotting for gain characterization
def gainChar_test_plot(freqArr, meanFFTArr, refLevArr, iqBw, cf):

    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_title("Mean FFTs for Various Reference Levels")
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Power [dBm]")
    ax.set_xlim(cf - iqBw/2, cf + iqBw/2)
    ax.set_ylim(-120, -110)
    ax.grid(which="major", axis="both", alpha=0.75)
    ax.grid(which="minor", axis="both", alpha=0.25)

    for (i, FFT) in enumerate(meanFFTArr):
        avgPwr = np.mean(FFT)
        ax.plot(freqArr[i, :], FFT, label="Ref. Level: {} dBm, Mean Power: {:.3f} dBm".format(refLevArr[i], avgPwr))
    ax.legend(loc='lower center')
    plt.show()
    
# Master function for gain characterization
def gain_char(minRL, maxRL, numRLs, cf=3e9, numFFTs=5000, recordLength=1024):

    compRecLen = numFFTs*recordLength
    iqBw = 40e6
    #refLevArr = np.array([-130, 30])
    refLevArr = np.linspace(minRL, maxRL,numRLs)

    meanFFTArr = np.zeros((len(refLevArr), recordLength))
    freqArr = np.zeros_like(meanFFTArr)

    connect()

    set_centerFreq(cf)
    set_iqBandwidth(iqBw)
    set_iqRecordLength(compRecLen)
    sampRate = get_iqSampleRate()

    for (i, refLev) in enumerate(refLevArr):
        set_refLevel(refLev)
        iqArray = np.zeros(compRecLen, dtype=complex)
        iqArray = iqblk_collect(compRecLen)
        iqSlice = np.zeros((numFFTs, recordLength), dtype=complex)
        for j in range(numFFTs):
            iqSlice[j] = iqArray[j*recordLength:(j+1)*recordLength]
        m4s_temp = iq_fft(iqSlice)
        meanFFTArr[i] = m4s_temp[2]
        freqArr[i] = generate_spectrum(cf, sampRate, recordLength)

    disconnect()

    gainChar_test_plot(freqArr, meanFFTArr, refLevArr, iqBw, cf)
    # set various ref levels (start with just max and min)
    # for each, record 50 IQ blocks
    # get average FFT for each ref level
    # make I data histogram for each ref level

def theoryNoise(bw, T=294.261):
    # Calculates thermal noise power
    # T: temp, kelvin
    # bw: bandwidth, Hz
    # Returns noise power in dBm
    k = 1.380649e-23 # J/K
    P_dBm = 10*np.log10(k*T*bw)
    return P_dBm

""" RUN STUFF """
iqblk_master(1e9, 0, 40e6, 1024, plot=True, savefig=False)
#char_sampleRate()
#wifi_fft(iqBw=2.25e7)
#sr_test_fft(cf=4000e6)


#gain_char(-130, -100, 4)
#gain_char(-100, -70, 4)
#gain_char(-70, -40, 4)
#gain_char(-40, -10, 4)
#gain_char(-10, 30, 5)