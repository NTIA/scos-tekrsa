# 1. NTIA/ITS SCOS Tektronix RSA Plugin

This repository is a plugin to add support for the Tektronix RSA306B signal analyzer to scos-sensor. See the [scos-sensor documentation](https://github.com/NTIA/scos-sensor/blob/SMBWTB475_refactor_radio_interface/README.md) for more information about scos-sensor, especially the section about [Actions and Hardware Support](https://github.com/NTIA/scos-sensor/blob/SMBWTB475_refactor_radio_interface/DEVELOPING.md#actions-and-hardware-support).

This plugin makes use of the [Python RSA API by Tektronix](https://github.com/tektronix/RSA_API/tree/master/Python). This repository includes a wrapper for this API which masks the Ctypes dependency, handles error-checking, and implements a few helper methods.

This repository also includes many 700MHz band actions in `scos_tekrsa/configs/actions`. Action classes, RadioInterface, and signals are used from scos_actions.

For information on adding actions, see the [scos_actions documentation](https://github.com/NTIA/scos-actions/blob/PublicRelease/README.md#adding-actions).

## 2. Table of Contents

- [Overview of Repo Structure](#3-overview-of-repo-structure)
- [Running in scos-sensor](#4-running-in-scos-sensor)
- [Development](#5-development)
- [License](#6-license)
- [Contact](#7-contact)

## 3. Overview of Repo Structure

- `scos_tekrsa/configs`: This folder contains the YAML files with the parameters used to initialize the Tektronix RSA 306B supported actions and sample calibration files.
- `scos_tekrsa/discover`: This includes the code to read YAML files and make actions available to scos-sensor.
- `scos_tekrsa/hardware`: This includes the Tektronix RSA 306B implementation of the radio interface. It also includes supporting calibration and test code, along with the API wrapper.

## 4. Running in scos-sensor

Requires pip>=18.1 (upgrade using `python3 -m pip install --upgrade pip`).

Below are the steps to run scos-sensor with the scos-tekrsa plugin:

TEMPORARY NOTE: Use the SMBWTB475_refactor_radio_interface branch of scos-sensor

1. Clone scos-sensor: `git clone https://github.com/NTIA/scos-sensor.git`. 

2. Navigate to scos-sensor: `cd scos-sensor`

3. While in the scos-sensor root directory, create the `env` file by copying the template file: `cp env.template ./env`

4. In the `env` file, set `BASE_IMAGE` to `BASE_IMAGE=docker.pkg.github.com/ntia/scos-tekrsa/tekrsa_usb:0.1.2`

	- While this repository is private, [authentication with GitHub packages](https://docs.github.com/en/free-pro-team@latest/packages/using-github-packages-with-your-projects-ecosystem/configuring-docker-for-use-with-github-packages#authenticating-to-github-packages) using a [GitHub personal access token](https://docs.github.com/en/free-pro-team@latest/packages/publishing-and-managing-packages/about-github-packages#about-tokens) is required.
	- If your personal access token is stored at `~/token.txt`, this can be done by running: `cat ~/token.txt | docker login https://docker.pkg.github.com -u <GITHUB_USERNAME> --password-stdin`

5. In `scos-sensor/src/requirements.txt`, remove or comment any unnecessary dependencies (such as scos-usrp), then add the scos_tekrsa dependency: `scos_tekrsa @ git+${DOCKER_GIT_CREDENTIALS}/NTIA/scos-tekrsa@master#egg=scos_tekrsa`

6. TEMPORARY: Add `--use-deprecated=legacy-resolver` to the `pip3` command (line 24) in `scos-sensor/docker/Dockerfile-api`. This should be resolved in a future update to scos-sensor.

7. Download the [RSA API for Linux](https://www.tek.com/spectrum-analyzer/rsa306-software/rsa-application-programming-interface--api-for-64bit-linux--v100014) from Tektronix. Place the two driver files, `libRSA_API.so` and `libcyusb_shared.so`, in the directory `scos-sensor/drivers`.

8. TEMPORARY: Add `- ${REPO_ROOT}/drivers:/drivers` as a volume in the `api` section of scos-sensor's `docker-compose.yml`. This will not be necessary in the future (relevant PR for scos-sensor [here](https://github.com/NTIA/scos-sensor/pull/189))

9. Get environment variables: `source ./env`

10. Build and start containers: `docker-compose up -d --build --force-recreate`

11. Optionally, view logs: `docker-compose logs -f`

## 5. Development

### Requirements and Configuration

Requires pip>=18.1 (upgrade using `python3 -m pip install --upgrade pip`) and python>=3.6.

It is highly recommended that you first initialize a virtual development environment using a tool such as conda or venv. The following commands create a virtual environment using venv and install the required dependencies for development and testing.

```
python3 -m venv ./venv
source venv/bin/activate
python3 -m pip install --upgrade pip # upgrade to pip>=18.1
python3 -m pip install -r requirements.txt
```

### Running Tests
A docker container is used for testing. [Install Docker](https://docs.docker.com/get-docker/) in order to run tests.

```
docker build -f docker/Dockerfile -t tekrsa_usb .
docker build -f docker/Dockerfile-test -t rsa_test .
docker run rsa_test
```

## 6. License

Coming soon.

## 7. Contact

For technical questions about scos-tekrsa, contact Anthony Romaniello, aromaniello@ntia.gov