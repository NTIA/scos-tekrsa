"""Test aspects of RadioInterface with mocked RSA306B."""

import pytest

from scos_tekrsa.hardware import radio
from scos_tekrsa.hardware.tests.resources.utils import (
    create_dummy_calibration,
    easy_gain,
    is_close,
)


class TestRSA306B:
    # Ensure we write the test cal file and use mocks
    setup_complete = False

    @pytest.fixture(autouse=True)
    def setup_mock_rsa306b(self):
        """Create the mock RSA306B."""

        # Only setup once
        if self.setup_complete:
            return

        # Create the RadioInterface and get the radio
        if not radio.is_available:
            raise RuntimeError("Receiver is not available.")
        self.rx = radio

        # Alert that the setup was complete
        self.setup_complete = True

    # Ensure recovery from acquisition errors
    def test_acquire_samples_with_retries(self):
        """Acquire samples should retry without error up to `max_retries`."""

        # Check that the setup was completed
        assert self.setup_complete, "Setup was not completed"

        max_retries = 5

        try:
            self.rx.acquire_time_domain_samples(1000, retries=max_retries)
        except RuntimeError:
            msg = "Acquisition failing with {} retries \n"
            msg += "requested should NOT have raised an error."
            msg = msg.format(max_retries)
            pytest.fail(msg)

    def test_acquire_samples_fails_when_over_max_retries(self):
        """After `max_retries`, an error should be thrown."""

        # Check that the setup was completed
        assert self.setup_complete, "Setup was not completed"

        max_retries = 5

        msg = "Acquisition failing with {} retries\n"
        msg += "requested SHOULD have raised an error."
        msg = msg.format(max_retries)
        with pytest.raises(RuntimeError):
            self.rx.acquire_time_domain_samples(1000, 1000, max_retries)
            pytest.fail(msg)

    def test_scaled_data_acquisition(self):
        """Check that the samples are properly scaled"""
        # Check that the setup was completed
        assert self.setup_complete, "Setup was not completed"

        # Do an arbitrary data collection
        self.rx.sample_rate = int(10e6)
        self.rx.frequency = 1e9
        self.rx.reference_level = 0
        measurement_result = self.rx.acquire_time_domain_samples(1000)
        data = measurement_result["data"]

        # The true value should be the 1 / linear gain
        true_val = easy_gain(int(10e6), 1e9, 20) - 10
        true_val = 10 ** (-1 * float(true_val) / 20)

        # Get the observed value
        observed_val = data[0]

        # Assert the value
        tolerance = 1e-5
        msg = "Acquisition was not properly scaled.\n"
        msg += "    Algorithm: {}\n".format(observed_val)
        msg += "    Expected: {}\n".format(true_val)
        msg += "    Tolerance: {}\r\n".format(tolerance)
        assert is_close(true_val, observed_val, tolerance), msg

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
        ref_lev_settings = [40, 60, 0, 60]
        frequencies = [1000e6, 2000e6, 10e6, 1500e6]

        # Run each set
        for i in range(len(sample_rates)):
            # Get the parameters for this run
            sample_rate = sample_rates[i]
            ref_lev_setting = ref_lev_settings[i]
            frequency = frequencies[i]

            # Setup the rx
            self.rx.sample_rate = sample_rate
            self.rx.reference_level = ref_lev_setting
            self.rx.frequency = frequency

            # Recompute the calibration parameters
            self.rx.recompute_calibration_data()

            # Check the defaulted calibration parameters
            self.check_defaulted_calibration_parameter(
                "gain_sigan", ref_lev_setting, self.rx.sigan_calibration_data["gain_sigan"]
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
                "reference_level",
                ref_lev_setting,
                self.rx.sensor_calibration_data["reference_level"],
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
        ref_lev_settings = [40, 60, 0, 60]
        frequencies = [1000e6, 2000e6, 10e6, 1500e6]

        # Run each set
        for i in range(len(sample_rates)):
            # Get the parameters for this run
            sample_rate = sample_rates[i]
            ref_lev_setting = ref_lev_settings[i]
            frequency = frequencies[i]

            # Setup the rx
            self.rx.sample_rate = sample_rate
            self.rx.reference_level = ref_lev_setting
            self.rx.frequency = frequency

            # Recompute the calibration parameters
            self.rx.recompute_calibration_data()

            # Check the defaulted calibration parameters
            self.check_defaulted_calibration_parameter(
                "reference_level",
                self.rx.sigan_calibration_data["gain_sigan"],
                self.rx.sensor_calibration_data["reference_level"],
            )

        # Reload the dummy sensor calibration in case they're used elsewhere
        self.rx.sensor_calibration = create_dummy_calibration()
