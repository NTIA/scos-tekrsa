"""Set the preselector to the antenna"""

import logging

from scos_actions.actions.interfaces.action import Action
from scos_tekrsa.hardware import sigan

logger = logging.getLogger(__name__)


class EnableAntenna(Action):
    """Set the preselector to the antenna"""

    def __init__(self,gps, parameters={}, sigan=sigan):
        super().__init__(parameters=parameters, sigan=sigan, gps=gps)

    def __call__(self, schedule_entry_json, task_id):
        logger.debug("Enabling antenna")
        preselector.set_rf_path('antenna')