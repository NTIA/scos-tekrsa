""" Mock functions from RSA API that are used in RadioInterface. """
from numpy import linspace

class MockRSA:
	def __init__(self, randomize_values=False):
		
		# Simulate returning less than requested num samples
		self.times_to_fail_recv = 0
		self.times_failed_recv = 0

	def CONFIG_GetMinCenterFreq(self):
		return 9.0e3

	def CONFIG_GetMaxCenterFreq(self):
		return 6.2e9

	def CONFIG_GetCenterFreq(self):
		return 1.0e9

	def CONFIG_SetCenterFreq(self, val):
		return None

	def CONFIG_GetReferenceLevel(self):
		return 0.

	def CONFIG_SetReferenceLevel(self, val):
		return None

	def DEVICE_SearchAndConnect(self, verbose=False):
		return None

	def DEVICE_GetNomenclature(self):
		return "MOCKED RSA306B"

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

	def IQSTREAM_Tempfile(self, cf, refLev, bw, dur_msec):
		n_samp = int((dur_msec/1000)*56e6)
		i = linspace(0, 100, num=n_samp)
		q = linspace(1, 101, num=n_samp)
		iq = i + 1j*q
		print("MOCK RETURNS LENGTH________:{}".format(len(iq)))
		return iq
