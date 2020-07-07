import numpy as np
import statsmodels.api as sm
import scipy.optimize as opt
import scipy.special as sf
import scipy.stats as stats
import scipy.integrate as integ
import matplotlib.pyplot as plt
from matplotlib import rc as mpl_rc
from matplotlib.ticker import StrMethodFormatter
from time import sleep, strftime
# The next import also loads the RSA driver and device
# It may be better to load the driver/device in this file instead
from RSA_API import *

""" PLOT FORMATTING STUFF """
mpl_rc('xtick', direction='in', top=True)
mpl_rc('ytick', direction='in', right=True)
mpl_rc('xtick.minor', visible=True)
mpl_rc('ytick.minor', visible=True)

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

# Take IQ Data FFT + Calculate M4S
def gainChar_meanFFT(iqData, power=True):
    # iqData: IQ data array

    (numFFTs, recLength) = np.shape(iqData)

    # Take FFT and normalize
    complex_fft = np.fft.fftshift(np.fft.fft(iqData))

    # Convert to psuedo-power
    complex_fft = np.square(np.abs(complex_fft))
    
    # Create the detector result
    result = np.zeros(recLength, dtype=np.float32)

    # Get mean FFT
    result = np.mean(complex_fft, axis=0)

    # Convert to power
    if power:
        impedance_factor = -10*np.log10(50)
        result = 10*np.log10(result) + impedance_factor + 30
        result -= 3 # Account for double sided FFT
        # Normalize FFT
        fft_normalization_factor = -20*np.log10(recLength)
        result += fft_normalization_factor

    return result

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
    
# Master function for gain characterization
def gain_char(minRL, maxRL, numRLs, noiseFig=False, trunc=False, trunc1=False, fftPlot=False, hist=False,
    normTest=False, enbw=False):

    # Data collection settings
    recordLength = 1024 # IQ samples per block
    numSets = 1024 # Number of IQ blocks
    cf = 3.6e9 # Center frequency
    iqBw = 40e6 # IQ Bandwidth
    
    # Create necessary variables
    compRecLen = numSets*recordLength
    refLev = np.linspace(minRL, maxRL, numRLs)
    iqArr = np.zeros((len(refLev), compRecLen), dtype=complex)
    FFTs = np.zeros((len(refLev), recordLength))
    freqArr = np.zeros((len(refLev), recordLength))

    connect()

    # Configure device
    set_centerFreq(cf)
    set_iqBandwidth(iqBw)
    set_iqRecordLength(compRecLen)

    # Generate FFT frequencies
    sampRate = get_iqSampleRate()
    freqs = generate_spectrum(cf, sampRate, recordLength)
    for i in range(len(refLev)):
        freqArr[i] = freqs

    # Collect and structure IQ data
    for (i, RL) in enumerate(refLev):
        set_refLevel(RL)
        iqArr[i] = iqblk_collect(compRecLen)
        iqSlice = np.zeros((numSets, recordLength), dtype=complex)
        for j in range(numSets):
            iqSlice[j] = iqArr[i,j*recordLength:(j+1)*recordLength]
        FFTs[i] = gainChar_meanFFT(iqSlice, power=True) # Store mean FFT
        
    disconnect()

    if trunc:
        # Truncate freq domain data to the set bandwidth (remove tails)
        lowBound = findNearest(freqArr, cf - iqBw/2)
        highBound = findNearest(freqArr, cf + iqBw/2)
        newFFTs = np.zeros((len(refLev), highBound + 1 - lowBound))
        newFreqArr = np.zeros_like(newFFTs)
        for (i, arr) in enumerate(freqArr):
            newFreqArr[i] = arr[lowBound:highBound + 1]
        for (i, FFT) in enumerate(FFTs):
            newFFTs[i] = FFT[lowBound:highBound + 1]
        # Replace existing arrays
        FFTs = newFFTs
        freqArr = newFreqArr

    if trunc1:
        # Remove first value only
        newFFTs = np.zeros((len(refLev), recordLength-1))
        newFreqArr = np.zeros((len(refLev), recordLength-1))
        newFFTs = FFTs[:,1:]
        newFreqArr = freqArr[:,1:]
        FFTs = newFFTs
        freqArr = newFreqArr

    # Calculate noise figures
    if noiseFig:
        nf = gainChar_noiseFig(freqArr, FFTs, iqArr, refLev)
        noiseFig_compPlot(nf, refLev)

    # Plot FFT:
    if fftPlot:
        gainChar_fftPlot(freqArr, FFTs, refLev, power=False)

    # Plot IQ histograms
    if hist:
        gainChar_hist(iqArr, refLev)

    # Normality tests for IQ data
    if normTest:
        gainChar_normTests(iqArr, refLev)

