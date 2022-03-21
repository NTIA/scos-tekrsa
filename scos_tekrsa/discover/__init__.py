import logging
from os import path

from scos_actions.actions.monitor_sigan import MonitorSignalAnalyzer
from scos_actions.actions.sync_gps import SyncGps
from scos_actions.discover import init

from scos_tekrsa.hardware import sigan
from scos_tekrsa.settings import ACTION_DEFINITIONS_DIR

logger = logging.getLogger(__name__)

actions = {}
logger.exception('scos-tekrsa: discovering actions')
# Adjust ACTION_DEFINITIONS_DIR for specific Tektronix analyzer in use
if sigan:
    if sigan.device_name in ['RSA306B', 'RSA306']:
        ACTION_DEFINITIONS_DIR += '-300'
    elif sigan.device_name in ['RSA503A', 'RSA507A', 'RSA513A', 'RSA518A', 'RSA603A', 'RSA607A']:
        ACTION_DEFINITIONS_DIR += '-500-600'
    else:
        logger.error("Unable to determine RSA model")
        ACTION_DEFINITIONS_DIR += '-500-600'
    actions["monitor_tekrsa"] = MonitorSignalAnalyzer(sigan)

    # Pass new radio to existing action classes with new SDR specific yaml files
    logger.debug("scos_tekrsa: ACTION_DEFINITIONS_DIR =  " + ACTION_DEFINITIONS_DIR)
    yaml_actions, yaml_test_actions = init(sigan=sigan, yaml_dir=ACTION_DEFINITIONS_DIR)
    actions.update(yaml_actions)
else:
    logger.info('Sigan is null')




# Support status endpoint
def get_last_calibration_time():
    return sigan.last_calibration_time
