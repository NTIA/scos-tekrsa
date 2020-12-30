import time
from datetime import datetime
from unittest.mock import Mock, create_autospec, patch

import numpy as np
import pytest
from pytest import approx

from scos_tekrsa import settings

from scos_tekrsa.hardware.rsa306b_radio import RSARadio
from scos_tekrsa.hardware.tests.resources.utils import (
    create_dummy_calibration,
    easy_gain,
)


class TestRSA:
    def setup_method(self):
        """ Create the mock Keysight"""

        # https://stackoverflow.com/questions/57299968/python-how-to-reuse-a-mock-to-avoid-writing-mock-patch-multiple-times
        self.keysight_measurement_patcher = patch(
            "scos_sensor_keysight.hardware.n6841a_radio.Measurement"
        )
        self.keysight_utils_patcher = patch(
            "scos_sensor_keysight.hardware.n6841a_radio.Utils"
        )
        self.keysight_system_info_patcher = patch(
            "scos_sensor_keysight.hardware.n6841a_radio.SystemInfo"
        )
        self.mock_keysight_measurement = self.keysight_measurement_patcher.start()
        self.mock_keysight_utils = self.keysight_utils_patcher.start()
        self.mock_keysight_system_info = self.keysight_system_info_patcher.start()

        def side_effect_attributes(metadata):
            metadata.update(
                {
                    "attenuation_max": 43,
                    "attenuation_min": -10,
                    "center_freq_max": 6e9,
                    "center_freq_min": 20e4,
                }
            )

        self.mock_keysight_system_info.get_all_attributes.side_effect = (
            side_effect_attributes
        )

        caps = SALLinux.salSensorCapabilities2()
        caps.maxSampleRate = 28e6
        self.mock_keysight_system_info.get_capabilities = Mock(return_value=caps)

        self.tuner_info = SALLinux.salTunerParms()
        self.tuner_info.sampleRate = 28e6
        self.tuner_info.centerFrequency = 700e6
        self.tuner_info.attenuation = 40
        self.mock_keysight_measurement.get_tuner = Mock(return_value=self.tuner_info)
        self.rx = N6841ARadio(
            sensor_cal_file=settings.SENSOR_CALIBRATION_FILE,
            sigan_cal_file=settings.SIGAN_CALIBRATION_FILE,
        )

    def teardown_method(self):
        self.keysight_measurement_patcher.stop()
        self.keysight_utils_patcher.stop()
        self.keysight_system_info_patcher.stop()

    def test_acquire_samples_with_retries(self):
        """Acquire samples should retry without error up to `max_retries`."""

        max_retries = 5
        times_to_fail = 3

        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            if call_count < times_to_fail:
                call_count += 1
                result = Measurement.IQResult()
                result.data = np.arange(0, 500, dtype=np.csingle)
                result.sigan_overload = False
                result.capture_time = datetime.now()
                return result
            else:
                call_count += 1
                result = Measurement.IQResult()
                result.data = np.arange(0, 1000, dtype=np.csingle)
                result.sigan_overload = False
                result.capture_time = datetime.now()
                return result

        self.mock_keysight_measurement.time_domain_iq_measurement.side_effect = (
            side_effect
        )

        try:
            self.rx.acquire_time_domain_samples(1000, retries=max_retries)
        except RuntimeError:
            msg = "Acquisition failing {} times sequentially with {}\n"
            msg += "retries requested should NOT have raised an error."
            msg = msg.format(times_to_fail, max_retries)
            pytest.fail(msg)

    def test_acquire_samples_fails_when_over_max_retries(self):
        """After `max_retries`, an error should be thrown."""

        max_retries = 5
        times_to_fail = 7
        call_count = 0

        def side_effect(*args, **kwargs):
            nonlocal call_count
            if call_count < times_to_fail:
                call_count += 1
                result = Measurement.IQResult()
                result.data = np.arange(0, 500, dtype=np.csingle)
                result.capture_time = datetime.now()
                result.sigan_overload = False
                return result
            else:
                call_count += 1
                result = Measurement.IQResult()
                result.data = np.arange(0, 1000, dtype=np.csingle)
                result.capture_time = datetime.now()
                result.sigan_overload = False
                return result

        self.mock_keysight_measurement.time_domain_iq_measurement.side_effect = (
            side_effect
        )

        msg = "Acquisition failing {} times sequentially with {}\n"
        msg += "retries requested SHOULD have raised an error."
        msg = msg.format(times_to_fail, max_retries)
        with pytest.raises(RuntimeError):
            self.rx.acquire_time_domain_samples(1000, 1000, max_retries)
            pytest.fail(msg)

    def test_tune_result_frequency(self):
        """Check that the tuning is correct"""
        assert self.tuner_info.centerFrequency == self.rx.frequency

        f_lo = 1.0e9
        self.rx.frequency = f_lo
        tuner_info = self.tuner_info
        tuner_info.centerFrequency = f_lo
        args, kwargs = self.mock_keysight_measurement.set_tuner.call_args
        assert args[1] == tuner_info or kwargs["tuner"] == tuner_info

    def test_tune_result_sample_rate(self):
        """Check that the tuning is correct"""
        sample_rate = 14e6
        self.rx.sample_rate = sample_rate
        tuner_info = self.tuner_info
        tuner_info.sampleRate = sample_rate
        args, kwargs = self.mock_keysight_measurement.set_tuner.call_args
        assert args[1] == tuner_info or kwargs["tuner"] == tuner_info

    def test_scaled_data_acquisition(self):
        """Check that the samples are properly scaled"""
        db_gain = 20
        self.rx.sensor_calibration_data["gain_sensor"] = db_gain

        def side_effect(*args, **kwargs):
            result = Measurement.IQResult()
            result.data = np.repeat(1.0, 1000)
            result.sigan_overload = False
            result.capture_time = datetime.now()
            return result

        self.mock_keysight_measurement.time_domain_iq_measurement.side_effect = (
            side_effect
        )

        measurement_result = self.rx.acquire_time_domain_samples(1000)
        data = measurement_result["data"]

        # The true value should be the 1 / linear gain
        true_val = easy_gain(int(10e6), 1e9, db_gain) - 10
        true_val = 10 ** (-1 * float(true_val) / 20)

        # Get the observed value
        observed_val = data[0]

        # Assert the value
        tolerance = 1e-5
        msg = "Acquisition was not properly scaled.\n"
        msg += "    Algorithm: {}\n".format(observed_val)
        msg += "    Expected: {}\n".format(true_val)
        msg += "    Tolerance: {}\r\n".format(tolerance)
        # assert is_close(true_val, observed_val, tolerance), msg
        observed_val == approx(true_val, abs=tolerance)

    def check_defaulted_calibration_parameter(self, param, expected, observed):
        msg = "Default calibration parameters were not properly set.\n"
        msg += "    Parameter: {}\n".format(param)
        msg += "    Expected: {}\n".format(expected)
        msg += "    Observed: {}\r\n".format(observed)
        assert expected == observed, msg

    def test_defaulted_calibration_values(self):
        """Ensure that default calibration values are loaded"""

        # Save and clear the calibrations
        sigan_calibration = self.rx.sigan_calibration
        sensor_calibration = self.rx.sensor_calibration
        self.rx.sigan_calibration = None
        self.rx.sensor_calibration = None

        # Create some dummy setups to ensure calibration updates
        sample_rates = [10e6, 40e6, 1e6, 56e6]
        attenuation_settings = [0, 43, -19, 43]
        frequencies = [1000e6, 2000e6, 10e6, 1500e6]

        # Run each set
        for i in range(len(sample_rates)):
            # Get the parameters for this run
            sample_rate = sample_rates[i]
            attenuation_setting = attenuation_settings[i]
            frequency = frequencies[i]

            # Setup the rx
            tuner_info = SALLinux.salTunerParms()
            tuner_info.sampleRate = sample_rate
            tuner_info.centerFrequency = frequency
            tuner_info.attenuation = attenuation_setting
            self.mock_keysight_measurement.get_tuner = Mock(return_value=tuner_info)

            # Recompute the calibration parameters
            self.rx.recompute_calibration_data()

            # Check the defaulted calibration parameters
            self.check_defaulted_calibration_parameter(
                "gain_sigan", 0, self.rx.sigan_calibration_data["gain_sigan"]
            )
            self.check_defaulted_calibration_parameter(
                "enbw_sigan", sample_rate, self.rx.sigan_calibration_data["enbw_sigan"]
            )
            self.check_defaulted_calibration_parameter(
                "noise_figure_sigan",
                0,
                self.rx.sigan_calibration_data["noise_figure_sigan"],
            )
            self.check_defaulted_calibration_parameter(
                "1db_compression_sigan",
                100,
                self.rx.sigan_calibration_data["1db_compression_sigan"],
            )
            self.check_defaulted_calibration_parameter(
                "gain_sensor", 0, self.rx.sensor_calibration_data["gain_sensor"],
            )
            self.check_defaulted_calibration_parameter(
                "enbw_sensor",
                sample_rate,
                self.rx.sensor_calibration_data["enbw_sensor"],
            )
            self.check_defaulted_calibration_parameter(
                "noise_figure_sensor",
                0,
                self.rx.sensor_calibration_data["noise_figure_sensor"],
            )
            self.check_defaulted_calibration_parameter(
                "1db_compression_sensor",
                100,
                self.rx.sensor_calibration_data["1db_compression_sensor"],
            )
            self.check_defaulted_calibration_parameter(
                "gain_preselector",
                0,
                self.rx.sensor_calibration_data["gain_preselector"],
            )
            self.check_defaulted_calibration_parameter(
                "noise_figure_preselector",
                0,
                self.rx.sensor_calibration_data["noise_figure_preselector"],
            )
            self.check_defaulted_calibration_parameter(
                "1db_compression_preselector",
                100,
                self.rx.sensor_calibration_data["1db_compression_preselector"],
            )

        # Reload the calibrations in case they're used elsewhere
        self.rx.sigan_calibration = sigan_calibration
        self.rx.sensor_calibration = sensor_calibration

    def test_sigan_only_defaulting(self):
        """Ensure that sensor calibration values default to sigan"""

        # Load an empty sensor calibration
        self.rx.sensor_calibration = create_dummy_calibration(empty_cal=True)

        # Create some dummy setups to ensure calibration updates
        sample_rates = [10e6, 40e6, 1e6, 56e6]
        attenuation_settings = [0, 43, -19, 43]
        frequencies = [1000e6, 2000e6, 10e6, 1500e6]

        # Run each set
        for i in range(len(sample_rates)):
            # Get the parameters for this run
            sample_rate = sample_rates[i]
            attenuation_setting = attenuation_settings[i]
            frequency = frequencies[i]

            tuner_info = SALLinux.salTunerParms()
            tuner_info.sampleRate = sample_rate
            tuner_info.centerFrequency = frequency
            tuner_info.attenuation = attenuation_setting
            self.mock_keysight_measurement.get_tuner = Mock(return_value=tuner_info)

            # Recompute the calibration parameters
            self.rx.recompute_calibration_data()

            # Check the defaulted calibration parameters
            self.check_defaulted_calibration_parameter(
                "gain_sensor",
                self.rx.sigan_calibration_data["gain_sigan"],
                self.rx.sensor_calibration_data["gain_sensor"],
            )

        # Reload the dummy sensor calibration in case they're used elsewhere
        self.rx.sensor_calibration = create_dummy_calibration()

    def test_healthy_no_connection(self):
        def side_effect(ip_address):
            raise SensorConnectionException()

        self.mock_keysight_utils.sensor.side_effect = side_effect
        assert not self.rx.healthy

    def test_healthy_no_time_data(self):
        def side_effect(sensor):
            return SALLinux.salTimeInfo()

        self.mock_keysight_system_info.get_sensor_time.side_effect = side_effect
        assert not self.rx.healthy

    def test_healthy_with_connection(self):
        def side_effect(sensor):
            time_info = SALLinux.salTimeInfo()
            time_info.timestampSeconds = int(time.time())
            return time_info

        self.mock_keysight_system_info.get_sensor_time.side_effect = side_effect
        assert self.rx.healthy
