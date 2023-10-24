import logging

from scos_actions.actions.monitor_sigan import MonitorSignalAnalyzer
from scos_actions.discover import init

from scos_tekrsa.hardware import sigan
from scos_tekrsa.settings import CONFIG_DIR

logger = logging.getLogger(__name__)

actions = {}
logger.debug("scos-tekrsa: discovering actions")
# Adjust ACTION_DEFINITIONS_DIR for specific Tektronix analyzer in use
if sigan:
    logger.debug(f"Device Name: {sigan.device_name}")
    if sigan.device_name in ["RSA306B", "RSA306"]:
        ACTION_DEFINITIONS_DIR = CONFIG_DIR / "actions-300"
    elif sigan.device_name in [
        "RSA503A",
        "RSA507A",
        "RSA513A",
        "RSA518A",
        "RSA603A",
        "RSA607A",
    ]:
        ACTION_DEFINITIONS_DIR = CONFIG_DIR / "actions-500-600"
    else:
        logger.error("Unable to determine RSA model. Defaulting to use RSA500/600 action configs")
        ACTION_DEFINITIONS_DIR = CONFIG_DIR / "actions-500-600"
    logger.debug(f"Action configs directory: {ACTION_DEFINITIONS_DIR}")
    actions["monitor_tekrsa"] = MonitorSignalAnalyzer(
        parameters={"name": "monitor_tekrsa"}, sigan=sigan
    )
    logger.debug("Created Monitor SIGAN action")
    # Pass new radio to existing action classes with new SDR specific yaml files
    logger.debug("Initializing yaml actions")
    yaml_actions, yaml_test_actions = init(sigan=sigan, yaml_dir=ACTION_DEFINITIONS_DIR)
    logger.debug(f"Created {len(yaml_actions)} actions")
    actions.update(yaml_actions)
else:
    logger.warning("Sigan is None")


# Support status endpoint
def get_last_calibration_time():
    return sigan.last_calibration_time
