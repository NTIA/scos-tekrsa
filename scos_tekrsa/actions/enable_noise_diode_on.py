"""Set the preselector to noise diode on"""

import logging
import subprocess

from scos_actions.actions.interfaces.action import Action
from scos_tekrsa.hardware import sigan
from scos_actions.hardware import preselector

logger = logging.getLogger(__name__)


class EnableNoiseDiodeOn(Action):
    """Set the preselector to noise diode on"""

    def __init__(self, parameters={'name': 'enable_noise_diode_on'}, sigan=sigan):
        super().__init__(parameters=parameters, sigan=sigan)

    def __call__(self, schedule_entry_json, task_id):
        logger.debug("Enabling antenna")
        preselector.set_state('noise_diode_on')

    def add_metadata_decorators(self, measurement_result):
        pass

    def create_metadata(self, schedule_entry, measurement_result):
        pass