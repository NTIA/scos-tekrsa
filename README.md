# NTIA/ITS SCOS Tektronix® RSA Plugin[^disclaimer]

This repository is a plugin to add support for the Tektronix RSA306, RSA306B, RSA503A,
RSA507A, RSA513A, RSA518A, RSA603A, and RSA607A real-time spectrum analyzers to
scos-sensor. See the
[scos-sensor documentation](https://github.com/NTIA/scos-sensor/blob/master/README.md)
for more information about scos-sensor, especially the section about
[Actions and Hardware Support](https://github.com/NTIA/scos-sensor/blob/master/README.md#actions-and-hardware-support).

This plugin makes use of the
[RSA API by Tektronix](https://github.com/tektronix/RSA_API/).
A custom [Python wrapper for this API](https://github.com/NTIA/tekrsa-api-wrap/) is also
used to mask Ctypes syntax, handle error-checking, and implement helper methods.

This repository also includes many 700MHz band actions in
`scos_tekrsa/configs/actions-300` and CBRS band actions in `scos_tekrsa/configs/actions-500-600`.
Actions are defined separately for RSA300- and RSA500/600-series devices, allowing for
preamp and attenuation control of the RSA500/600-series devices. Action classes,
`SignalAnalyzerInterface`, and signals are used from [scos_actions](https://github.com/NTIA/scos-actions/).

For information on adding actions, see the [scos_actions documentation](https://github.com/NTIA/scos-actions/blob/master/README.md#adding-actions).

## Table of Contents

- [Overview of Repo Structure](#overview-of-repo-structure)
- [Running in scos-sensor](#running-in-scos-sensor)
- [Development](#development)
- [License](#license)
- [Contact](#contact)

## Overview of Repo Structure

- `scos_tekrsa/configs`: This folder contains the YAML files with the parameters used to
initialize the Tektronix RSA supported actions and sample calibration files.
- `scos_tekrsa/discover`: This includes the code to read YAML files and make actions
available to `scos-sensor`.
- `scos_tekrsa/hardware`: This includes the Tektronix RSA implementation of the signal
analyzer interface. It also includes supporting test code.

## Running in scos-sensor

Requires `pip>=18.1` (upgrade using `python3 -m pip install --upgrade pip`).

Below are the steps to run scos-sensor with the scos-tekrsa plugin:

1. Clone scos-sensor: `git clone https://github.com/NTIA/scos-sensor.git`.

2. Navigate to scos-sensor: `cd scos-sensor`
    - While testing locally, run: `cd scripts && ./create_localhost_cert.sh` to generate
    the necessary SSL certificates.

3. While in the scos-sensor root directory, create the `env` file by copying the template
file: `cp env.template ./env`

4. In the `env` file, set `BASE_IMAGE` to `BASE_IMAGE=ghcr.io/ntia/scos-tekrsa/tekrsa_usb:0.1.5`

5. In `scos-sensor/src/requirements.in`, remove or comment any unnecessary dependencies
(such as `scos_usrp`), then add the `scos_tekrsa` dependency:

    `scos_tekrsa @ git+https://github.com/NTIA/scos-tekrsa@1.0.0`

6. Compile `requirements.txt` by running: `pip-compile requirements.in`

7. Download the [RSA API for Linux](https://www.tek.com/spectrum-analyzer/rsa306-software/rsa-application-programming-interface--api-for-64bit-linux--v100014)
from Tektronix. Place the three files `libRSA_API.so`, `libcyusb_shared.so`, and
`cyusb.conf` in the directory `scos-sensor/drivers`.

8. Create a `files.json` file in `scos-sensor/drivers` containing:

    ```json
    {
        "scos_files": [
            {
                "source_path": "cyusb.conf",
                "dest_path": "/etc/cyusb.conf"
            }
        ]
    }
    ```

9. Get environment variables: `source ./env`

10. Build and start containers: `docker-compose up -d --build --force-recreate`

11. Optionally, view logs: `docker-compose logs -f`

## Development

### Updating the `tekrsa_usb` package

To build, tag the version as X.X.X, and push the updated image to the GitHub Container
Registry, run:

```bash
docker build -f docker/Dockerfile -t tekrsa_usb .
docker tag tekrsa_usb ghcr.io/ntia/scos-tekrsa/tekrsa_usb:X.X.X
docker push ghcr.io/ntia/scos-tekrsa/tekrsa_usb:X.X.X
```

### Requirements and Configuration

Requires `pip>=18.1` (upgrade using `python3 -m pip install --upgrade pip`) and `python>=3.7`.

It is highly recommended that you first initialize a virtual development environment
using a tool such as conda or venv. The following commands create a virtual environment
using venv and install the required dependencies for development and testing.

```bash
python3 -m venv ./venv
source venv/bin/activate
python3 -m pip install --upgrade pip # upgrade to pip>=18.1
python3 -m pip install -r requirements.txt
```

#### Using `pip-tools`

It is recommended to keep direct dependencies in a separate file. The direct
dependencies are in the `requirements.in` and `requirements-dev.in` files. Then `pip-tools`
can be used to generate files with all the dependencies and transitive dependencies
(sub-dependencies). The files containing all the dependencies are in `requirements.txt` and
`requirements-dev.txt`. Run the following in the virtual environment to install `pip-tools`:

```bash
python3 -m pip install pip-tools
```

To update `requirements.txt` after modifying `requirements.in`:

```bash
pip-compile requirements.in
```

To update `requirements-dev.txt` after modifying `requirements-dev.in`:

```bash
pip-compile requirements-dev.in
```

Use `pip-sync` to match virtual environment to `requirements-dev.txt`:

```bash
pip-sync requirements.txt requirements-dev.txt
```

For more information about `pip-tools`, see [https://pip-tools.readthedocs.io/en/latest/#](https://pip-tools.readthedocs.io/en/latest/#)

### Running Tests

A Docker container is used for testing. [Install Docker](https://docs.docker.com/get-docker/)
in order to run tests.

```bash
docker build -f docker/Dockerfile-test -t rsa_test .
docker run rsa_test
```

## License

See [LICENSE](LICENSE.md)

TEKTRONIX and TEK are registered trademarks of Tektronix, Inc.

## Contact

For technical questions about `scos_tekrsa`, contact Anthony Romaniello, aromaniello@ntia.gov

### Disclaimer

[^disclaimer]: Certain commercial equipment, instruments, or materials are identified in this project were used for the convenience of the developers. In no case does such identification imply recommendation or endorsement by the National Telecommunications and Information Administration, nor does it imply that the material or equipment identified is necessarily the best available for the purpose.
