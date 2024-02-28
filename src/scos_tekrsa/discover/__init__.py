import logging

from scos_actions.actions.monitor_sigan import MonitorSignalAnalyzer
from scos_actions.actions.runtime_error_action import RuntimeErrorAction
from scos_actions.actions.system_exit_action import SystemExitAction
from scos_actions.discover import init

from scos_tekrsa.settings import CONFIG_DIR, DEVICE_MODEL

logger = logging.getLogger(__name__)

actions = {}
logger.debug("scos-tekrsa: discovering actions")
# Adjust ACTION_DEFINITIONS_DIR for specific Tektronix analyzer in use
logger.debug(f"Device Model: {DEVICE_MODEL}")
if DEVICE_MODEL in ["RSA306B", "RSA306"]:
    ACTION_DEFINITIONS_DIR = CONFIG_DIR / "actions-300"
elif DEVICE_MODEL in [
    "RSA503A",
    "RSA507A",
    "RSA513A",
    "RSA518A",
    "RSA603A",
    "RSA607A",
]:
    ACTION_DEFINITIONS_DIR = CONFIG_DIR / "actions-500-600"
else:
    logger.error(
        "Unable to determine RSA model. Defaulting to use RSA500/600 action configs"
    )
    ACTION_DEFINITIONS_DIR = CONFIG_DIR / "actions-500-600"
logger.debug(f"Action configs directory: {ACTION_DEFINITIONS_DIR}")
actions["monitor_tekrsa"] = MonitorSignalAnalyzer(parameters={"name": "monitor_tekrsa"})
actions["system_exit"] = SystemExitAction()
actions["runtime_exception"] = RuntimeErrorAction()
logger.debug("Created Monitor SIGAN action")
# Pass new radio to existing action classes with new SDR specific yaml files
logger.debug("Initializing yaml actions")
yaml_actions, yaml_test_actions = init(yaml_dir=ACTION_DEFINITIONS_DIR)
logger.debug(f"Created {len(yaml_actions)} actions")
actions.update(yaml_actions)
