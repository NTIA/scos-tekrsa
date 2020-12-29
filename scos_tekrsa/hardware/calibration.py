import json
import logging

logger = logging.getLogger(__name__)

# Define the default calibration dicts
DEFAULT_SIGAN_CALIBRATION = {
    "gain_sigan": None,  # Defaults to gain setting
    "enbw_sigan": None,  # Defaults to sample rate
    "noise_figure_sigan": 0,
    "1db_compression_sigan": 100,
}

DEFAULT_SENSOR_CALIBRATION = {
    "gain_sensor": None,  # Defaults to sigan gain
    "enbw_sensor": None,  # Defaults to sigan enbw
    "noise_figure_sensor": None,  # Defaults to sigan noise figure
    "1db_compression_sensor": None,  # Defaults to sigan compression + preselector gain
    "gain_preselector": 0,
    "noise_figure_preselector": 0,
    "1db_compression_preselector": 100,
}

class Calibration(object):
    def __init__(
        self,
        calibration_datetime,
        calibration_data,
        calibration_frequency_divisions=None,
    ):
        self.calibration_datetime = calibration_datetime
        self.calibration_data = calibration_data
        self.calibration_frequency_divisions = sorted(
            calibration_frequency_divisions,
            key=lambda division: division["lower_bound"],
        )

    def get_calibration_dict(self, sample_rate, lo_frequency, reference_level):
        """Find the calibration points closest to the current frequency/reference level."""

        # Check if the sample rate was calibrated
        sr = freq_to_compare(sample_rate)
        srs = sorted(self.calibration_data.keys())
        if sr not in srs:
            logger.warning("Requested sample rate was not calibrated!")
            return {}  # if out of range, do not return any calibration data

        # Get the nearest calibrated frequency and its index
        f = lo_frequency
        fs = sorted(self.calibration_data[sr].keys())
        f_i = -1
        if f < fs[0]:  # Frequency below calibrated range
            logger.warning("Tuned frequency is below calibrated range!")
            return {}  # if out of range, do not return any calibration data
        elif f > fs[-1]:  # Frequency above calibrated range
            logger.warning("Tuned frequency is above calibrated range!")
            return {}  # if out of range, do not return any calibration data
        else:
            # Check if we are within a frequency division
            for div in self.calibration_frequency_divisions:
                if f > div["lower_bound"] and f < div["upper_bound"]:
                    logger.warning("Tuned frequency within a division!")
                    logger.warning("Assuming frequency at lower bound:")
                    logger.warning("    Tuned frequency:   {}".format(f))
                    logger.warning(
                        "    Lower bound:       {}".format(div["lower_bound"])
                    )
                    logger.warning(
                        "    Upper bound:       {}".format(div["upper_bound"])
                    )
                    logger.warning(
                        "    Assumed frequency: {}".format(div["lower_bound"])
                    )
                    f = div["lower_bound"]  # Interpolation will force this point; no interpolation error
            # Determine the index associated with the closest frequency less than or equal to f
            for i in range(len(fs) - 1):
                f_i = i
                # If the next frequency is larger, we're done
                if fs[i + 1] > f:
                    break

        # Get the nearest calibrated reference level and its index
        ref_level_setting = reference_level
        ref_levels = sorted(self.calibration_data[sr][fs[f_i]].keys())
        ref_levels_index = -1
        if ref_level_setting < ref_levels[0]:  # Reference level below calibrated range
            logger.warning("Current reference level is below calibrated range!")
            return {}  # if out of range, do not return any calibration data
        elif ref_level_setting > ref_levels[-1]:  # Reference level above calibrated range
            logger.warning("Current reference level is above calibrated range!")
            return {}  # if out of range, do not return any calibration data
        else:
            # Determine the index associated with the closest reference level less than or equal to ref_level_setting
            for i in range(len(ref_levels) - 1):
                ref_levels_index = i
                # If the next reference level is larger, we're done
                if ref_levels[i + 1] > ref_level_setting:
                    break

        # Get the list of calibration factors
        calibration_factors = self.calibration_data[sr][fs[f_i]][
            ref_levels[ref_levels_index]
        ].keys()

        # Interpolate as needed for each calibration point
        interpolated_calibration = {}
        for cal_factor in calibration_factors:
            factor = self.interpolate_2d(
                f,
                ref_level_setting,
                fs[f_i],
                fs[f_i + 1],
                ref_levels[ref_levels_index],
                ref_levels[ref_levels_index + 1],
                self.calibration_data[sr][fs[f_i]][ref_levels[ref_levels_index]][
                    cal_factor
                ],
                self.calibration_data[sr][fs[f_i + 1]][
                    ref_levels[ref_levels_index]
                ][cal_factor],
                self.calibration_data[sr][fs[f_i]][
                    ref_levels[ref_levels_index + 1]
                ][cal_factor],
                self.calibration_data[sr][fs[f_i + 1]][
                    ref_levels[ref_levels_index + 1]
                ][cal_factor],
            )

            # Add the calibration factor to the interpolated list
            interpolated_calibration[cal_factor] = factor

        # Return the interpolated calibration factors
        return interpolated_calibration

    def interpolate_1d(self, x, x1, x2, y1, y2):
        """Interpolate between points in one dimension."""
        return y1 * (x2 - x) / (x2 - x1) + y2 * (x - x1) / (x2 - x1)

    def interpolate_2d(self, x, y, x1, x2, y1, y2, z11, z21, z12, z22):
        """Interpolate between points in two dimensions."""
        z_y1 = self.interpolate_1d(x, x1, x2, z11, z21)
        z_y2 = self.interpolate_1d(x, x1, x2, z12, z22)
        return self.interpolate_1d(y, y1, y2, z_y1, z_y2)


def freq_to_compare(f):
    """Allow a frequency of type [float] to be compared with =="""
    f = int(round(f))
    return f


def load_from_json(fname):
    with open(fname) as file:
        calibration = json.load(file)

    # Check that the required fields are in the dict
    assert "calibration_datetime" in calibration
    assert "calibration_frequency_divisions" in calibration
    assert "calibration_data" in calibration

    # Load all the calibration data
    calibration_data = {}
    for sample_rate_row in calibration["calibration_data"]["sample_rates"]:
        sr = freq_to_compare(sample_rate_row["sample_rate"])
        for frequency_row in sample_rate_row["calibration_data"]["frequencies"]:
            f = frequency_row["frequency"]
            for ref_level_row in frequency_row["calibration_data"]["ref_levels"]:
                rl = ref_level_row["reference_level"]
                cal_point = ref_level_row["calibration_data"]

                # Initialize dictionaries
                if sr not in calibration_data.keys():
                    calibration_data[sr] = {}
                if f not in calibration_data[sr].keys():
                    calibration_data[sr][f] = {}
                calibration_data[sr][f][rl] = cal_point

    # Create and return the Calibration object
    return Calibration(
        calibration["calibration_datetime"],
        calibration_data,
        calibration["calibration_frequency_divisions"],
    )
