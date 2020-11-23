# 1. NTIA/ITS SCOS TekRSA Plugin

This repository is a plugin to add support for the Tektronix RSA306B signal analyzer to scos-sensor. See the [scos-sensor documentation]() for more information about scos-sensor, especially the section about [Actions and Hardware Support]().

See scos_tekrsa/hardware/drivers/README.md 

This repository includes many 700MHz band actions in scos_tekrsa/configs/actions. Action classes, RadioInterface, and signals are used from scos_actions.

For information on adding actions, see the [scos_actions documentation]().

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

4. Make sure the scos-tekrsa dependency is in requirements.txt in the scos-sensor/src folder. If you are using a different branch than master, change master in the following line to the branch you are using 

## 5. Development



## 6. License

See [LICENSE](LICENSE.md)

## 7. Contact

For technical questions about scos-tekrsa, contact Anthony Romaniello, aromaniello@ntia.gov