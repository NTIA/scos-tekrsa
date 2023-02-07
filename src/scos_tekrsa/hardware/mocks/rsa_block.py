""" Mock functions from RSA API that are used in SignalAnalyzerInterface. """
import numpy as np

from scos_tekrsa.hardware.tekrsa_constants import IQSTREAM_BW_SR_MAP

rng = np.random.default_rng()

TIMES_TO_FAIL = 0

# Mock Signal Analyzer Constants
DEVICE_NOMENCLATURE = "MOCK RSA507A"
MIN_CENTER_FREQ = 9e3
MAX_CENTER_FREQ = 6.2e9
MIN_IQ_BW = 9e3
MAX_IQ_BW = 40e6

# Default values
IQSTREAM_BW = 40e6
IQSTREAM_SR = 56e6
CENTER_FREQ = 1e9
REFERENCE_LEVEL = -30
ATTENUATION = 10
PREAMP_ENABLE = True


class MockRSA:
    def __init__(self, randomize_values=False):

        # Simulate returning less than requested num samples
        self.times_to_fail = TIMES_TO_FAIL
        self.times_failed = 0
        self.randomize_values = randomize_values

        # Initialize parameters
        self._frequency = CENTER_FREQ
        self._reference_level = REFERENCE_LEVEL
        self._iq_bandwidth = IQSTREAM_BW
        self._sample_rate = IQSTREAM_SR
        self._attenuation = ATTENUATION
        self._preamp_enable = PREAMP_ENABLE

    def CONFIG_GetMinCenterFreq(self):
        return MIN_CENTER_FREQ

    def CONFIG_GetMaxCenterFreq(self):
        return MAX_CENTER_FREQ

    def CONFIG_GetCenterFreq(self):
        return self._frequency

    def CONFIG_SetCenterFreq(self, val):
        self._frequency = val

    def CONFIG_GetReferenceLevel(self):
        return self._reference_level

    def CONFIG_SetReferenceLevel(self, val):
        self._reference_level = val

    def CONFIG_GetRFAttenuator(self):
        return self._attenuation

    def CONFIG_SetRFAttenuator(self, val):
        self._attenuation = val

    def CONFIG_SetAutoAttenuationEnable(self, en):
        return

    def CONFIG_GetRFPreampEnable(self):
        return self._preamp_enable

    def CONFIG_SetRFPreampEnable(self, en):
        self._preamp_enable = en

    def DEVICE_SearchAndConnect(self, verbose=False):
        return None

    def DEVICE_GetNomenclature(self):
        return DEVICE_NOMENCLATURE

    def ALIGN_GetWarmupStatus(self):
        return True

    def ALIGN_GetAlignmentNeeded(self):
        return True

    def ALIGN_RunAlignment(self):
        return None

    def IQSTREAM_GetAcqParameters(self):
        return self._iq_bandwidth, self._sample_rate

    def IQSTREAM_GetMinAcqBandwidth(self):
        return MIN_IQ_BW

    def IQSTREAM_GetMaxAcqBandwidth(self):
        return MAX_IQ_BW

    def IQSTREAM_SetAcqBandwidth(self, bw):
        self._iq_bandwidth = bw
        self._sample_rate = IQSTREAM_BW_SR_MAP[self._iq_bandwidth]

    def IQSTREAM_Tempfile_NoConfig(self, dur_msec, return_status):
        # Get n_samp from dur_msec
        n_samp = int((dur_msec / 1000) * self.IQSTREAM_GetAcqParameters()[1])

        if self.times_failed < self.times_to_fail:
            self.times_failed += 1
            iq = np.ones(0, dtype=np.complex64)
            return np.ones(0, dtype=np.complex64)
        if self.randomize_values:
            i = rng.normal(0.5, 0.5, n_samp)
            q = rng.normal(0.5, 0.5, n_samp)
            rand_iq = np.empty(n_samp, dtype=np.complex64)
            rand_iq.real = i
            rand_iq.imag = q
            iq = rand_iq
        else:
            iq = np.ones(n_samp, dtype=np.complex64)
        if return_status:
            return iq, "No error."
        else:
            return iq

    def IQSTREAM_Acquire(self, dur_msec, return_status):
        return self.IQSTREAM_Tempfile_NoConfig(dur_msec, return_status)

    def set_times_to_fail(self, n):
        self.times_to_fail = n
        self.times_failed = 0