def gainChar_noiseFig(freqs, FFTs, IQ, refLevels):
    # Variables for calculations
    k = 1.380649e-23 # J/K, Boltzmann constant
    T = 294.261 # K, ambient temperature
    avgPwr = np.zeros_like(refLevels)
    ENBW = gainChar_ENBW(freqs, FFTs, refLevels)
    for (i, RL) in enumerate(refLevels):
        avgPwr[i] = np.mean((np.abs(IQ[i])**2)/50) # avg power, watts

    print(ENBW)

    # Calculate noise figure
    nf = avgPwr/(k*T*ENBW) # dimensionless, Watts/Watts
    nf_dBm = 10*np.log10(nf) # convert to dBm

    return nf_dBm

def noiseFig_compPlot(nf_dBm, refLevels):
    # Curve fitting
    # Model function
    def pw_model(x, x0, y0, k1, k2):
        return np.piecewise(x, [x < x0, x >= x0], [lambda x:k1*x + y0-k1*x0,
            lambda x:k2*x + y0-k2*x0])
    p0 = np.array([-30, 22, 0, 1])
    sigma_y = np.ones_like(nf_dBm) # arbitrary error...
    absErr = True
    refLevFine = np.linspace(refLevels[0], refLevels[-1], 1000) # For fit plot

    (p, C) = opt.curve_fit(pw_model, refLevels, nf_dBm, sigma=sigma_y, absolute_sigma=absErr)
    sigp = np.sqrt(np.diag(C))
    chisq = np.sum(((nf_dBm - pw_model(refLevels, *p)) ** 2)/(sigma_y ** 2))
    dof = len(nf_dBm) - len(p) # deg of freedom
    rChiSq = chisq/dof # Reduced Chisq
    Q = sf.gammaincc(0.5*dof, 0.5*chisq) # Goodness of fit

    # Print fit statistics
    print("Fit Statistics:\n"
        + "x0 = {:.3f} +/- {:.3f} dBm\n".format(p[0], sigp[0])
        + "y0 = {:.3f} +/- {:.3f}\n".format(p[1], sigp[1])
        + "m1 = {:.3f} +/- {:.3f}\n".format(p[2], sigp[2])
        + "m2 = {:.3f} +/- {:.3f}\n".format(p[3], sigp[3])
        + "Chi Squared = {:.3f}\n".format(chisq)
        + "Reduced ChiSq = {:.3f}\n".format(rChiSq)
        + "Degress of Freedom = {}\n".format(dof)
        + "Goodness of Fit = {:.3f}\n".format(Q))
        
    # Plot noise figure vs. ref level with fit
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.plot(refLevels, nf_dBm, 'k.', label="Data")
    ax.plot(refLevFine, pw_model(refLevFine, *p), 'r--',
        label="Curve Fit, Goodness of Fit = {:.3f}".format(Q))
    ax.set_xlabel("Reference Level [dBm]")
    ax.set_ylabel("Noise Figure")
    ax.set_title("Noise Figure vs. Reference Level Setting")
    ax.grid(which="major", axis="both", alpha=0.75)
    ax.grid(which="minor", axis="both", alpha=0.4)
    ax.legend()
    plt.show()

