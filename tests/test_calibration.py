import pytest
from scos_actions.calibration import get_sensor_calibration, get_sigan_calibration

from scos_tekrsa.settings import CONFIG_DIR


class TestCalibration:
    def test_sigan_calibration(self):
        sigan_calibration = get_sigan_calibration(
            CONFIG_DIR / "sigan_calibration_example.json"
        )
        assert sigan_calibration is not None
        assert isinstance(sigan_calibration.calibration_data, dict)
        assert isinstance(sigan_calibration.calibration_datetime, str)
        assert isinstance(sigan_calibration.calibration_parameters, list)
        assert (
            sigan_calibration.calibration_data[14000000.0][3555000000][-25][1][0][
                "noise_figure_sigan"
            ]
            == 46.03993010994134
        )

    def test_sensor_calibration(self):
        sensor_calibration = get_sensor_calibration(
            CONFIG_DIR / "sensor_calibration_example.json"
        )
        assert sensor_calibration is not None
        assert (
            sensor_calibration.calibration_data[14000000.0][3555000000][-25][1][0][
                "noise_figure_sensor"
            ]
            == 5.0
        )
        assert isinstance(sensor_calibration.calibration_data, dict)
        assert isinstance(sensor_calibration.calibration_datetime, str)
        assert isinstance(sensor_calibration.calibration_parameters, list)
