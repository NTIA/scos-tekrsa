Tektronix RSA306b scos Testing
==============================

Building a Python interface for the Tektronix RSA API which will eventually be used to integrate the [Tektronix RSA306b](https://www.tek.com/spectrum-analyzer/rsa306) into [`scos-sensor`](https://github.com/NTIA/scos-sensor). At the moment, this repository serves mostly as a backup for in-progress code while the RSA306b is characterized. Eventually, it will morph into a plugin which adds RSA support into `scos-sensor`. It will also be possible to relatively easily extend this code to support a larger variety of devices in the Tektronix RSA line of real time spectrum analyzers.

Brief Overview of Files
-----------------------

- `RSA_API.py` contains Python implementations of commands that are a part of the Tektronix RSA API, which is implemented in C. It makes use of `ctypes` as well as a few shared object files, and essentially serves to abstract API calls for easier use in other Python scripts.

- `testbed.py` is, well, exactly that. This is where I'm currently writing various methods used for different tests and characterizations of the RSA306b. It is a temporary file, and is a little messier as a result.

- `drivers` contains the two shared object files required to interface with the RSA. These are loaded up within `RSA_API.py`.

- `SDR_Error.py` is a simple class, borrowed from [`sdrcalibrator`](https://github.com/NTIA/sdrcalibrator/) which is used to handle errors.

Usage
-----
As mentioned, this code isn't really ready for any real usage. If you do wish to try it out, though, here's the way to go about it.

Clone this repository, and connect the RSA306b to your computer via a USB 3.0 port. Then, you can either run the testbed code (not necessarily recommended), or start by writing your own code (recommended).

To run the testbed code, open a terminal in the directory where you cloned the repository. Run `python3 testbed.py`. That's it! Keep in mind that the testbed file is unpredictable in function, as it is updated to run different tests, and in functionality, as I may commit something that's currently not working.

To start writing your own RSA script, create a new Python file in the cloned directory, and start out by importing the RSA API at the beginning of the file:

`from RSA_API import *`

Next you can get started by making API calls. The first thing you might want to do is simply connect to, then disconnect from, the device. If no errors are thrown, everything is working well!

To do this, simply add to your code:

```
connect()
disconnect()
```

Now you can get started using other API calls. The methods within `RSA_API.py` are documented using the standard Python docstring format, which should be enough information to get going.

Questions/Comments
------------------
Anthony Romaniello | NTIA/Institute for Telecommunication Sciences | aromaniello@ntia.gov