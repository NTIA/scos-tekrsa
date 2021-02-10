# Mock functions from RSA API that are used in RadioInterface
from numpy import linspace

def CONFIG_GetMinCenterFreq():
	return 9.0e3

def CONFIG_GetMaxCenterFreq():
	return 6.2e9

def CONFIG_GetCenterFreq():
	return 1.0e9

def CONFIG_SetCenterFreq(val):
	return None

def CONFIG_GetReferenceLevel():
	return 0.

def CONFIG_SetReferenceLevel(val):
	return None

def DEVICE_SearchAndConnect(verbose=False):
	return None

def DEVICE_GetNomenclature():
	return "MOCKED RSA306B"

def ALIGN_GetWarmupStatus():
	return True

def ALIGN_GetAlignmentNeeded():
	return True

def ALIGN_RunAlignment():
	return None

def IQSTREAM_GetAcqParameters():
	return 40.0e6, 56.0e6

def IQSTREAM_SetAcqBandwidth(bw):
	return None

def IQSTREAM_Tempfile(cf, refLev, bw, dur_msec):
	n_samp = (dur_msec/1000)*56e6
	i = linspace(0, 100, num=n_samp)
	q = linspace(1, 101, num=n_samp)
	iq = i + 1j*q
	return iq
