"""
Generate and TX chirp samples in a continuous wave
Requires initial and final frequencies for frequency sweep
"""

import argparse
import numpy as np
import uhd
from distutils.version import StrictVersion

waveforms = {
    "sine": lambda n, tone_offset, rate: np.exp(n * 2j * np.pi * tone_offset / rate),
    "square": lambda n, tone_offset, rate: np.sign(waveforms["sine"](n, tone_offset, rate)),
    "const": lambda n, tone_offset, rate: 1 + 1j,
    "ramp": lambda n, tone_offset, rate:
            2*(n*(tone_offset/rate) - np.floor(float(0.5 + n*(tone_offset/rate))))
}

def parse_args():
    """Parse the command line arguments"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--args", default="", type=str)
    parser.add_argument(
        "-w", "--waveform", default="sine", choices=waveforms.keys(), type=str)
    parser.add_argument("-f0", "--freq0", type=float, required=True)
    parser.add_argument("-f1", "--freq1", type=float, required=True)
    parser.add_argument("-s", "--save", type=bool, default=False)
    parser.add_argument("-o", "--output-file", type=str, default=None)
    parser.add_argument("-r", "--rate", default=10e6, type=float)
    parser.add_argument("-d", "--duration", default=5, type=float)
    parser.add_argument("-c", "--channels", default=0, nargs="+", type=int)
    parser.add_argument("-g", "--gain", type=int, default=10)
    parser.add_argument("--wave-freq", default=1e4, type=float)
    parser.add_argument("--wave-ampl", default=0.3, type=float)
    parser.add_argument("-n", "--numpy", default=False, action="store_true",
                        help="Save output file in NumPy format (default: No)")
    return parser.parse_args()


def create_IQdata():
    args = parse_args()
    T = 10e-3
    if not isinstance(args.channels, list):
        args.channels = [args.channels]
    # frequency interval
    interval = (args.freq1 - args.freq0) / T
    phase = np.zeros(int(T * args.rate))
    for i in range(int(T * args.rate)):
        # time interval
        x = i / args.rate
        phase[i] = 2 * np.pi * (((interval / 2) * (x * x)) + args.freq0 * x)
    Idata = [np.sin(x) for x in phase]
    Qdata = [np.cos(x) for x in phase]
    data = np.array([complex(x, y) for x, y in zip(Idata, Qdata)], dtype=np.complex64)
    return data


def main():
    # """TX samples based on input arguments"""
    args = parse_args()
    # T = 10e-3
    # usrp = uhd.usrp.MultiUSRP(args.args)
    if not isinstance(args.channels, list):
         args.channels = [args.channels]
    # #frequency interval
    # interval = (args.freq1-args.freq0)/T
    # phase = np.zeros(int(T*args.rate))
    # for i in range(int(T*args.rate)):
    #     # time interval
    #     x = i/args.rate
    #     phase[i] = 2*np.pi*(((interval/2)*(x*x))+args.freq0*x)
    # Idata = [np.sin(x) for x in phase]
    # Qdata = [np.cos(x) for x in phase]
    # data = np.array([complex(x,y) for x,y in zip(Idata,Qdata)], dtype=np.complex64)

    #save IQdata
    usrp = uhd.usrp.MultiUSRP(args.args)

    data = create_IQdata()
    if args.save:
        if args.output_file == None:
            print("Could not save IQ data, please specify a file name")
        else:
            with open(args.output_file, 'wb') as out_file:
               if args.numpy:
                    np.save(out_file, data, allow_pickle=False, fix_imports=False)
               else:
                   data.tofile(out_file)

    print("Press Ctrl+C to end transmission")
    # send transmission
    usrp.send_waveform(data, args.duration, args.freq1, args.rate, args.channels, args.gain)

if __name__ == "__main__":
    main()