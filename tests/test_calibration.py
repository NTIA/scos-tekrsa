import pytest
from scos_actions.calibration import get_sensor_calibration

from scos_tekrsa.settings import CONFIG_DIR


class TestCalibration:
    def test_sensor_calibration(self):
        sensor_calibration = get_sensor_calibration(
            CONFIG_DIR / "sensor_calibration_example.json"
        )
        assert sensor_calibration is not None
        assert (
            sensor_calibration.calibration_data["14000000.0"]["3555000000"]["-25"][
                "true"
            ]["0"]["noise_figure"]
            == 5.0
        )
        assert isinstance(sensor_calibration.calibration_data, dict)
        assert isinstance(sensor_calibration.last_calibration_datetime, str)
        assert isinstance(sensor_calibration.calibration_parameters, list)
