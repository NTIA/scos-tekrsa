# 1. NTIA/ITS SCOS TekRSA Plugin

This repository is a plugin to add support for the Tektronix RSA306B signal analyzer to scos-sensor. See the [scos-sensor documentation](https://github.com/NTIA/scos-sensor/blob/SMBWTB475_refactor_radio_interface/README.md) for more information about scos-sensor, especially the section about [Actions and Hardware Support](https://github.com/NTIA/scos-sensor/blob/SMBWTB475_refactor_radio_interface/DEVELOPING.md#actions-and-hardware-support).

See scos_tekrsa/hardware/drivers/README.md 

This repository includes many 700MHz band actions in scos_tekrsa/configs/actions. Action classes, RadioInterface, and signals are used from scos_actions.

For information on adding actions, see the [scos_actions documentation](https://github.com/NTIA/scos-actions/blob/PublicRelease/README.md#adding-actions).

## 2. Table of Contents

- [Overview of Repo Structure](#3-overview-of-repo-structure)
- [Running in scos-sensor](#4-running-in-scos-sensor)
- [Development](#5-development)
- [License](#6-license)
- [Contact](#7-contact)

## 3. Overview of Repo Structure

- scos_tekrsa/configs: This folder contains the YAML files with the parameters used to initialize the Tektronix RSA 306B supported actions and sample calibration files.
- scos_tekrsa/discover: This includes the code to read YAML files and make actions available to scos-sensor.
- scos_tekrsa/hardware: This includes the Tektronix RSA 306B implementation of the radio interface. It also includes supporting calibration and test code.

## 4. Running in scos-sensor

Requires pip>=18.1 (upgrade using `python3 -m pip install --upgrade pip`).

Below are the steps to run scos-sensor with the scos-tekrsa plugin:

1. Clone scos-sensor: `git clone https://github.com/NTIA/scos-sensor.git`

2. Navigate to scos-sensor: `cd scos-sensor`

3. If it does not exist, create env file while in the root scos-sensor directory `cp env.template ./env`

4. Make sure the scos-tekrsa dependency is in requirements.txt in the scos-sensor/src folder. If you are using a different branch than master, change master in the following line to the branch you are using: `scos_tekrsa @ git+${DOCKER_GIT_CREDENTIALS}/NTIA/scos-tekrsa@master#egg=scos_tekrsa`

	- Additionally, remove or comment any unnecessary dependencies, such as scos-usrp.

5. Make sure `BASE_IMAGE` is set to `BASE_IMAGE=docker.pkg.github.com/ntia/scos-tekrsa/tekrsa_usb:0.1.0` in the env file

	- While this repository is private, [authentication with GitHub packages](https://docs.github.com/en/free-pro-team@latest/packages/using-github-packages-with-your-projects-ecosystem/configuring-docker-for-use-with-github-packages#authenticating-to-github-packages) using a [GitHub personal access token](https://docs.github.com/en/free-pro-team@latest/packages/publishing-and-managing-packages/about-github-packages#about-tokens) is required. 

6. Get environment variables: `source ./env`

7. Build and start containers: `docker-compose up -d --build --force-recreate`

8. Optionally, view logs: `docker-compose logs -f`

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

## 6. License

Coming Soon

## 7. Contact

For technical questions about scos-tekrsa, contact Anthony Romaniello, aromaniello@ntia.gov