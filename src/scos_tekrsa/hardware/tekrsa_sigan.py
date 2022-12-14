import logging
import threading

from scos_actions import utils
from scos_actions.hardware.hardware_configuration_exception import (
    HardwareConfigurationException,
)
from scos_actions.hardware.sigan_iface import SignalAnalyzerInterface
from scos_actions.hardware.utils import power_cycle_sigan

from scos_tekrsa import settings
from scos_tekrsa.hardware.mocks.rsa_block import MockRSA

logger = logging.getLogger(__name__)


class TekRSASigan(SignalAnalyzerInterface):
    def __init__(self):
        try:
            super().__init__()
            logger.info("Initializing Tektronix RSA Signal Analyzer")
            self.sigan_lock = threading.Lock()
            self.rsa = None
            self._is_available = False

            # Allowed sample rates and bandwidth settings, ordered from
            # greatest to least. SR in samples/sec, BW in Hz.
            self.ALLOWED_SR = [
                56.0e6,
                28.0e6,
                14.0e6,
                7.0e6,
                3.5e6,
                1.75e6,
                875.0e3,
                437.5e3,
                218.75e3,
                109.375e3,
                54687.5,
                24373.75,
                13671.875,
            ]

            self.ALLOWED_BW = [
                40.0e6,
                20.0e6,
                10.0e6,
                5.0e6,
                2.5e6,
                1.25e6,
                625.0e3,
                312.5e3,
                156.25e3,
                78125.0,
                39062.5,
                19531.25,
                9765.625,
            ]

            # Use values defined above to create SR/BW mapping dict,
            # with SR as keys and BW as values.
            self.SR_BW_MAP = dict(zip(self.ALLOWED_SR, self.ALLOWED_BW))

            self.max_sample_rate = self.ALLOWED_SR[0]
            self.max_reference_level = 30  # dBm, constant
            self.min_reference_level = -130  # dBm, constant
            self.max_attenuation = 51
            self.min_attenuation = 0
            self.max_frequency = None
            self.min_frequency = None

            self.sensor_calibration_data = None
            self.sigan_calibration_data = None
            self._capture_time = None
            self.connect()

        except Exception as error:
            logger.error(f"Unable to initialize sigan: {error}")
            self.power_cycle_and_connect()

    def get_constraints(self):
        self.min_frequency = self.rsa.CONFIG_GetMinCenterFreq()
        self.max_frequency = self.rsa.CONFIG_GetMaxCenterFreq()
        self.min_iq_bandwidth = self.rsa.IQSTREAM_GetMinAcqBandwidth()
        self.max_iq_bandwidth = self.rsa.IQSTREAM_GetMaxAcqBandwidth()

    def connect(self):
        logger.info("Connecting to TEKRSA")
        # Device already connected
        if self._is_available:
            return True

        if settings.RUNNING_TESTS or settings.MOCK_SIGAN:
            # Mock signal analyzer if desired
            logger.warning("Using mock Tektronix RSA.")
            random = settings.MOCK_SIGAN_RANDOM
            self.rsa = MockRSA(randomize_values=random)
            self.device_name = "RSA306B"  # Mock sigan pretends to be a 306B
        else:
            try:
                # Load API wrapper
                logger.info("Loading RSA API wrapper")
                import rsa_api
            except ImportError as import_error:
                logger.warning("API Wrapper not loaded - disabling signal analyzer.")
                self._is_available = False
                raise import_error

            try:
                logger.debug("Initializing ")
                self.rsa = rsa_api.RSA()
                # Connect to device using API wrapper
                self.rsa.DEVICE_SearchAndConnect()
                self.device_name = self.rsa.DEVICE_GetNomenclature()
                logger.info("Device Name: " + self.device_name)
                self.get_constraints()
                logger.info("Using the following Tektronix RSA device:")
                logger.info(
                    self.device_name
                    + " "
                    + str(self.min_frequency)
                    + "-"
                    + str(self.max_frequency)
                )
            except Exception as e:
                self._is_available = False
                self.device_name = "NONE: Failed to connect to TekRSA"
                logger.exception("Unable to connect to TEKRSA")
                raise e

        self._is_available = True

    @property
    def is_available(self):
        """Returns True if initialized and ready for measurements"""
        return self._is_available

    @property
    def sample_rate(self):
        return self.rsa.IQSTREAM_GetAcqParameters()[1]

    @sample_rate.setter
    def sample_rate(self, sample_rate):
        """Set the device sample rate and bandwidth by specifying the sample rate."""
        if sample_rate > self.max_sample_rate:
            err_msg = f"Sample rate {sample_rate} too high. Max sample rate is {self.max_sample_rate}."
            logger.error(err_msg)
            raise Exception(err_msg)
        if sample_rate not in self.ALLOWED_SR:
            # If requested sample rate is not an allowed value
            allowed_sample_rates_str = ", ".join(map(str, self.ALLOWED_SR))
            err_msg = (
                f"Requested sample rate {sample_rate} not in allowed sample rates."
                + f" Allowed sample rates are {allowed_sample_rates_str}"
            )
            logger.error(err_msg)
            raise ValueError(err_msg)
        # Set RSA IQ Bandwidth based on sample_rate
        # The IQ Bandwidth determines the RSA sample rate.
        bw = self.SR_BW_MAP.get(sample_rate)
        self.rsa.IQSTREAM_SetAcqBandwidth(bw)
        msg = (
            "Set Tektronix RSA sample rate: "
            + f"{self.rsa.IQSTREAM_GetAcqParameters()[1]:.1f} samples/sec"
        )
        logger.debug(msg)

    @property
    def iq_bandwidth(self):
        return self.rsa.IQSTREAM_GetAcqParameters()[0]

    @iq_bandwidth.setter
    def iq_bandwidth(self, iq_bandwidth):
        """Set the device sample rate and bandwidth by specifying the bandwidth."""
        if iq_bandwidth not in self.ALLOWED_BW:
            allowed_bandwidths_str = ", ".join(map(str, self.allowed_BW))
            err_msg = (
                f"Requested IQ bandwidth {iq_bandwidth} not in allowed bandwidths."
                + f" Allowed IQ bandwidths are {allowed_bandwidths_str}"
            )
            logger.error(err_msg)
            raise ValueError(err_msg)
        # Set the RSA IQ Bandwidth. This also sets the sample rate.
        self.rsa.IQSTREAM_SetAcqBandwidth(iq_bandwidth)
        new_bw, new_sr = self.rsa.IQSTREAM_GetAcqParameters()
        msg = (
            "Set Tektronix RSA IQ Bandwidth: "
            + f"{new_bw:.1f} Hz, resulting in sample rate: {new_sr:.1f} samples/sec"
        )
        logger.debug(msg)

    @property
    def frequency(self):
        return self.rsa.CONFIG_GetCenterFreq()

    @frequency.setter
    def frequency(self, freq):
        """Set the device center frequency."""
        self.rsa.CONFIG_SetCenterFreq(freq)
        msg = (
            "Set Tektronix RSA center frequency: "
            + f"{self.rsa.CONFIG_GetCenterFreq():.1f} Hz"
        )
        logger.debug(msg)

    @property
    def reference_level(self):
        return self.rsa.CONFIG_GetReferenceLevel()

    @reference_level.setter
    def reference_level(self, reference_level):
        """Set the device reference level."""
        self.rsa.CONFIG_SetReferenceLevel(reference_level)
        msg = (
            "Set Tektronix RSA reference level: "
            + f"{self.rsa.CONFIG_GetReferenceLevel():.1f} dBm"
        )
        logger.debug(msg)

    @property
    def attenuation(self):
        if self.device_name not in ["RSA306B", "RSA306"]:
            return self.rsa.CONFIG_GetRFAttenuator()
        else:
            logger.debug("Tektronix RSA 300 series device has no attenuator.")
            return None

    @attenuation.setter
    def attenuation(self, attenuation):
        """Set device attenuation, in dB, for RSA 500/600 series devices"""
        if self.device_name not in ["RSA306B", "RSA306"]:
            self.rsa.CONFIG_SetAutoAttenuationEnable(False)
            self.rsa.CONFIG_SetRFAttenuator(
                -1 * attenuation
            )  # rounded to nearest integer
            msg = (
                "Set Tektronix RSA attenuation: "
                + f"{self.rsa.CONFIG_GetRFAttenuator():.1} dB"
            )
            logger.debug(msg)
        else:
            logger.debug("Tektronix RSA 300 series device has no attenuator.")

    @property
    def preamp_enable(self):
        if self.device_name not in ["RSA306B", "RSA306"]:
            return self.rsa.CONFIG_GetRFPreampEnable()
        else:
            logger.debug("Tektronix RSA 300 series device has no built-in preamp.")
            return None

    @preamp_enable.setter
    def preamp_enable(self, preamp_enable):
        if self.device_name not in ["RSA306B", "RSA306"]:
            if self.preamp_enable != preamp_enable:
                logger.debug("Switching preamp to " + str(preamp_enable))
                self.rsa.CONFIG_SetRFPreampEnable(preamp_enable)
                msg = (
                    "Set Tektronix RSA preamp enable status: "
                    f"{self.rsa.CONFIG_GetRFPreampEnable()}"
                )
                logger.debug(msg)
        else:
            logger.debug("Tektronix RSA 300 series device has no built-in preamp.")

    @property
    def healthy(self, num_samples=56000):
        """Perform health check by collecting IQ samples."""
        logger.debug("Performing Tektronix RSA health check.")

        try:
            # self.frequency = 3555e6
            # self.reference_level = -25
            # self.attenuation = 0
            # self.preamp_enable = True
            # self.sample_rate = 14e6
            measurement_result = self.acquire_time_domain_samples(num_samples, gain_adjust=False)
            data = measurement_result["data"]
        except Exception as e:
            logger.exception("Unable to acquire samples from RSA device.")
            return False

        if not len(data) == num_samples:
            logger.error("RSA data doesn't match request.")
            return False

        return True


    def acquire_time_domain_samples(
        self, num_samples, num_samples_skip=0, retries=5, gain_adjust=True
    ):
        """Acquire specific number of time-domain IQ samples."""
        self._capture_time = None
        nsamps_req = int(num_samples)  # Requested number of samples
        nskip = int(num_samples_skip)  # Requested number of samples to skip
        nsamps = nsamps_req + nskip  # Total number of samples to collect

        if gain_adjust:
            # Get calibration data for acquisition
            calibration_args = [self.sample_rate, self.frequency, self.reference_level]
            self.recompute_calibration_data(calibration_args)
            # Compute the linear gain
            db_gain = self.sensor_calibration_data["gain_sensor"]
            linear_gain = 10 ** (db_gain / 20.0)
        else:
            linear_gain = 1

        # Determine correct time length (round up, integer ms)
        durationMsec = int(1000 * (nsamps / self.sample_rate)) + (
            1000 * nsamps % self.sample_rate > 0
        )

        if durationMsec == 0:
            # Num. samples requested is less than minimum duration for IQ stream.
            # Handle this by skipping more samples than requested
            durationMsec = 1  # Minimum allowed IQ stream duration
            nskip = int((self.sample_rate / 1000) - nsamps_req)
            nsamps = nskip + nsamps_req

        logger.debug(f"acquire_time_domain_samples starting, num_samples = {nsamps}")
        logger.debug(f"Number of retries = {retries}")

        max_retries = retries

        while True:
            self._capture_time = utils.get_datetime_str_now()
            try:
                self.sigan_lock.acquire() # not sure if this is sufficient, may need lock to include setting sigan parameters
                data, status = self.rsa.IQSTREAM_Acquire(durationMsec, True)
            finally:
                self.sigan_lock.release()
            data = data[nskip:]  # Remove extra samples, if any
            data_len = len(data)

            # Print warning from status indicator
            # if status != 'No error.':
            iq_warn = "IQ Stream Status:\n{}"
            logger.warning(iq_warn.format(status))

            # Check status string for overload / data loss
            self.overload = False
            if "Input overrange" in status:
                self.overload = True
            if "data loss" in status or "discontinuity" in status:
                if retries > 0:
                    logger.warning(f"Retrying {retries} more times.")
                    retries -= 1
                else:
                    err = "Data loss occurred with no retries remaining."
                    err += f" (tried {retries} times.)"
                    raise RuntimeError(err)

            if not data_len == nsamps_req:
                if retries > 0:
                    msg = f"RSA error: requested {nsamps_req + nskip} samples, but got {data_len}."
                    logger.warning(msg)
                    logger.warning(f"Retrying {retries} more times.")
                    retries -= 1
                else:
                    err = "Failed to acquire correct number of samples "
                    err += f"{max_retries} times in a row."
                    raise RuntimeError(err)
            else:
                logger.debug(f"Successfully acquired {data_len} samples.")
                # Scale data to RF power and return
                logger.debug("Applying gain of {}".format(linear_gain))
                data /= linear_gain

                measurement_result = {
                    "data": data,
                    "overload": self.overload,
                    "frequency": self.frequency,
                    "reference_level": self.reference_level,
                    "sample_rate": self.rsa.IQSTREAM_GetAcqParameters()[1],
                    "capture_time": self._capture_time,
                }
                if self.device_name not in ["RSA306B", "RSA306"]:
                    measurement_result["attenuation"] = self.attenuation
                    measurement_result["preamp_enable"] = self.preamp_enable
                return measurement_result
