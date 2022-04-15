import logging
from os import path

from scos_actions.actions.monitor_sigan import MonitorSignalAnalyzer
from scos_actions.actions.sync_gps import SyncGps
from scos_actions.discover import init
from scos_tekrsa.actions.enable_antenna import EnableAntenna
from scos_tekrsa.actions.enable_noise_diode_on import EnableNoiseDiodeOn
from scos_tekrsa.actions.enable_noise_diode_off import EnableNoiseDiodeOff
from scos_tekrsa.hardware import sigan
from scos_tekrsa.settings import ACTION_DEFINITIONS_DIR

logger = logging.getLogger(__name__)

actions = {"enable_antenna": EnableAntenna(sigan=sigan), 'enable_noise_diode_on': EnableNoiseDiodeOn(sigan=sigan),
           'enable_noise_diode_off': EnableNoiseDiodeOff(sigan=sigan)}
logger.info('scos-tekrsa: discovering actions')
# Adjust ACTION_DEFINITIONS_DIR for specific Tektronix analyzer in use
if sigan:
    logger.debug("Devine Name: " + sigan.device_name)
    if sigan.device_name in ['RSA306B', 'RSA306']:
        ACTION_DEFINITIONS_DIR += '-300'
    elif sigan.device_name in ['RSA503A', 'RSA507A', 'RSA513A', 'RSA518A', 'RSA603A', 'RSA607A']:
        ACTION_DEFINITIONS_DIR += '-500-600'
    else:
        logger.error("Unable to determine RSA model")
        ACTION_DEFINITIONS_DIR += '-500-600'
    logger.debug('Action dir: ' + ACTION_DEFINITIONS_DIR)
    actions["monitor_tekrsa"] = MonitorSignalAnalyzer(sigan)
    logger.debug('Created Monitor SIGAN action')
    # Pass new radio to existing action classes with new SDR specific yaml files
    logger.debug("Initializing yaml actions")
    yaml_actions, yaml_test_actions = init(sigan=sigan, yaml_dir=ACTION_DEFINITIONS_DIR)
    logger.debug('Created ' + str(len(yaml_actions)) + ' actions')
    actions.update(yaml_actions)
else:
    logger.warning('Sigan is null')


# Support status endpoint
def get_last_calibration_time():
    return sigan.last_calibration_time
