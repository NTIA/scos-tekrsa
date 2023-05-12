"""
These are constants which are relevant for ALL supported Tektronix RSA devices.
The values are obtained from the RSA API Programming Manual provided by Tektronix.
"""

IQSTREAM_ALLOWED_SR = [  # Samples/sec
    56.0e6,
    28.0e6,
    14.0e6,
    7.0e6,
    3.5e6,
    1.75e6,
    875.0e3,
    437.5e3,
    218.75e3,
    109.375e3,
    54687.5,
    24373.75,
    13671.875,
]

IQSTREAM_ALLOWED_BW = [  # Hz
    40.0e6,
    20.0e6,
    10.0e6,
    5.0e6,
    2.5e6,
    1.25e6,
    625.0e3,
    312.5e3,
    156.25e3,
    78125.0,
    39062.5,
    19531.25,
    9765.625,
]

IQSTREAM_SR_BW_MAP = dict(zip(IQSTREAM_ALLOWED_SR, IQSTREAM_ALLOWED_BW))
IQSTREAM_BW_SR_MAP = dict(zip(IQSTREAM_ALLOWED_BW, IQSTREAM_ALLOWED_SR))

MAX_REFERENCE_LEVEL = 30  # dBm
MIN_REFERENCE_LEVEL = -130  # dBm

MAX_ATTENUATION = 51  # dB
MIN_ATTENUATION = 0  # dB