def gainChar_ENBW(freqs, FFTs, refLevels):
    # Calculates ENBWs from FFTs for various refLevels
    # Expects FFTs in power units (dBm)
    ENBW = np.zeros(len(refLevels))
    for (i, RL) in enumerate(refLevels):
        linFFT = 10**((FFTs[i]-30)/10) # Convert dBm to Watts
        integral = integ.cumtrapz(np.abs(linFFT/np.max(linFFT))**2, freqs[i])
        ENBW[i] = integral[-1]
    return ENBW

def gainChar_fftPlot(freqs, FFTs, refLevels, power=True):
    if power is False:
        for i in range(len(FFTs)):
            FFTs[i] = 10**((FFTs[i]-30)/10) # dBm to W
        y_unit = " [Watts]"
    else:
        y_unit = " [dBm]"
    fig = plt.figure()
    ax = fig.add_subplot(111)
    ax.set_xlabel("Frequency [Hz]")
    ax.set_ylabel("Power" + y_unit)
    ax.set_title("Mean Noise FFTs for Various Reference Levels")
    ax.grid(which="major", axis="both", alpha=0.75)
    ax.grid(which="minor", axis="both", alpha=0.4)
    for (i, RL) in enumerate(refLevels):
        ax.plot(freqs[i], FFTs[i], label="Ref. Level: {:.2f} dBm".format(RL))
    ax.legend()
    plt.show()

def gainChar_hist(iqData, refLevels, numBins=30):
    # Make histograms for sets of IQ samples
    # taken with various reference levels

    fig, ax = plt.subplots(len(refLevels), 3)
    ytick_fmt = StrMethodFormatter(('{x:,g}'))
    xtick_fmt = StrMethodFormatter(('{x:.3f}'))

    for (i, RL) in enumerate(refLevels):
        iData = np.real(iqData[i]) # V
        qData = np.imag(iqData[i]) # V
        pwrData = (np.abs(iqData[i])**2)/50 # W

        # I histogram
        ax[i][0].grid(which="major", axis="y", alpha=0.75)
        ax[i][0].grid(which="minor", axis="y", alpha=0.25)
        ax[i][0].hist(iData*1e3, numBins, label="Ref. Level = {:.2f} dBm".format(RL))
        ax[i][0].set_ylabel("Number")
        ax[i][0].yaxis.set_major_formatter(ytick_fmt)
        ax[i][0].xaxis.set_major_formatter(xtick_fmt)
        ax[i][0].legend()

        # Q histogram
        ax[i][1].grid(which="major", axis="y", alpha=0.75)
        ax[i][1].grid(which="minor", axis="y", alpha=0.25)
        ax[i][1].hist(qData*1e3, numBins, label="Ref. Level = {:.2f} dBm".format(RL))
        ax[i][1].yaxis.set_major_formatter(ytick_fmt)
        ax[i][1].xaxis.set_major_formatter(xtick_fmt)
        ax[i][1].legend()

        # Power histogram
        ax[i][2].grid(which="major", axis="y", alpha=0.75)
        ax[i][2].grid(which="minor", axis="y", alpha=0.25)
        ax[i][2].hist(pwrData*1e3, numBins, label="Ref. Level = {:.2f} dBm".format(RL))
        ax[i][2].yaxis.set_major_formatter(ytick_fmt)
        ax[i][2].xaxis.set_major_formatter(xtick_fmt)
        ax[i][2].legend()

    # Axis Labels
    ax[0][0].set_title("Histogram of I Data")
    ax[0][1].set_title("Histogram of Q Data")
    ax[0][2].set_title("Histogram of Power Data")
    ax[-1][0].set_xlabel("I (mV)")
    ax[-1][1].set_xlabel("Q (mV)")
    ax[-1][2].set_xlabel("Power (mW)")

    plt.gcf().subplots_adjust(bottom=0.15)
    plt.show()

