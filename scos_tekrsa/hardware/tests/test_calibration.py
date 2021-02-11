"""Test aspects of ScaleFactors."""
import datetime
import json
import random
from copy import deepcopy

import pytest

from scos_tekrsa.hardware import calibration
from scos_tekrsa.hardware.tests.resources.utils import easy_gain, is_close


class TestCalibrationFile:
    # Ensure we load the test file
    setup_complete = False

    def rand_index(self, l):
        """ Get a random index for a list """
        return random.randint(0, len(l) - 1)

    def check_duplicate(self, sr, f, g):
        """ Check if a set of points was already tested """
        for pt in self.pytest_points:
            duplicate_f = f == pt["frequency"]
            duplicate_a = g == pt["ref_level"]
            duplicate_sr = sr == pt["sample_rate"]
            if duplicate_f and duplicate_a and duplicate_sr:
                return True

    def run_pytest_point(
        self, sr, f, ref_level, reason, sr_m=False, f_m=False, reflev_m=False
    ):
        """ Test the calculated value against the algorithm
            Parameters:
                sr, f, ref_level -> Set values for the mock RSA
                reason: Test case string for failure reference
                sr_m, f_m, reflev_m -> Set values to use when calculating the expected value
                                  May differ in from actual set points in edge cases
                                  such as tuning in divisions or uncalibrated sample rate"""
        # Check that the setup was completed
        assert self.setup_complete, "Setup was not completed"

        # If this point was tested before, skip it (triggering a new one)
        if self.check_duplicate(sr, f, ref_level):
            return False

        # If the point doesn't have modified inputs, use the algorithm ones
        if not f_m:
            f_m = f
        if not reflev_m:
            reflev_m = ref_level
        if not sr_m:
            sr_m = sr

        # Calculate what the scale factor should be
        calc_gain_sigan = easy_gain(sr_m, f_m, reflev_m)

        # Get the scale factor from the algorithm
        interp_cal_data = self.sample_cal.get_calibration_dict(sr, f, reflev_m)
        interp_gain_siggan = interp_cal_data["gain_sigan"]

        # Save the point so we don't duplicate
        self.pytest_points.append(
            {
                "sample_rate": int(sr),
                "frequency": f,
                "ref_level": ref_level,
                "gain_sigan": calc_gain_sigan,
                "test": reason,
            }
        )

        # Check if the point was calculated correctly
        tolerance = 1e-5
        msg = "Gain sigan not correctly calculated!\r\n"
        msg = "{}    Expected value:   {}\r\n".format(msg, calc_gain_sigan)
        msg = "{}    Calculated value: {}\r\n".format(msg, interp_gain_siggan)
        msg = "{}    Tolerance: {}\r\n".format(msg, tolerance)
        msg = "{}    Test: {}\r\n".format(msg, reason)
        msg = "{}    Sample Rate: {}({})\r\n".format(msg, sr / 1e6, sr_m / 1e6)
        msg = "{}    Frequency: {}({})\r\n".format(msg, f / 1e6, f_m / 1e6)
        msg = "{}    Reference Level: {}({})\r\n".format(msg, ref_level, reflev_m)
        msg = "{}    Formula: -1 * (Reference Level - Frequency[GHz] - Sample Rate[MHz])\r\n".format(
            msg
        )
        assert is_close(calc_gain_sigan, interp_gain_siggan, tolerance), msg
        return True

    @pytest.fixture(autouse=True)
    def setup_calibration_file(self, tmpdir):
        """ Create the dummy calibration file in the pytest temp directory """

        # Only setup once
        if self.setup_complete:
            return

        # Create and save the temp directory and file
        self.tmpdir = tmpdir.strpath
        self.calibration_file = "{}".format(tmpdir.join("dummy_cal_file.json"))

        # Setup variables
        self.dummy_noise_figure = 10
        self.dummy_compression = -20
        self.test_repeat_times = 3

        # Sweep variables
        self.sample_rates = [10e6, 15.36e6, 40e6]
        self.reflev_min = -30
        self.reflev_max = 30
        self.ref_level_step = 10
        ref_levels = list(
            range(self.reflev_min, self.reflev_max, self.ref_level_step)
        ) + [self.reflev_max]
        self.frequency_min = 9000
        self.frequency_max = 6200000000
        self.frequency_step = 200000000
        frequencies = list(
            range(self.frequency_min, self.frequency_max, self.frequency_step)
        ) + [self.frequency_max]
        self.frequency_divisions = [[1299990000, 1300000000], [2199990000, 2200000000]]
        for div in self.frequency_divisions:
            if div[0] not in frequencies:
                frequencies.append(div[0])
            if div[1] not in frequencies:
                frequencies.append(div[1])
        frequencies = sorted(frequencies)

        # Start with blank cal data dicts
        cal_data = {}

        # Add the simple stuff to new cal format
        cal_data["calibration_datetime"] = "{}Z".format(
            datetime.datetime.utcnow().isoformat()
        )
        cal_data["sensor_uid"] = "SAMPLE_CALIBRATION"

        # Add the frequency divisions to the calibration data
        cal_data["calibration_frequency_divisions"] = []
        for div in self.frequency_divisions:
            cal_data["calibration_frequency_divisions"].append(
                {"lower_bound": div[0], "upper_bound": div[1]}
            )

        # Create the JSON architecture for the calibration data
        cal_data["calibration_data"] = {}
        cal_data["calibration_data"]["sample_rates"] = []
        for k in range(len(self.sample_rates)):
            cal_data_sr = {}
            cal_data_sr["sample_rate"] = self.sample_rates[k]
            cal_data_sr["calibration_data"] = {}
            cal_data_sr["calibration_data"]["frequencies"] = []
            for i in range(len(frequencies)):
                cal_data_f = {}
                cal_data_f["frequency"] = frequencies[i]
                cal_data_f["calibration_data"] = {}
                cal_data_f["calibration_data"]["ref_levels"] = []
                for j in range(len(ref_levels)):
                    cal_data_rl = {}
                    cal_data_rl["reference_level"] = ref_levels[j]

                    # Create the scale factor that ensures easy interpolation
                    gain_sigan = easy_gain(
                        self.sample_rates[k], frequencies[i], ref_levels[j]
                    )

                    # Create the data point
                    cal_data_point = {
                        "gain_sigan": gain_sigan,
                        "noise_figure_sigan": self.dummy_noise_figure,
                        "1dB_compression_sigan": self.dummy_compression,
                    }

                    # Add the generated dicts to the parent lists
                    cal_data_rl["calibration_data"] = deepcopy(cal_data_point)
                    cal_data_f["calibration_data"]["ref_levels"].append(
                        deepcopy(cal_data_rl)
                    )
                cal_data_sr["calibration_data"]["frequencies"].append(
                    deepcopy(cal_data_f)
                )
            cal_data["calibration_data"]["sample_rates"].append(deepcopy(cal_data_sr))

        # Write the new json file
        with open(self.calibration_file, "w+") as file:
            json.dump(cal_data, file, indent=4)

        # Load the data back in
        self.sample_cal = calibration.load_from_json(self.calibration_file)

        # Create a list of previous points to ensure that we don't repeat
        self.pytest_points = []

        # Create sweep lists for test points
        self.srs = self.sample_rates
        self.rli_s = list(
            range(self.reflev_min, self.reflev_max, self.ref_level_step)
        )
        self.fi_s = list(
            range(self.frequency_min, self.frequency_max, self.frequency_step)
        )
        self.rl_s = self.rli_s + [self.reflev_max]
        self.f_s = self.fi_s + [self.frequency_max]

        # Get a list of division frequencies
        self.div_fs = []
        for div in self.frequency_divisions:
            self.div_fs.append(div[0])
            self.div_fs.append(div[1])
        for f in self.div_fs:
            if f in self.f_s:
                self.f_s.remove(f)

        # Don't repeat test setup
        self.setup_complete = True

    def test_sf_bound_points(self):
        """ Test SF determination at boundary points """
        self.run_pytest_point(
            self.srs[0],
            self.frequency_min,
            self.reflev_min,
            "Testing boundary points",
        )
        self.run_pytest_point(
            self.srs[0],
            self.frequency_max,
            self.reflev_max,
            "Testing boundary points",
        )

    def test_sf_no_interpolation_points(self):
        """ Test points without interpolation """
        for i in range(4 * self.test_repeat_times):
            while True:
                rl = self.rl_s[self.rand_index(self.rl_s)]
                f = self.f_s[self.rand_index(self.f_s)]
                if self.run_pytest_point(
                    self.srs[0], f, rl, "Testing no interpolation points"
                ):
                    break

    def test_sf_f_interpolation_points(self):
        """ Test points with frequency interpolation only """
        for i in range(4 * self.test_repeat_times):
            while True:
                rl = self.rl_s[self.rand_index(self.rl_s)]
                f = self.fi_s[self.rand_index(self.fi_s)]
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                if self.run_pytest_point(
                    self.srs[0], f + f_add, rl, "Testing frequency interpolation points"
                ):
                    break

    def test_sf_rl_interpolation_points(self):
        """ Test points with reference level interpolation only """
        for i in range(4 * self.test_repeat_times):
            while True:
                rl = self.rli_s[self.rand_index(self.rli_s)]
                f = self.f_s[self.rand_index(self.f_s)]
                rl_add = random.randint(1, self.ref_level_step - 1)
                if self.run_pytest_point(
                    self.srs[0],
                    f,
                    rl + rl_add,
                    "Testing ref_level interpolation points",
                ):
                    break

    def test_sf_rl_f_interpolation_points(self):
        """ Test points with frequency and reference level interpolation only """
        for i in range(4 * self.test_repeat_times):
            while True:
                rl = self.rli_s[self.rand_index(self.rli_s)]
                f = self.fi_s[self.rand_index(self.fi_s)]
                f_add = random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                rl_add = random.randint(1, self.ref_level_step - 1)
                if self.run_pytest_point(
                    self.srs[0],
                    f + f_add,
                    rl + rl_add,
                    "Testing frequency and ref_level interpolation points",
                ):
                    break

    def test_division_f_points(self):
        """ Test points with division frequencies """
        for i in range(self.test_repeat_times):
            for f in self.div_fs:
                while True:
                    rl = self.rl_s[self.rand_index(self.rl_s)]
                    if self.run_pytest_point(
                        self.srs[0], f, rl, "Testing division frequency points"
                    ):
                        break

    def test_rl_interpolation_division_f_points(self):
        """ Test points with reference level interpolation and division frequencies """
        for i in range(self.test_repeat_times):
            for f in self.div_fs:
                while True:
                    rl = self.rli_s[self.rand_index(self.rli_s)]
                    rl_add = random.randint(1, self.ref_level_step - 1)
                    if self.run_pytest_point(
                        self.srs[0],
                        f,
                        rl + rl_add,
                        "Testing division frequency with ref_level interpolation points",
                    ):
                        break

    def test_in_division_f_points(self):
        """ Test points with in-division frequencies """
        for j in range(self.test_repeat_times):
            for i in range(0, len(self.div_fs), 2):
                while True:
                    f = random.randint(self.div_fs[i] + 1, self.div_fs[i + 1] - 1)
                    a = self.rl_s[self.rand_index(self.rl_s)]
                    if self.run_pytest_point(
                        self.srs[0],
                        f,
                        a,
                        "Testing within division frequency points",
                        f_m=self.div_fs[i],
                    ):
                        break

    def test_rl_interpolation_in_division_f_points(self):
        """ Test points with reference level interpolation and in-division frequencies """
        for j in range(self.test_repeat_times):
            for i in range(0, len(self.div_fs), 2):
                while True:
                    f = random.randint(self.div_fs[i] + 1, self.div_fs[i + 1] - 1)
                    rl = self.rli_s[self.rand_index(self.rli_s)]
                    rl_add = random.randint(1, self.ref_level_step - 1)
                    if self.run_pytest_point(
                        self.srs[0],
                        f,
                        rl + rl_add,
                        "Testing within division frequency with reference level interpolation points",
                        f_m=self.div_fs[i],
                    ):
                        break

    def test_sample_rate_points(self):
        """ Test points with reference level and frequency interpolation at different sample rates """
        for j in range(self.test_repeat_times):
            for i in range(len(self.srs)):
                while True:
                    rl = self.rli_s[self.rand_index(self.rli_s)]
                    f = self.fi_s[self.rand_index(self.fi_s)]
                    f_add = (
                        random.randint(1, int(self.frequency_step / 10e6) - 1) * 10e6
                    )
                    rl_add = random.randint(1, self.ref_level_step - 1)
                    if self.run_pytest_point(
                        self.srs[i],
                        f + f_add,
                        rl + rl_add,
                        "Testing different sample rate points",
                    ):
                        break
