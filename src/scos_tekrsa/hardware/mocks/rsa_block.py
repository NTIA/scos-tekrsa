""" Mock functions from RSA API that are used in SignalAnalyzerInterface. """
import numpy as np

rng = np.random.default_rng()

TIMES_TO_FAIL = 0
MIN_CENTER_FREQ = 9e3
MAX_CENTER_FREQ = 6.2e9
CENTER_FREQ = 1e9
REFERENCE_LEVEL = -30
ATTENUATION = 10
PREAMP_ENABLE = True
DEVICE_NOMENCLATURE = "Mock TekRSA"
IQSTREAM_BW = 40e6
IQSTREAM_SR = 56e6
MIN_IQ_BW = 9e3
MAX_IQ_BW = 40e6


class MockRSA:
    def __init__(self, randomize_values=False):

        # Simulate returning less than requested num samples
        self.times_to_fail = TIMES_TO_FAIL
        self.times_failed = 0
        self.randomize_values = randomize_values

    def CONFIG_GetMinCenterFreq(self):
        return MIN_CENTER_FREQ

    def CONFIG_GetMaxCenterFreq(self):
        return MAX_CENTER_FREQ

    def CONFIG_GetCenterFreq(self):
        return CENTER_FREQ

    def CONFIG_SetCenterFreq(self, val):
        return None

    def CONFIG_GetReferenceLevel(self):
        return REFERENCE_LEVEL

    def CONFIG_SetReferenceLevel(self, val):
        return None

    def CONFIG_GetRFAttenuator(self):
        return ATTENUATION

    def CONFIG_SetRFAttenuator(self, atten):
        return

    def CONFIG_SetAutoAttenuationEnable(self, en):
        return

    def CONFIG_GetRFPreampEnable(self):
        return PREAMP_ENABLE

    def CONFIG_SetRFPreampEnable(self, en):
        return

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
        return IQSTREAM_BW, IQSTREAM_SR

    def IQSTREAM_GetMinAcqBandwidth(self):
        return MIN_IQ_BW

    def IQSTREAM_GetMaxAcqBandwidth(self):
        return MAX_IQ_BW

    def IQSTREAM_SetAcqBandwidth(self, bw):
        return None

    def IQSTREAM_Tempfile_NoConfig(self, dur_msec):
        # Get n_samp from dur_msec (assuming 56e6 SR)
        n_samp = int((dur_msec / 1000) * 56e6)

        if self.times_failed < self.times_to_fail:
            self.times_failed += 1
            return np.ones(0, dtype=np.complex64)
        if self.randomize_values:
            i = rng.normal(0.5, 0.5, n_samp)
            q = rng.normal(0.5, 0.5, n_samp)
            rand_iq = np.empty(n_samp, dtype=np.complex64)
            rand_iq.real = i
            rand_iq.imag = q
            return rand_iq
        else:
            return np.ones(n_samp, dtype=np.complex64)

    def IQSTREAM_Acquire(self, dur_msec):
        self.IQSTREAM_Tempfile_NoConfig(dur_msec)

    def set_times_to_fail(self, n):
        self.times_to_fail = n
        self.times_failed = 0