def gainChar_normTests(iqData, refLevels):

    shapAlph = 0.05
    agosAlph = 0.05
    iShap, qShap = False, False
    iAgos, qAgos = False, False

    fig, ax = plt.subplots(len(refLevels), 2, figsize=(10,6))
    fig.suptitle("IQ Data QQ Plots")
    
    for (i, refLev) in enumerate(refLevels):
        iData = np.real(iqData[i])
        qData = np.imag(iqData[i])

        # Make QQ Plots
        sm.qqplot(iData, line='s', ax=ax[i][0], color='b', label="I Data")
        sm.qqplot(qData, line='s', ax=ax[i][1], color='b', label="Q Data")
        ax[i][0].set_title("I Data, RL = {} dBm".format(refLev))
        ax[i][1].set_title("Q Data, RL = {} dBm".format(refLev))

        # Shapiro-Wilk Test
        iShapStat, iShapP = stats.shapiro(iData)
        qShapStat, qShapP = stats.shapiro(qData)
        if iShapP > shapAlph:
            iShap = True
        if qShapP > shapAlph:
            qShap = True
        print("\nBeginning Normality Tests for Reference Level = {} dBm:\n".format(refLev))
        print("Shapiro-Wilk Test:\n")
        print("  I Statistic = {:.3f}\n".format(iShapStat)
            + "  I P-Value = {:.3f}\n".format(iShapP)
            + "  I Data is Gaussian: {}\n".format(str(iShap))
            + "  Q Statistic = {:.3f}\n".format(qShapStat)
            + "  Q P-Value = {:.3f}\n".format(qShapP)
            + "  Q Data is Gaussian: {}\n".format(str(qShap)))

        # D'Agostino K^2 Test
        iAgosStat, iAgosP = stats.normaltest(iData)
        qAgosStat, qAgosP = stats.normaltest(qData)
        if iAgosP > agosAlph:
            iAgos = True
        if qAgosP > agosAlph:
            qAgos = True
        print("D'Agostino K^2 Test:\n")
        print("  I Statistic = {:.3f}\n".format(iAgosStat)
            + "  I P-Value = {:.3f}\n".format(iAgosP)
            + "  I Data is Gaussian: {}\n".format(str(iAgos))
            + "  Q Statistic = {:.3f}\n".format(qAgosStat)
            + "  Q P-Value = {:.3f}\n".format(qAgosP)
            + "  Q Data is Gaussian: {}\n".format(str(qAgos)))

        # Anderson-Darling Test
        iAndersRes = stats.anderson(iData)
        qAndersRes = stats.anderson(qData)
        print("Anderson-Darling Test:\n")
        print("  I Statistic = {:.3f}".format(iAndersRes.statistic))
        for i in range(len(iAndersRes.critical_values)):
            res = iAndersRes
            sl, cv = res.significance_level[i], res.critical_values[i]
            print("    For Significance Level = {:.3f} and Critical Value = {:.3f}: ".format(sl, cv))
            if res.statistic < cv:
                print("      I Data is Gaussian")
            else:
                print("      I Data is not Gaussian")
        print("\n  Q Statistic = {:.3f}".format(qAndersRes.statistic))
        for i in range(len(qAndersRes.critical_values)):
            res = qAndersRes
            sl, cv = res.significance_level[i], res.critical_values[i]
            print("    For Significance Level = {:.3f} and Critical Value = {:.3f}: ".format(sl, cv))
            if res.statistic < cv:
                print("      Q Data is Gaussian")
            else:
                print("      Q Data is not Gaussian")

    plt.tight_layout(1.5, h_pad=1, w_pad=1)
    # For some reason, showing the QQ plots causes matplotlib to freeze
    # It still works, but temporarily disabled for this reason
    plt.show()

def findNearest(arr, val):
    # Return index of array element nearest to value
    idx = np.abs(arr - val).argmin()
    return idx

""" RUN STUFF """
#iqblk_master(1e9, 0, 40e6, 1024, plot=True, savefig=False)
#char_sampleRate()
#wifi_fft(iqBw=2.25e7)
#sr_test_fft(cf=4000e6)
#gain_char(-130, 30, 50)
#gain_char(-70, -50, 3, fftPlot=True, noiseFig=False, trunc1=True)
gain_char(-130, 30, 2, trunc=True, normTest=True)