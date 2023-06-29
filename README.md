# NTIA/ITS SCOS Tektronix® RSA Plugin

[![GitHub release (latest SemVer)][latest-release-semver-badge]][github-releases]
[![GitHub Actions Test Status][github-actions-test-badge]][github-actions-tox-link]
[![GitHub all releases][github-download-count-badge]][github-releases]
[![GitHub issues][github-issue-count-badge]][github-issues]
[![Code style: black][code-style-badge]][code-style-repo]

[NTIA/ITS]: https://its.ntia.gov/
[github-actions-tox-link]: https://github.com/NTIA/scos-tekrsa/actions/workflows/tox.yaml
[github-actions-test-badge]: https://github.com/NTIA/scos-tekrsa/actions/workflows/tox.yaml/badge.svg
[code-style-badge]: https://img.shields.io/badge/code%20style-black-000000.svg
[code-style-repo]: https://github.com/psf/black
[latest-release-semver-badge]: https://img.shields.io/github/v/release/NTIA/scos-tekrsa?display_name=tag&sort=semver
[github-releases]: https://github.com/NTIA/scos-tekrsa/releases
[github-download-count-badge]: https://img.shields.io/github/downloads/NTIA/scos-tekrsa/total
[github-issue-count-badge]: https://img.shields.io/github/issues/NTIA/scos-tekrsa
[github-issues]: https://github.com/NTIA/scos-tekrsa/issues

