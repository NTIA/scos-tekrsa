import logging
import threading
from typing import Optional

from its_preselector.web_relay import WebRelay
from scos_actions import utils
from scos_actions.hardware.sigan_iface import SignalAnalyzerInterface

import scos_tekrsa.hardware.tekrsa_constants as rsa_constants
from scos_tekrsa import __package__ as SCOS_TEKRSA_NAME
from scos_tekrsa import __version__ as SCOS_TEKRSA_VERSION
from scos_tekrsa import settings
from scos_tekrsa.hardware.mocks.rsa_block import MockRSA

logger = logging.getLogger(__name__)

sigan_lock = threading.Lock()


class TekRSASigan(SignalAnalyzerInterface):
    def __init__(
        self,
        switches: Optional[dict[str, WebRelay]] = None,
    ):

        try:
            super().__init__(switches)
            logger.debug("Initializing Tektronix RSA Signal Analyzer")
            self._plugin_version = SCOS_TEKRSA_VERSION
            self._plugin_name = SCOS_TEKRSA_NAME

            self.rsa = None
            self._is_available = False  # should not be set outside of connect method

            # Retrieve constants applicable to ALL supported devices
            self.ALLOWED_SR = rsa_constants.IQSTREAM_ALLOWED_SR  # Samps/sec
            self.ALLOWED_BW = rsa_constants.IQSTREAM_ALLOWED_BW  # Hz
            self.max_sample_rate = max(self.ALLOWED_SR)
            self.max_reference_level = rsa_constants.MAX_REFERENCE_LEVEL  # dBm
            self.min_reference_level = rsa_constants.MIN_REFERENCE_LEVEL  # dBm
            self.max_attenuation = rsa_constants.MAX_ATTENUATION  # dB
            self.min_attenuation = rsa_constants.MIN_ATTENUATION  # dB

            # SR/BW mapping dict, with SR as keys and BW as values.
            self.SR_BW_MAP = rsa_constants.IQSTREAM_SR_BW_MAP

            # These are device-dependent, set in get_constraints()
            self.max_frequency = None
            self.min_frequency = None

            self._capture_time = None
            self._reference_level = None
            self._frequency = None
            self._iq_bandwidth = None
            self._sample_rate = None
            self._attenuation = None
            self._preamp_enable = None
            self._api_version = None
            self._firmware_version = None
            self.max_iq_bandwidth = None
            self.min_iq_bandwidth = None
            self.overload = None
            self.connect()

        except BaseException as error:
            logger.error(f"Unable to initialize sigan: {error}.")
            self._is_available = False
            self._model = "NONE: Failed to connect to TekRSA"

    def get_constraints(self):
        self.min_frequency = self.rsa.CONFIG_GetMinCenterFreq()
        self.max_frequency = self.rsa.CONFIG_GetMaxCenterFreq()
        self.min_iq_bandwidth = self.rsa.IQSTREAM_GetMinAcqBandwidth()
        self.max_iq_bandwidth = self.rsa.IQSTREAM_GetMaxAcqBandwidth()

    def connect(self):
        logger.debug("Connecting to TEKRSA")
        # Device already connected
        if self._is_available:
            return True

        if settings.RUNNING_TESTS or settings.MOCK_SIGAN:
            # Mock signal analyzer if desired
            logger.warning("Using mock Tektronix RSA signal analyzer.")
            random = settings.MOCK_SIGAN_RANDOM
            self.rsa = MockRSA(randomize_values=random)
        else:
            try:
                import rsa_api
            except ImportError as import_error:
                logger.exception("API Wrapper not loaded - disabling signal analyzer.")
                self._is_available = False
                self._model = "NONE: Failed to connect to TekRSA"
                raise import_error
            logger.debug("Initializing ")
            self.rsa = rsa_api.RSA()
            # Connect to device using API wrapper
            self.rsa.DEVICE_SearchAndConnect()

        # Finish setup with either real or Mock RSA device
        self._model = self.rsa.DEVICE_GetNomenclature()
        self._firmware_version = self.rsa.DEVICE_GetFWVersion()
        self._api_version = self.rsa.DEVICE_GetAPIVersion()
        self.get_constraints()
        logger.debug("Using the following Tektronix RSA device:")
        logger.debug(f"{self._model} ({self.min_frequency}-{self.max_frequency} Hz)")
        # Populate instance variables for parameters on connect
        self._preamp_enable = self.preamp_enable
        self._attenuation = self.attenuation
        self._sample_rate = self.sample_rate  # Also sets self._iq_bandwidth
        self._frequency = self.frequency
        self._reference_level = self.reference_level
        self._is_available = True

    @property
    def is_available(self) -> bool:
        """Returns True if initialized and ready for measurements"""
        return self._is_available

    @property
    def plugin_version(self) -> str:
        """Returns the current version of scos-tekrsa."""
        return self._plugin_version

    @property
    def plugin_name(self) -> str:
        """Returns the current package name of scos-tekrsa."""
        return self._plugin_name

    @property
    def firmware_version(self) -> str:
        """Returns the current firmware version of the connected RSA device."""
        return self._firmware_version

    @property
    def api_version(self) -> str:
        """Returns the version of the Tektronix RSA API for Linux currently in use."""
        return self._api_version

    @property
    def sample_rate(self):
        self._iq_bandwidth, self._sample_rate = self.rsa.IQSTREAM_GetAcqParameters()
        return self._sample_rate

    @sample_rate.setter
    def sample_rate(self, sample_rate):
        """Set the device sample rate and bandwidth by specifying the sample rate."""
        if sample_rate > self.max_sample_rate:
            err_msg = f"Sample rate {sample_rate} too high. Max sample rate is {self.max_sample_rate}."
            logger.error(err_msg)
            raise ValueError(err_msg)
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
        self._iq_bandwidth, self._sample_rate = self.rsa.IQSTREAM_GetAcqParameters()
        msg = "Set Tektronix RSA sample rate: " + f"{self._sample_rate} samples/sec"
        logger.debug(msg)

    @property
    def iq_bandwidth(self):
        self._iq_bandwidth, self._sample_rate = self.rsa.IQSTREAM_GetAcqParameters()
        return self._iq_bandwidth

    @iq_bandwidth.setter
    def iq_bandwidth(self, iq_bandwidth):
        """Set the device sample rate and bandwidth by specifying the bandwidth."""
        if iq_bandwidth not in self.ALLOWED_BW:
            allowed_bandwidths_str = ", ".join(map(str, self.ALLOWED_BW))
            err_msg = (
                f"Requested IQ bandwidth {iq_bandwidth} not in allowed bandwidths."
                + f" Allowed IQ bandwidths are {allowed_bandwidths_str}"
            )
            logger.error(err_msg)
            raise ValueError(err_msg)
        # Set the RSA IQ Bandwidth. This also sets the sample rate.
        self.rsa.IQSTREAM_SetAcqBandwidth(iq_bandwidth)
        self._iq_bandwidth, self._sample_rate = self.rsa.IQSTREAM_GetAcqParameters()
        msg = (
            "Set Tektronix RSA IQ Bandwidth: "
            + f"{self._iq_bandwidth} Hz, resulting in sample rate: "
            + f"{self._sample_rate} samples/sec"
        )
        logger.debug(msg)

    @property
    def frequency(self):
        self._frequency = self.rsa.CONFIG_GetCenterFreq()
        return self._frequency

    @frequency.setter
    def frequency(self, freq):
        """Set the device center frequency."""
        self.rsa.CONFIG_SetCenterFreq(freq)
        self._frequency = self.rsa.CONFIG_GetCenterFreq()
        msg = f"Set Tektronix RSA center frequency: {self._frequency} Hz"
        logger.debug(msg)

    @property
    def reference_level(self):
        self._reference_level = self.rsa.CONFIG_GetReferenceLevel()
        return self._reference_level

    @reference_level.setter
    def reference_level(self, reference_level):
        """Set the device reference level."""
        self.rsa.CONFIG_SetReferenceLevel(reference_level)
        self._reference_level = self.rsa.CONFIG_GetReferenceLevel()
        msg = f"Set Tektronix RSA reference level: {self._reference_level} dBm"
        logger.debug(msg)

    @property
    def attenuation(self):
        if self._model not in ["RSA306B", "RSA306"]:
            # API returns attenuation as negative value. Convert to positive.
            self._attenuation = abs(self.rsa.CONFIG_GetRFAttenuator())
        else:
            logger.debug("Tektronix RSA 300 series device has no attenuator.")
            self._attenuation = None
        return self._attenuation

    @attenuation.setter
    def attenuation(self, attenuation):
        """Set device attenuation, in dB, for RSA 500/600 series devices"""
        if self._model not in ["RSA306B", "RSA306"]:
            if self.min_attenuation <= abs(attenuation) <= self.max_attenuation:
                self.rsa.CONFIG_SetAutoAttenuationEnable(False)
                # API requires attenuation set as a negative number. Convert to negative.
                self.rsa.CONFIG_SetRFAttenuator(
                    -1 * abs(attenuation)
                )  # rounded to nearest integer
                self._attenuation = abs(self.rsa.CONFIG_GetRFAttenuator())
                logger.debug(f"Set Tektronix RSA attenuation: {self._attenuation} dB")
            else:
                raise ValueError(
                    f"Attenuation setting must be between {self.min_attenuation}"
                    + f" and {self.max_attenuation} dB."
                )
        else:
            logger.debug("Tektronix RSA 300 series device has no attenuator.")

    @property
    def preamp_enable(self):
        if self._model not in ["RSA306B", "RSA306"]:
            self._preamp_enable = self.rsa.CONFIG_GetRFPreampEnable()
        else:
            logger.debug("Tektronix RSA 300 series device has no built-in preamp.")
            self._preamp_enable = None
        return self._preamp_enable

    @preamp_enable.setter
    def preamp_enable(self, preamp_enable):
        if self._model not in ["RSA306B", "RSA306"]:
            if self.preamp_enable != preamp_enable:
                logger.debug("Switching preamp to " + str(preamp_enable))
                self.rsa.CONFIG_SetRFPreampEnable(preamp_enable)
                self._preamp_enable = self.rsa.CONFIG_GetRFPreampEnable()
                msg = f"Set Tektronix RSA preamp enable status: {self._preamp_enable}"
                logger.debug(msg)
            else:
                logger.debug(
                    f"Tektronix RSA preamp enable status is already {self._preamp_enable}"
                )
        else:
            logger.debug("Tektronix RSA 300 series device has no built-in preamp.")

    @property
    def temperature(self) -> float:
        """Read-only attribute: internal temperature, in Celsius."""
        return self.rsa.DEVICE_GetTemperature()

    def acquire_time_domain_samples(
        self,
        num_samples: int,
        num_samples_skip: int = 0,
    ):
        """Acquire specific number of time-domain IQ samples."""
        with sigan_lock:
            self._capture_time = None
            if isinstance(num_samples, int) or (
                isinstance(num_samples, float) and num_samples.is_integer()
            ):
                nsamps_req = int(num_samples)  # Requested number of samples
            else:
                raise ValueError("Requested number of samples must be an integer.")
            nskip = int(num_samples_skip)  # Requested number of samples to skip
            nsamps = nsamps_req + nskip  # Total number of samples to collect

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

            logger.debug(
                f"acquire_time_domain_samples starting, num_samples = {nsamps}"
            )

            self._capture_time = utils.get_datetime_str_now()

            data, status = self.rsa.IQSTREAM_Tempfile_NoConfig(durationMsec, True)

            data = data[nskip : nskip + nsamps_req]  # Remove extra samples, if any
            data_len = len(data)

            logger.debug(f"IQ Stream status: {status}")

            # Check status string for overload / data loss
            self.overload = False
            if "Input overrange" in status:
                self.overload = True
                logger.debug("IQ stream: ADC overrange event occurred.")

            if "data loss" in status or "discontinuity" in status:  # Invalid data
                msg = "Data loss occurred during IQ streaming"
                logger.debug(msg)
                raise RuntimeError(msg)
            elif (
                not data_len == nsamps_req
            ):  # Invalid data: incorrect number of samples
                msg = f"RSA error: requested {nsamps_req + nskip} samples, but got {data_len}."
                logger.debug(msg)
                raise RuntimeError(msg)
            else:
                logger.debug(f"IQ stream: successfully acquired {data_len} samples.")

                measurement_result = {
                    "data": data,
                    "overload": self.overload,
                    "frequency": self.frequency,
                    "reference_level": self.reference_level,
                    "sample_rate": self.rsa.IQSTREAM_GetAcqParameters()[1],
                    "capture_time": self._capture_time,
                }
                if self._model not in ["RSA306B", "RSA306"]:
                    measurement_result["attenuation"] = self.attenuation
                    measurement_result["preamp_enable"] = self.preamp_enable
                return measurement_result
