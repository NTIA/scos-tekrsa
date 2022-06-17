"""Set the preselector to the antenna"""

import logging

from scos_actions.actions.interfaces.action import Action
from scos_tekrsa.hardware import sigan
from scos_actions.hardware import preselector

logger = logging.getLogger(__name__)


class EnableAntenna(Action):
    """Set the preselector to the antenna"""

    def __init__(self, parameters={'name':'enable_antenna'}, sigan=sigan):
        super().__init__(parameters=parameters, sigan=sigan)

    def __call__(self, schedule_entry_json, task_id):
        logger.debug("Enabling antenna")
        preselector.set_state('antenna')

    def add_metadata_generators(self, measurement_result):
        pass

    def create_metadata(self, schedule_entry, measurement_result):
        pass

    def send_signals(self, measurement_result):
        pass

    def test_required_components(self):
        pass