This repository is a plugin to add support for the Tektronix RSA306, RSA306B, RSA503A,
RSA507A, RSA513A, RSA518A, RSA603A, and RSA607A real-time spectrum analyzers to
SCOS Sensor, developed by [NTIA/ITS]. See the
[SCOS Sensor documentation](https://github.com/NTIA/scos-sensor/blob/master/README.md)
for more information about SCOS Sensor, especially the section about
[Actions and Hardware Support](https://github.com/NTIA/scos-sensor/blob/master/README.md#actions-and-hardware-support).

This plugin requires the
[RSA API for Linux](https://github.com/tektronix/RSA_API/) by Tektronix.
A custom [Python wrapper for this API](https://github.com/NTIA/tekrsa-api-wrap/) is also
used to mask Ctypes syntax, handle error-checking, and implement helper methods.

This repository also includes many 700 MHz band actions in
`scos_tekrsa/configs/actions-300` and CBRS band (3550-3700 MHz) actions in `scos_tekrsa/configs/actions-500-600`.
Actions are defined separately for RSA300- and RSA500/600-series devices, allowing for
preamp and attenuation control of the RSA500/600-series devices. Action classes,
`SignalAnalyzerInterface`, and signals are used from the [SCOS Actions Plugin](https://github.com/NTIA/scos-actions/).

For information on adding actions, see the [SCOS Actions Plugin documentation](https://github.com/NTIA/scos-actions/blob/master/README.md#adding-actions).

## Table of Contents

- [Overview of Repo Structure](#overview-of-repo-structure)
- [Running in SCOS Sensor](#running-in-scos-sensor)
- [Development](#development)
- [License](#license)
- [Contact](#contact)
- [Disclaimer](#disclaimer)

## Overview of Repo Structure

- `scos_tekrsa/configs`: Contains example calibration files and the YAML files with the
parameters used to initialize the Tektronix RSA supported actions
- `scos_tekrsa/discover`: Includes the code to read YAML files and make actions
available to `scos-sensor`
- `scos_tekrsa/hardware`: Includes an implementation of the signal analyzer interface for
Tektronix RSA devices, along with supporting test code

## Running in SCOS Sensor

Requires `git`, `python>=3.8`, `pip>=18.1`, and `pip-tools>=6.6.2`

Below are the steps to run SCOS Sensor with the SCOS Tektronix RSA plugin:

1. Clone `scos-sensor`:

    ```bash
    git clone https://github.com/NTIA/scos-sensor.git
    ```

1. Navigate to the cloned `scos-sensor` directory:

    ```bash
    cd scos-sensor
    ```

1. If testing locally, generate the necessary SSL certificates by running:

    ```bash
    cd scripts && ./create_localhost_cert.sh
    ````

1. While in the `scos-sensor` directory, create the `env` file by copying the template
file:

    ```bash
    cp env.template ./env
    ```

1. In the newly-created `env` file, set the `BASE_IMAGE`:

    ```text
    BASE_IMAGE=ghcr.io/ntia/scos-tekrsa/tekrsa_usb:latest
    ```

1. Get environment variables:

    ```bash
    source ./env
    ```

1. In `scos-sensor/src/requirements.in`, remove or comment any unnecessary dependencies
(such as `scos_usrp`), then add the `scos_tekrsa` dependency:

    ```text
    scos_tekrsa @ git+https://github.com/NTIA/scos-tekrsa@3.0.1
    ```

1. Compile requirements by running:

    ```bash
    cd src
    pip-compile requirements.in
    pip-compile requirements-dev.in
    ```

1. Download the [RSA API for Linux](https://www.tek.com/spectrum-analyzer/rsa306-software/rsa-application-programming-interface--api-for-64bit-linux--v100014)
from Tektronix. Place the three files `libRSA_API.so`, `libcyusb_shared.so`, and
`cyusb.conf` in the directory `scos-sensor/drivers`.

1. Create a `files.json` file in `scos-sensor/drivers` containing:

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

1. Build and start containers (and optionally, view logs):

    ```bash
    docker-compose build --no-cache
    docker-compose up -d --force-recreate
    docker-compose logs -f
    ```

## Development

### Development Environment

Set up a development environment using a tool like
[Conda](https://docs.conda.io/en/latest/)
or [venv](https://docs.python.org/3/library/venv.html#module-venv), with `python>=3.8`.
Then, from the cloned directory, install the development dependencies by running:

```bash
pip install .[dev]
```

This will install the project itself, along with development dependencies for pre-commit
hooks, building distributions, and running tests. Set up pre-commit, which runs
auto-formatting and code-checking automatically when you make a commit, by running:

```bash
pre-commit install
```

The pre-commit tool will auto-format Python code using [Black](https://github.com/psf/black)
and [isort](https://github.com/pycqa/isort). Other pre-commit hooks are also enabled, and
can be found in [`.pre-commit-config.yaml`](.pre-commit-config.yaml).

### Updating the `scos_tekrsa` package

This project uses [Hatchling](https://github.com/pypa/hatch/tree/master/backend) as a
backend. Hatchling makes versioning and building new releases easy. The package version can
be updated easily by using any of the following commands.

```bash
hatchling version major   # 1.0.0 -> 2.0.0
hatchling version minor   # 1.0.0 -> 1.1.0
hatchling version micro   # 1.0.0 -> 1.0.1
hatchling version "X.X.X" # 1.0.0 -> X.X.X
```

To build a new release (both wheel and sdist/tarball), run:

```bash
hatchling build
```

### Updating the `tekrsa_usb` package

To build, tag the version as X.X.X, and push the updated image to the GitHub Container
Registry, run:

```bash
docker build -f docker/Dockerfile -t tekrsa_usb .
docker tag tekrsa_usb ghcr.io/ntia/scos-tekrsa/tekrsa_usb:X.X.X
docker push ghcr.io/ntia/scos-tekrsa/tekrsa_usb:X.X.X
```

### Running Tests

The `scos_tekrsa` plugin is tested using [`tox`](https://tox.wiki/en/latest/) and the [`pytest`](https://docs.pytest.org/en/7.1.x/)
framework. The following commands can be used to run tests and show coverage reports.

```bash
pytest          # faster, but less thorough
tox             # test code in virtual environments for multiple versions of Python
tox --recreate  # To recreate the virtual environments used for testing
```

## License

See [LICENSE](LICENSE.md)

TEKTRONIX and TEK are registered trademarks of Tektronix, Inc.

## Contact

For technical questions about `scos_tekrsa`, contact Anthony Romaniello, <aromaniello@ntia.gov>

## Disclaimer

Certain commercial equipment, instruments, or materials are identified in this project
were used for the convenience of the developers. In no case does such identification
imply recommendation or endorsement by the National Telecommunications and Information
Administration, nor does it imply that the material or equipment identified is
necessarily the best available for the purpose.
