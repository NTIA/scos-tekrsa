"""Set the preselector to noise diode off"""

import logging
import subprocess

from scos_actions.actions.interfaces.action import Action
from scos_tekrsa.hardware import sigan
from scos_actions.hardware import preselector

logger = logging.getLogger(__name__)


class EnableNoiseDiodeOff(Action):
    """Set the preselector to noise diode off"""

    def __init__(self, parameters={'name': 'enable_noise_diode_off'}, sigan=sigan):
        super().__init__(parameters=parameters, sigan=sigan)

    def __call__(self, schedule_entry_json, task_id):
        logger.debug("Enabling antenna")
        preselector.set_rf_path('noise_diode_off')