import datetime
from scos_tekrsa.hardware.calibration import Calibration

# Notes:
# easy_gain currently uses (30 - reference_level) as "gain"
# dummy calibration may need to be updated / is untested

def easy_gain(sr, f, rl):
    """Create an easily interpolated value."""
    return (30-rl)*(sr/1e6)*(f/1e9)

def create_dummy_calibration(empty_cal=False):
    """Create a dummy calibration object"""

    # Define the calibration file steps
    sample_rates = [14e6, 28e6, 56e6]
    reference_levels = [-40, -20, 0, 20]
    frequencies = [1e9, 2e9, 3e9, 4e9]

    # Create the datetime
    calibration_datetime = "{}Z".format(datetime.datetime.utcnow().isoformat())

    # Create the frequency divisions
    calibration_frequency_divisions = []

    # Create the actual data if not an empty cal file
    calibration_data = {}
    if not empty_cal:
        for sr in sample_rates:
            for f in frequencies:
                for rl in reference_levels:
                    # initialize dictionaries
                    if sr not in calibration_data.keys():
                        calibration_data[sr] = {}
                    if f not in calibration_data[sr].keys():
                        calibration_data[sr][f] = {}
                    calibration_data[sr][f][rl] = {
                        "gain_sigan": easy_gain(sr, f, rl),
                        "gain_preselector": -10,
                        "gain_sensor": easy_gain(sr, f, rl) - 10,
                        "1db_compression_sensor": 1,
                    }
    else:  # Create an empty calibration file
        calibration_data = {  # Empty calibration file data
            10e6: {1e9: {-30: {}, 0: {}}, 2e9: {-30: {}, 0: {}}}
        }

    return Calibration(
        calibration_datetime,
        calibration_data,
        calibration_sample_clock_rate_lookup,
        calibration_frequency_divisions,
    )