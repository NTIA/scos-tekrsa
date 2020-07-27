from RSA_API import *
from time import sleep

def iqstream_master(cf, refLev, bw, filename, filelength, duration):
	search_connect()
	config_iqStream(cf, refLev, bw, filename, filelength)
	run()
	print("ACQUIRING...")
	IQSTREAM_Start()
	sleep(duration)
	IQSTREAM_Stop()
	print("...DONE")
	stop()
	disconnect()

def config_iqStream(cf, refLev, bw, filename, filelength):
	setCenterFreq(cf)
	setReferenceLevel(refLev)
	IQSTREAM_SetAcqBandwidth(bw)
	IQSTREAM_SetOutputConfiguration('FILE_SIQ', 'SINGLE')
	IQSTREAM_SetDiskFilenameBase(filename)
	IQSTREAM_SetDiskFileLength(filelength)
	IQSTREAM_ClearAcqStatus()

iqstream_master(1e9, 0, 40e6, '/home/aromaniello/W/scos_tekrsa/DataTest', 0, 5)