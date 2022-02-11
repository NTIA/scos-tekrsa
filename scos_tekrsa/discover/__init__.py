import logging
from os import path

from scos_actions.actions.monitor_radio import RadioMonitor
from scos_actions.actions.sync_gps import SyncGps
from scos_actions.discover import init

from scos_tekrsa.hardware import radio
from scos_tekrsa.settings import ACTION_DEFINITIONS_DIR

# Adjust ACTION_DEFINITIONS_DIR for specific Tektronix analyzer in use
if radio.device_name in ['RSA306B', 'RSA306']:
    ACTION_DEFINITIONS_DIR += '-300'
elif radio.device_name in ['RSA503A', 'RSA507A', 'RSA513A', 'RSA518A', 'RSA603A', 'RSA607A']:
    ACTION_DEFINITIONS_DIR += '-500-600'

logger = logging.getLogger(__name__)

actions = {
    "monitor_tekrsa": RadioMonitor(radio)
}

# Pass new radio to existing action classes with new SDR specific yaml files
logger.debug("scos_tekrsa: ACTION_DEFINITIONS_DIR =  " + ACTION_DEFINITIONS_DIR)
yaml_actions, yaml_test_actions = init(radio=radio, yaml_dir=ACTION_DEFINITIONS_DIR)
actions.update(yaml_actions)

# Support status endpoint
def get_last_calibration_time():
    return radio.last_calibration_time
