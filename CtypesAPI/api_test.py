from rsa_api import *
from time import sleep
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import rc as mpl_rc
from matplotlib.ticker import StrMethodFormatter
""" PLOT FORMATTING STUFF """
mpl_rc('xtick', direction='in', top=True)
mpl_rc('ytick', direction='in', right=True)
mpl_rc('xtick.minor', visible=True)
mpl_rc('ytick.minor', visible=True)


def cw_detect_test():
	cf = 1e9
	iqBw = 40e6
	refLev = 0
	recLen = 1024

	DEVICE_Connect()
	config_iqblk(cf, refLev, iqBw, recLen)
	iqSR = IQBLK_GetIQSampleRate()
	iqData = iqblk_collect(recLen)
	DEVICE_Disconnect()
	iqblk_plot(iqSR, recLen, iqData)


def alignTest():
	print("Running alignment...")
	ALIGN_RunAlignment()
	print("...done.")
	print("Running alignment tests...")
	print("Alignment needed:", ALIGN_GetAlignmentNeeded())
	print("Device warmed up:", ALIGN_GetWarmupStatus())

def audioTest():
	CONFIG_SetCenterFreq(99.9e6)
	CONFIG_SetReferenceLevel(-30)
	AUDIO_SetMute(False)
	AUDIO_SetVolume(1)
	AUDIO_SetMode('FM_200KHZ')
	DEVICE_Run()
	AUDIO_Start()
	data, outsize = AUDIO_GetData(100)
	AUDIO_Stop()
	DEVICE_Stop()
	print(data, outsize)

def confTest():
	print(CONFIG_GetExternalRefEnable())
	print(CONFIG_GetFrequencyReferenceSource())
	CONFIG_SetFrequencyReferenceSource('EXTREF')
	print(CONFIG_GetFrequencyReferenceSource())
	print(CONFIG_GetExternalRefFrequency())

	CONFIG_SetExternalRefEnable(True)
	print(CONFIG_GetExternalRefEnable())

# Run desired tests
# search_connect()
cw_detect_test()
# DEVICE_Disconnect()