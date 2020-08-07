scos_tekrsa
============

Tektronix RSA support for [`scos-sensor`](https://github.com/NTIA/scos-sensor). Currently WIP.

This will eventually become a plugin which adds support for the [Tektronix RSA306b](https://www.tek.com/spectrum-analyzer/rsa306) into [`scos-sensor`](https://github.com/NTIA/scos-sensor). It will also be possible to relatively easily extend this code to support a wider range of Tektronix RSA devices which use the same API: the RSA306, RSA500A series, and RSA600A series real time spectrum analyzers. 

Brief Overview of Repo Structure
--------------------------------

- `scos_tekrsa` and the top level directory contain the main files which will incorporate the RSA into `scos-sensor`. Right now, there isn't much here, but this will be the main content of this repository when finished. Most of what is present is borrowed from [`scos_usrp`](https://github.com/NTIA/scos_usrp) and will be replaced or adapted soon.

- `Ctypes API` contains a custom-made Python wrapper for the RSA API.
	- The `RSA_API.py` file contains Python methods which wrap API calls in order to make them more Pythonic and easier to use. This wrapper handles data type conversions under the hood, so you can interface with the RSA using standard Python data types, instead of worrying about converting to the proper C data types for every function call. API calls are documented using a standard docstring format to allow for quick reference of API functionality in a development environment.

- `Cython API` contains another version of the API, which is currently not functional. This version is forked from the Tektronix [Cython RSA API](https://github.com/tektronix/RSA_API/tree/master/Python/Cython%20Version), with adaptations made to the `setup.py` file in order to run on Linux. There are some limitations to this version of the API, as documented in the [`README`](https://github.com/NTIA/scos_tekrsa/blob/master/Cython%20API/README.md). Also, it currently has errors which cause the module it compiles not to import into a Python script. This makes it currently unusable, although in the future this may be fixed and used instead of the Ctypes version. This version likely runs faster than the Ctypes implementation.

Usage
-----
As of right now, only the custom Ctypes API is worth trying to use. If you do wish to try it out, here's the way to go about it.

Clone this repository (or just the `Ctypes API` folder), and connect the RSA306b to your computer via a USB 3.0 port. Then, you can start by writing your own code to control the RSA 306b.

To start writing your own RSA script, create a new Python file in the cloned `Ctypes API` directory, and start out by importing the RSA API at the beginning of the file:

```python
from RSA_API import *
```

Next you can get started by making API calls. The first thing you might want to do is simply connect to, then disconnect from, the device. If no errors are thrown, everything is working well!

To do this, simply add to your code:

```python
search_connect()
DEVICE_Disconnect()
```

Now you can get started using other API calls. The methods within `RSA_API.py` are documented using a standard docstring format, which should be enough information to get going. The Ctypes API [`README`](https://github.com/NTIA/scos_tekrsa/blob/master/Ctypes%20API/README.md) might also be helpful.

Questions/Comments
------------------
Anthony Romaniello | NTIA/Institute for Telecommunication Sciences | aromaniello@ntia.gov