"""Set the preselector to noise diode on"""

import logging
import subprocess

from scos_actions.actions.interfaces.action import Action
from scos_tekrsa.hardware import sigan

logger = logging.getLogger(__name__)


class EnableNoiseDiodeOn(Action):
    """Set the preselector to noise diode on"""

    def __init__(self, parameters={}, sigan=sigan):
        super().__init__(parameters=parameters, sigan=sigan)

    def __call__(self, schedule_entry_json, task_id):
        logger.debug("Enabling antenna")
        preselector.set_rf_path('noise_diode_on')