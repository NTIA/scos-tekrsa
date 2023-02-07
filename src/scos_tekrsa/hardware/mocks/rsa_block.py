""" Mock functions from RSA API that are used in RadioInterface. """
import numpy as np


class MockRSA:
    def __init__(self, randomize_values=False):
        # Simulate returning less than requested num samples
        self.times_to_fail = 0
        self.times_failed = 0
        self.randomize_values = randomize_values

    def CONFIG_GetMinCenterFreq(self):
        return 9.0e3

    def CONFIG_GetMaxCenterFreq(self):
        return 6.2e9

    def CONFIG_GetCenterFreq(self):
        return 1.0e9

    def CONFIG_SetCenterFreq(self, val):
        return None

    def CONFIG_GetReferenceLevel(self):
        return 0.0

    def CONFIG_SetReferenceLevel(self, val):
        return None

    def DEVICE_SearchAndConnect(self, verbose=False):
        return None

    def DEVICE_GetNomenclature(self):
        return "MOCK RSA507A"

    def ALIGN_GetWarmupStatus(self):
        return True

    def ALIGN_GetAlignmentNeeded(self):
        return True

    def ALIGN_RunAlignment(self):
        return None

    def IQSTREAM_GetAcqParameters(self):
        return 40.0e6, 56.0e6

    def IQSTREAM_SetAcqBandwidth(self, bw):
        return None

    def IQSTREAM_Tempfile_NoConfig(self, dur_msec):
        # Get n_samp from dur_msec (assuming 56e6 SR)
        n_samp = int((dur_msec / 1000) * 56e6)

        if self.times_failed < self.times_to_fail:
            self.times_failed += 1
            return np.ones(0, dtype=np.complex64)
        if self.randomize_values:
            i = np.random.normal(0.5, 0.5, n_samp)
            q = np.random.normal(0.5, 0.5, n_samp)
            rand_iq = np.empty(n_samp, dtype=np.complex64)
            rand_iq.real = i
            rand_iq.imag = q
            return rand_iq
        else:
            return np.ones(n_samp, dtype=np.complex64)

    def set_times_to_fail(self, n):
        self.times_to_fail = n
        self.times_failed = 0
