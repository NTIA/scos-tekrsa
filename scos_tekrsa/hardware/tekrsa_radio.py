import logging
import time

import numpy as np

from scos_actions import utils
from scos_actions.hardware.radio_iface import RadioInterface

from scos_tekrsa import settings

# Calibration not yet performed but these should be the right imports
# or at least a decent starting point based on the keysight/usrp versions

# Nothing that references calibration works yet
from scos_tekrsa.hardware import calibration
from scos_tekrsa.hardware.calibration import (
    DEFAULT_SENSOR_CALIBRATION,
    DEFAULT_SIGAN_CALIBRATION
)

# RSA API import happens in connect method

logger = logging.getLogger(__name__)

class RSARadio(RadioInterface):

    # Allowed SR's: 56e6, 28e6, 14e6, ...
    ALLOWED_SAMPLE_RATES = []

    # Allowed BW's : 40e6, 20e6, 10e6, ...
    ALLOWED_ACQ_BW = []

    def __init__(
        self,
        sensor_cal_file=settings.SENSOR_CALIBRATION_FILE,
        sigan_cal_file=settings.SIGAN_CALIBRATION_FILE,
    ):
        self._is_available = False
        
        allowed_sr = 56.0e6 # maximum cardinal SR
        allowed_acq_bw = 40.0e6 # maximum corresponding BW

        while allowed_sr > 13670.0:
            # Note: IQ Block acquisition allows for lower SR's. This
            # loop adds only the SR's available for BOTH IQ block and
            # IQ streaming acquisitions.
            self.ALLOWED_SAMPLE_RATES.append(allowed_sr)
            self.ALLOWED_ACQ_BW.append(allowed_acq_bw)
            allowed_acq_bw /= 2
            allowed_sr /= 2

        # Create SR/BW mapping dictionary
        # With SR as keys, BW as values
        sr_bw_map = {allowed_sr[i] : allowed_acq_bw for i in range(len(allowed_sr))}

        self.max_sample_rate = allowed_sr
        self.max_reference_level = 30 # dBm, constant
        self.min_reference_level = -130 # dBm, constant
        self.max_frequency = None
        self.min_frequency = None
        
        self.sensor_calibration_data = None
        self.sigan_calibration_data = None
        self.sensor_calibration = None
        self.sigan_calibration = None

        self.connect()
        # self.get_calibration(sensor_cal_file, sigan_cal_file)

    def get_constraints(self):
        self.min_frequency = self.CONFIG_GetMinCenterFreq()
        self.max_frequency = self.CONFIG_GetMaxCenterFreq()

    def connect(self):
        if self._is_available:
            return True

        try:
            from rsa_api import *
            self.get_constraints()
        except ImportError:
            logger.warning("Tektronix RSA API not available - disabling radio")
            return False

        self.search_connect()

        logger.debug("Using the following Tektronix RSA device:")
        logger.debug(self.DEVICE_GetNomenclature())

        try:
            self._is_available = True
            return True
        except Exception as err:
            logger.exception(err)
            return False

    @property
    def is_available(self):
        return self._is_available

    # get_calibration left untouched from USRP implementation so far
    def get_calibration(self, sensor_cal_file, sigan_cal_file):
        # Set the default calibration values
        self.sensor_calibration_data = DEFAULT_SENSOR_CALIBRATION.copy()
        self.sigan_calibration_data = DEFAULT_SIGAN_CALIBRATION.copy()

        # Try and load sensor/sigan calibration data
        if not settings.RUNNING_TESTS and not settings.MOCK_RADIO:
            try:
                self.sensor_calibration = calibration.load_from_json(sensor_cal_file)
            except Exception as err:
                logger.error(
                    "Unable to load sensor calibration data, reverting to none"
                )
                logger.exception(err)
                self.sensor_calibration = None
            try:
                self.sigan_calibration = calibration.load_from_json(sigan_cal_file)
            except Exception as err:
                logger.error("Unable to load sigan calibration data, reverting to none")
                logger.exception(err)
                self.sigan_calibration = None
        else:  # If in testing, create our own test files
            # from scos_usrp import hardware as test_utils

            dummy_calibration = create_dummy_calibration()
            self.sensor_calibration = dummy_calibration
            self.sigan_calibration = dummy_calibration

    @property
    def sample_rate(self):
        return self.IQSTREAM_GetAcqParameters()[1]

    @sample_rate.setter
    def sample_rate(self, sample_rate):
        if sample_rate > self.max_sample_rate:
            err_msg = f"Sample rate {sample_rate} too high. Max sample rate is {self.max_sample_rate}."
            logger.error(err_msg)
            raise Exception(err_msg)
        if sample_rate not in self.ALLOWED_SAMPLE_RATES:
            allowed_sample_rates_str = ", ".join(self.ALLOWED_SAMPLE_RATES)
            err_msg = (f"Requested sample rate {sample_rate} not in allowed sample rates."
                + " Allowed sample rates are {allowed_sample_rates_str}")
            logger.error(err_msg)
            raise Exception(err_msg)
        # set bandwidth according to SR setting
        bw = sr_bw_map.get(sample_rate)
        self.IQSTREAM_SetAcqBandwidth(bw)
        logger.debug(f"Sample rate: {self.sample_rate}")

    @property
    def frequency(self):
        return self.CONFIG_GetCenterFreq()

    @frequency.setter
    def frequency(self, freq):
        self.CONFIG_SetCenterFreq()

    @property
    def reference_level(self):
        return self.CONFIG_GetReferenceLevel()

    @reference_level.setter
    def reference_level(self, reference_level):
        self.CONFIG_SetReferenceLevel(reference_level)
        msg = "set Tektronix RSA reference level: {:.1f} dB"
        logger.debug(msg.format(self.CONFIG_GetReferenceLevel()))

    # revist the following section once all setpoints implemented
    # and calibration stuff is figured out

    def recompute_calibration_data(self):
        """Set the calibration data based on the currently tuning"""

        # Try and get the sensor calibration data
        self.sensor_calibration_data = DEFAULT_SENSOR_CALIBRATION.copy()
        if self.sensor_calibration is not None:
            self.sensor_calibration_data.update(
                self.sensor_calibration.get_calibration_dict(
                    sample_rate=self.sample_rate,
                    lo_frequency=self.frequency,
                    gain=self.gain,
                )
            )

        # Try and get the sigan calibration data
        self.sigan_calibration_data = DEFAULT_SIGAN_CALIBRATION.copy()
        if self.sigan_calibration is not None:
            self.sigan_calibration_data.update(
                self.sigan_calibration.get_calibration_dict(
                    sample_rate=self.sample_rate,
                    lo_frequency=self.frequency,
                    gain=self.gain,
                )
            )

        # Catch any defaulting calibration values for the sigan
        if self.sigan_calibration_data["gain_sigan"] is None:
            self.sigan_calibration_data["gain_sigan"] = self.gain
        if self.sigan_calibration_data["enbw_sigan"] is None:
            self.sigan_calibration_data["enbw_sigan"] = self.sample_rate

        # Catch any defaulting calibration values for the sensor
        if self.sensor_calibration_data["gain_sensor"] is None:
            self.sensor_calibration_data["gain_sensor"] = self.sigan_calibration_data[
                "gain_sigan"
            ]
        if self.sensor_calibration_data["enbw_sensor"] is None:
            self.sensor_calibration_data["enbw_sensor"] = self.sigan_calibration_data[
                "enbw_sigan"
            ]
        if self.sensor_calibration_data["noise_figure_sensor"] is None:
            self.sensor_calibration_data[
                "noise_figure_sensor"
            ] = self.sigan_calibration_data["noise_figure_sigan"]
        if self.sensor_calibration_data["1db_compression_sensor"] is None:
            self.sensor_calibration_data["1db_compression_sensor"] = (
                self.sensor_calibration_data["gain_preselector"]
                + self.sigan_calibration_data["1db_compression_sigan"]
            )

    def create_calibration_annotation(self):
        annotation_md = {
            "ntia-core:annotation_type": "CalibrationAnnotation",
            "ntia-sensor:gain_sigan": self.sigan_calibration_data["gain_sigan"],
            "ntia-sensor:noise_figure_sigan": self.sigan_calibration_data[
                "noise_figure_sigan"
            ],
            "ntia-sensor:1db_compression_point_sigan": self.sigan_calibration_data[
                "1db_compression_sigan"
            ],
            "ntia-sensor:enbw_sigan": self.sigan_calibration_data["enbw_sigan"],
            "ntia-sensor:gain_preselector": self.sensor_calibration_data[
                "gain_preselector"
            ],
            "ntia-sensor:noise_figure_sensor": self.sensor_calibration_data[
                "noise_figure_sensor"
            ],
            "ntia-sensor:1db_compression_point_sensor": self.sensor_calibration_data[
                "1db_compression_sensor"
            ],
            "ntia-sensor:enbw_sensor": self.sensor_calibration_data["enbw_sensor"],
        }
        return annotation_md

    def configure(self, action_name):
        pass

    def check_sensor_overload(self, data):
        measured_data = data.astype(np.complex64)
        time_domain_avg_power = 10 * np.log10(np.mean(np.abs(measured_data) ** 2))
        time_domain_avg_power += (
            10 * np.log10(1 / (2 * 50)) + 30
        )  # Convert log(V^2) to dBm
        self._sensor_overload = False
        # explicitly check is not None since 1db compression could be 0
        if self.sensor_calibration_data["1db_compression_sensor"] is not None:
            self._sensor_overload = (
                time_domain_avg_power
                > self.sensor_calibration_data["1db_compression_sensor"]
            )

    def acquire_time_domain_samples(
        self, num_samples, num_samples_skip=0, retries=5
    ):  # -> np.ndarray:
        """Aquire num_samples_skip+num_samples samples and return the last num_samples"""
        self._sigan_overload = False
        self._capture_time = None
        # Get the calibration data for the acquisition
        self.recompute_calibration_data()

        # Compute the linear gain
        db_gain = self.sensor_calibration_data["gain_sensor"]
        linear_gain = 10 ** (db_gain / 20.0)

        # Try to acquire the samples
        max_retries = retries
        while True:
            # No need to skip initial samples when simulating the radio
            if settings.RUNNING_TESTS or settings.MOCK_RADIO:
                nsamps = num_samples
            else:
                nsamps = num_samples + num_samples_skip

            self._capture_time = utils.get_datetime_str_now()
            samples = self.usrp.recv_num_samps(
                nsamps,  # number of samples
                self.frequency,  # center frequency in Hz
                self.sample_rate,  # sample rate in samples per second
                [0],  # channel list
                self.gain,  # gain in dB
            )
            # usrp.recv_num_samps returns a numpy array of shape
            # (n_channels, n_samples) and dtype complex64
            assert samples.dtype == np.complex64
            assert len(samples.shape) == 2 and samples.shape[0] == 1
            data = samples[0]  # isolate data for channel 0
            data_len = len(data)

            if not settings.RUNNING_TESTS:
                data = data[num_samples_skip:]

            if not len(data) == num_samples:
                if retries > 0:
                    msg = "USRP error: requested {} samples, but got {}."
                    logger.warning(msg.format(num_samples + num_samples_skip, data_len))
                    logger.warning("Retrying {} more times.".format(retries))
                    retries = retries - 1
                else:
                    err = "Failed to acquire correct number of samples "
                    err += "{} times in a row.".format(max_retries)
                    raise RuntimeError(err)
            else:
                logger.debug("Successfully acquired {} samples.".format(num_samples))
`
                # Check IQ values versus ADC max for sigan compression
                self._sigan_overload = False
                i_samples = np.abs(np.real(data))
                q_samples = np.abs(np.imag(data))
                i_over_threshold = np.sum(i_samples > self.ADC_FULL_RANGE_THRESHOLD)
                q_over_threshold = np.sum(q_samples > self.ADC_FULL_RANGE_THRESHOLD)
                total_over_threshold = i_over_threshold + q_over_threshold
                ratio_over_threshold = float(total_over_threshold) / num_samples
                if ratio_over_threshold > self.ADC_OVERLOAD_THRESHOLD:
                    self._sigan_overload = True

                # Scale the data back to RF power and return it
                data /= linear_gain
                return data
