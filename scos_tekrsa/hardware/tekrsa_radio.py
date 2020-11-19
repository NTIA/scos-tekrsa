import logging
import time

import numpy as np

from scos_actions import utils
from scos_actions.hardware.radio_iface import RadioInterface

from scos_tekrsa import settings
from scos_tekrsa.hardware.driver.rsa_api import *

# Calibration not yet performed but these should be the right imports,
# or at least a decent starting point based on the keysight/usrp versions.
# For now, everything calibration-related is commented out where possible,
# or replaced by placeholder code where needed.

# from scos_tekrsa.hardware import calibration
# from scos_tekrsa.hardware.calibration import (
#     DEFAULT_SENSOR_CALIBRATION,
#     DEFAULT_SIGAN_CALIBRATION
# )

logger = logging.getLogger(__name__)

class RSARadio(RadioInterface):

    def __init__(
        self,
        # sensor_cal_file=settings.SENSOR_CALIBRATION_FILE,
        # sigan_cal_file=settings.SIGAN_CALIBRATION_FILE,
    ):
        self._is_available = False

        # Allowed SR's: 56e6, 28e6, 14e6, ...
        self.ALLOWED_SR = []
        # Allowed BW's : 40e6, 20e6, 10e6, ...
        self.ALLOWED_BW = []

        self.max_sample_rate = 56.0e6
        self.max_reference_level = 30 # dBm, constant
        self.min_reference_level = -130 # dBm, constant
        self.max_frequency = None
        self.min_frequency = None
        
        allowed_sample_rate = self.max_sample_rate # maximum cardinal SR
        allowed_acq_bw = 40.0e6 # maximum corresponding BW

        while allowed_sample_rate > 13670.0:
            # Note: IQ Block acquisition allows for lower SR's. This
            # loop adds only the SR's available for BOTH IQ block and
            # IQ streaming acquisitions.
            self.ALLOWED_SR.append(allowed_sample_rate)
            self.ALLOWED_BW.append(allowed_acq_bw)
            allowed_acq_bw /= 2
            allowed_sample_rate /= 2

        # Create SR/BW mapping dictionary
        # With SR as keys, BW as values
        self.sr_bw_map = {self.ALLOWED_SR[i] : self.ALLOWED_BW[i] for i in range(len(self.ALLOWED_SR))}
        
        self.sensor_calibration_data = None
        self.sigan_calibration_data = None
        self.sensor_calibration = None
        self.sigan_calibration = None

        self.connect()
        # self.get_calibration(sensor_cal_file, sigan_cal_file)

    def get_constraints(self):
        self.min_frequency = CONFIG_GetMinCenterFreq()
        self.max_frequency = CONFIG_GetMaxCenterFreq()

    def connect(self):
        if self._is_available:
            return True

        search_connect()

        logger.debug("Using the following Tektronix RSA device:")
        logger.debug(DEVICE_GetNomenclature())

        try:
            self.get_constraints()
        except ImportError:
            logger.warning("Tektronix RSA API not available - disabling radio")
            return False

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
    # Not commented since it isn't called in current implementation.
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
        return IQSTREAM_GetAcqParameters()[1]

    @sample_rate.setter
    def sample_rate(self, sample_rate):
        if sample_rate > self.max_sample_rate:
            err_msg = f"Sample rate {sample_rate} too high. Max sample rate is {self.max_sample_rate}."
            logger.error(err_msg)
            raise Exception(err_msg)
        if sample_rate not in self.ALLOWED_SR:
            allowed_sample_rates_str = ", ".join(self.ALLOWED_SR)
            err_msg = (f"Requested sample rate {sample_rate} not in allowed sample rates."
                + " Allowed sample rates are {allowed_sample_rates_str}")
            logger.error(err_msg)
            raise Exception(err_msg)
        # set bandwidth according to SR setting
        bw = self.sr_bw_map.get(sample_rate)
        IQSTREAM_SetAcqBandwidth(bw)
        msg = "set Tektronix RSA sample rate: {:.1f} samples/sec"
        logger.debug(msg.format(IQSTREAM_GetAcqParameters()[1]))

    @property
    def frequency(self):
        return CONFIG_GetCenterFreq()

    @frequency.setter
    def frequency(self, freq):
        CONFIG_SetCenterFreq(freq)

    @property
    def reference_level(self):
        return CONFIG_GetReferenceLevel()
        msg = "Set Tektronix RSA center frequency: {:.1f} Hz"
        logger.debug(msg.format(CONFIG_GetCenterFreq()))

    @reference_level.setter
    def reference_level(self, reference_level):
        CONFIG_SetReferenceLevel(reference_level)
        msg = "Set Tektronix RSA reference level: {:.1f} dB"
        logger.debug(msg.format(CONFIG_GetReferenceLevel()))

    # revist the following section once all setpoints implemented
    # and calibration stuff is figured out

    @property
    def last_calibration_time(self):
        if self.sensor_calibration:
            return utils.convert_string_to_millisecond_iso_format(
                self.sensor_calibration.calibration_datetime
            )
        return None

    def recompute_calibration_data(self):
        """Set the calibration data based on the currently tuning"""

        # Try and get the sensor calibration data
        self.sensor_calibration_data = DEFAULT_SENSOR_CALIBRATION.copy()
        if self.sensor_calibration is not None:
            self.sensor_calibration_data.update(
                self.sensor_calibration.get_calibration_dict(
                    sample_rate=self.sample_rate,
                    lo_frequency=self.frequency,
                    attenuation=self.attenuation,
                )
            )

        # Try and get the sigan calibration data
        self.sigan_calibration_data = DEFAULT_SIGAN_CALIBRATION.copy()
        if self.sigan_calibration is not None:
            self.sigan_calibration_data.update(
                self.sigan_calibration.get_calibration_dict(
                    sample_rate=self.sample_rate,
                    lo_frequency=self.frequency,
                    attenuation=self.attenuation,
                )
            )

        # Catch any defaulting calibration values for the sigan
        if self.sigan_calibration_data["gain_sigan"] is None:
            self.sigan_calibration_data["gain_sigan"] = 0
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
        # While calibration isn't yet done, return placeholder info
        # This was needed for testing, pre-calibration.
        calDone = False
        if calDone:
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
        else:
            annotation_md = {
                "ntia-core:annotation_type": "CalibrationAnnotation",
                "ntia-sensor:gain_sigan": 1,
                "ntia-sensor:noise_figure_sigan": 1,
                "ntia-sensor:1db_compression_point_sigan": 1,
                "ntia-sensor:enbw_sigan": 1,
                "ntia-sensor:gain_preselector": 1,
                "ntia-sensor:noise_figure_sensor": 1,
                "ntia-sensor:1db_compression_point_sensor": 1,
                "ntia-sensor:enbw_sensor": 1,
            }
        return annotation_md

    def configure(self, action_name):
        pass

    @property
    def healthy(self):
        time_info = None
        try:
            with Utils.sensor(ip_address=KEYSIGHT_IP) as sensor:
                time_info = SystemInfo.get_sensor_time(sensor)
        except SensorConnectionException:
            logger.error("healthy: Unable to connect to Keysight sensor")
            return False
        return time_info.timestampSeconds != 0

    # Handle taking IQ samples
    def acquire_time_domain_samples(self, num_samples, num_samples_skip=0, retries=5):
        logger.debug(
            f"acquire_time_domain_samples starting num_samples = {num_samples}"
        )
        # Determine correct time length for num_samples based on current SR
        durationMsec = int((num_samples/self.sample_rate)*1000)
        # Calibration data not currently recomputed since calibration not done
        #self.recompute_calibration_data()
        #db_gain = self.sensor_calibration_data["gain_sensor"]
        # Placeholder db_gain:
        db_gain = 1
        logger.debug(f"Number of retries = {retries}")
        
        # Compute the linear gain
        linear_gain = 10 ** (db_gain / 20.0)
        total_samples = num_samples + num_samples_skip
        while True:
            try:
                result_data = iqstream_tempfile(self.frequency, self.reference_level,
                    self.sr_bw_map[self.sample_rate], durationMsec
                )
                received_samples = len(result_data)
                if received_samples < total_samples:
                    logger.warning(
                        f"Only {received_samples} samples received. Expected {total_samples} samples."
                    )
                    if retries > 0:
                        logger.info("Retrying time domain iq measurement.")
                        retries = retries - 1
                        continue
                    else:
                        error_message = "Max retries exceeded."
                        logger.error(error_message)
                        raise RuntimeError(error_message)
                data = result_data[num_samples_skip : received_samples + num_samples_skip]
                data /= linear_gain

                measurement_result = {
                    "data": data,
                    "overload": False, # overload check occurs automatically after measurement
                    "frequency": self.frequency,
                    "reference_level": self.reference_level,
                    "sample_rate": IQSTREAM_GetAcqParameters()[1],
                    "capture_time": durationMsec, # capture duration in milliseconds
                    "calibration_annotation": self.create_calibration_annotation()
                }
                return measurement_result
            except Exception as e:
                logger.error(e)
                if retries > 0:
                    logger.info("Retrying time domain iq measurement.")
                    retries = retries - 1
                    continue
                else:
                    error_message = "Max retries exceeded."
                    logger.error(error_message)
                    raise RuntimeError(error_message)