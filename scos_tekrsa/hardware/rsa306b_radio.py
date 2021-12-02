import logging
import time

import numpy as np
from scos_actions import utils
from scos_actions.hardware.radio_iface import RadioInterface

from scos_tekrsa import settings
from scos_tekrsa.hardware import calibration
from scos_tekrsa.hardware.mocks.rsa_block import MockRSA
from scos_tekrsa.hardware.tests.resources.utils import create_dummy_calibration
from scos_tekrsa.hardware.calibration import (
    DEFAULT_SENSOR_CALIBRATION,
    DEFAULT_SIGAN_CALIBRATION
)

logger = logging.getLogger(__name__)

class RSA306BRadio(RadioInterface):

    def __init__(
        self,
        sensor_cal_file=settings.SENSOR_CALIBRATION_FILE,
        sigan_cal_file=settings.SIGAN_CALIBRATION_FILE
    ):
        self.rsa_api = None
        self.rsa = None
        self._is_available = False

        # Allowed sample rates and bandwidth settings for RSA306B,
        # ordered from greatest to least. SR in samples/sec, BW in Hz.
        self.ALLOWED_SR = [56.0e6, 28.0e6, 14.0e6, 7.0e6, 3.5e6, 1.75e6, 875.e3,
                           437.5e3, 218.75e3, 109.375e3, 54687.5, 24373.75, 13671.875]

        self.ALLOWED_BW = [40.0e6, 20.0e6, 10.0e6, 5.0e6, 2.5e6, 1.25e6, 625.e3,
                           312.5e3, 156.25e3, 78125., 39062.5, 19531.25, 9765.625]
        
        # Use values defined above to create SR/BW mapping dict,
        # with SR as keys and BW as values.
        self.sr_bw_map = dict(zip(self.ALLOWED_SR, self.ALLOWED_BW))

        self.max_sample_rate = self.ALLOWED_SR[0]
        self.max_reference_level = 30 # dBm, constant
        self.min_reference_level = -130 # dBm, constant
        self.max_frequency = None
        self.min_frequency = None
        
        self.sensor_calibration_data = None
        self.sigan_calibration_data = None
        self.sensor_calibration = None
        self.sigan_calibration = None
        self._capture_time = None

        self.connect()
        self.get_calibration(sensor_cal_file, sigan_cal_file)

    def get_constraints(self):
        self.min_frequency = self.rsa.CONFIG_GetMinCenterFreq()
        self.max_frequency = self.rsa.CONFIG_GetMaxCenterFreq()

    def connect(self):
        # Device already connected
        if self._is_available:
            return

        if settings.RUNNING_TESTS or settings.MOCK_RADIO:
            # Mock radio if desired
            random = settings.MOCK_RADIO_RANDOM
            self.rsa = MockRSA(randomize_values=random)
        else:
            try:
                # Load API wrapper
                import rsa_api as api_wrap
                self.rsa_api = api_wrap
            except ImportError:
                logger.warning("API Wrapper not loaded - disabling radio.")
                self._is_available = False
                return
            try:
                self.rsa = self.rsa_api.RSA()
                # Connect to device using API wrapper
                self.rsa.DEVICE_SearchAndConnect()
                self.align()
                self.get_constraints()
            except Exception as e:
                logger.exception(e)
                return

        logger.debug("Using the following Tektronix RSA device:")
        logger.debug(self.rsa.DEVICE_GetNomenclature())

        self._is_available = True
        

    def align(self, retries=3):
        """Check if device alignment is needed, and if so, run it."""
        while True:
            try:
                if self.rsa.ALIGN_GetWarmupStatus(): # Must be warmed up first
                    if self.rsa.ALIGN_GetAlignmentNeeded():
                        self.rsa.ALIGN_RunAlignment()
                        return
                    else:
                        logger.debug("Device already aligned.")
                else:
                    logger.debug("Device not yet warmed up.")
                return
            except Exception as e:
                logger.error(e)
                if retries > 0:
                    logger.info("Waiting 5 seconds before retrying device alignment...")
                    retries = retries - 1
                    time.sleep(5)
                    continue
                else:
                    error_message = "Max retries exceeded."
                    logger.error(error_message)
                    raise RuntimeError(error_message)


    @property
    def is_available(self):
        return self._is_available

    def get_calibration(self, sensor_cal_file, sigan_cal_file):
        """Get calibration data from sensor_cal_file and sigan_cal_file."""
        # Set the default calibration values
        self.sensor_calibration_data = DEFAULT_SENSOR_CALIBRATION.copy()
        self.sigan_calibration_data = DEFAULT_SIGAN_CALIBRATION.copy()

        # Try and load sensor/sigan calibration data
        if not settings.RUNNING_TESTS and not settings.MOCK_RADIO:
            try:
                self.sensor_calibration = calibration.load_from_json(sensor_cal_file)
            except Exception as e:
                logger.error(
                    "Unable to load sensor calibration data, reverting to none."
                )
                logger.exception(e)
                self.sensor_calibration = None
            try:
                self.sigan_calibration = calibration.load_from_json(sigan_cal_file)
            except Exception as e:
                logger.error("Unable to load sigan calibration data, reverting to none.")
                logger.exception(e)
                self.sigan_calibration = None
        else:  # If in testing, create our own test files
            dummy_calibration = create_dummy_calibration()
            self.sensor_calibration = dummy_calibration
            self.sigan_calibration = dummy_calibration

    @property
    def sample_rate(self):
        return self.rsa.IQSTREAM_GetAcqParameters()[1]

    @sample_rate.setter
    def sample_rate(self, sample_rate):
        """Set the device sample rate and bandwidth."""
        if sample_rate > self.max_sample_rate:
            err_msg = f"Sample rate {sample_rate} too high. Max sample rate is {self.max_sample_rate}."
            logger.error(err_msg)
            raise Exception(err_msg)
        if sample_rate not in self.ALLOWED_SR:
            # If requested sample rate is not an allowed value
            allowed_sample_rates_str = ", ".join(map(str, self.ALLOWED_SR))
            err_msg = (f"Requested sample rate {sample_rate} not in allowed sample rates."
                + f" Allowed sample rates are {allowed_sample_rates_str}")
            logger.error(err_msg)
            raise ValueError(err_msg)
        # Set RSA IQ Bandwidth based on sample_rate
        # The IQ Bandwidth determines the RSA sample rate.
        bw = self.sr_bw_map.get(sample_rate)
        self.rsa.IQSTREAM_SetAcqBandwidth(bw)
        msg = "set Tektronix RSA 306B sample rate: {:.1f} samples/sec"
        logger.debug(msg.format(self.rsa.IQSTREAM_GetAcqParameters()[1]))

    @property
    def frequency(self):
        return self.rsa.CONFIG_GetCenterFreq()

    @frequency.setter
    def frequency(self, freq):
        """Set the device center frequency."""
        self.rsa.CONFIG_SetCenterFreq(freq)
        msg = "Set Tektronix RSA 306B center frequency: {:.1f} Hz"
        logger.debug(msg.format(self.rsa.CONFIG_GetCenterFreq()))

    @property
    def reference_level(self):
        return self.rsa.CONFIG_GetReferenceLevel()

    @reference_level.setter
    def reference_level(self, reference_level):
        """Set the device reference level."""
        self.rsa.CONFIG_SetReferenceLevel(reference_level)
        msg = "Set Tektronix RSA 306B reference level: {:.1f} dB"
        logger.debug(msg.format(self.rsa.CONFIG_GetReferenceLevel()))

    @property
    def last_calibration_time(self):
        """Return the last calibration time from calibration data."""
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
                    reference_level=self.reference_level,
                )
            )

        # Try and get the sigan calibration data
        self.sigan_calibration_data = DEFAULT_SIGAN_CALIBRATION.copy()
        if self.sigan_calibration is not None:
            self.sigan_calibration_data.update(
                self.sigan_calibration.get_calibration_dict(
                    sample_rate=self.sample_rate,
                    lo_frequency=self.frequency,
                    reference_level=self.reference_level,
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
        """Create the SigMF calibration annotation."""
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

    @property
    def healthy(self, num_samples=100000):
        """Perform health check by collecting IQ samples."""
        logger.debug("Performing Tektronix RSA 306B health check.")

        try:
            measurement_result = self.acquire_time_domain_samples(num_samples)
            data = measurement_result["data"]
        except Exception as e:
            logger.error("Unable to acquire samples from RSA device.")
            logger.error(e)
            return False
        
        if not len(data) == num_samples:
            logger.error("RSA data doesn't match request.")
        
        return True


    def acquire_time_domain_samples(self, num_samples, num_samples_skip=0, retries=5):
        """Acquire specific number of time-domain IQ samples."""
        self._capture_time = None
        nsamps_req = int(num_samples) # Requested number of samples
        nskip = int(num_samples_skip) # Requested number of samples to skip
        nsamps = nsamps_req + nskip # Total number of samples to collect

        # Get calibration data for acquisition
        self.recompute_calibration_data()

        # Compute the linear gain
        db_gain = self.sensor_calibration_data["gain_sensor"]
        linear_gain = 10 ** (db_gain / 20.0)
        
        # Determine correct time length for num_samples based on current SR
        durationMsec = int(1000*(nsamps/self.sample_rate))
        
        if durationMsec == 0:
            # Num. samples requested is less than minimum duration for IQ stream.
            # Handle this by skipping more samples than requested
            durationMsec = 1 # Minimum allowed IQ stream duration
            nskip = int((self.sample_rate/1000) - nsamps_req)
            nsamps = nskip + nsamps_req

        logger.debug(f"acquire_time_domain_samples starting, num_samples = {nsamps}")
        logger.debug(f"Number of retries = {retries}")

        max_retries = retries

        while True:
            self._capture_time = utils.get_datetime_str_now()
            data = self.rsa.IQSTREAM_Tempfile(
                                self.frequency, self.reference_level,
                                self.sr_bw_map[self.sample_rate], durationMsec
                          )
   
            data = data[nskip:]
            data_len = len(data)

            if not data_len == nsamps_req:
                if retries > 0:
                    msg = "RSA error: requested {} samples, but got {}."
                    logger.warning(msg.format(nsamps_req + nskip, data_len))
                    logger.warning("Retrying {} more times.".format(retries))
                    retries -= 1
                else:
                    err = "Failed to acquire correct number of samples "
                    err += "{} times in a row.".format(max_retries)
                    raise RuntimeError(err)
            else:
                logger.debug("Successfully acquired {} samples.".format(data_len))
            
                # Scale data to RF power and return
                data /= linear_gain

                measurement_result = {
                    "data": data,
                    "overload": False, # overload check occurs automatically after measurement
                    "frequency": self.frequency,
                    "reference_level": self.reference_level,
                    "sample_rate": self.rsa.IQSTREAM_GetAcqParameters()[1],
                    "capture_time": self._capture_time,
                    "calibration_annotation": self.create_calibration_annotation()
                }
                return measurement_result
