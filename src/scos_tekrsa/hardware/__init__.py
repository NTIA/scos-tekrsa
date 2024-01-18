import logging

from scos_actions.hardware.utils import load_switches
from scos_tekrsa.hardware.tekrsa_sigan import TekRSASigan
from scos_tekrsa import settings

logger = logging.getLogger(__name__)
try:
    if not settings.RUNNING_MIGRATIONS:
        logger.debug(
            "*********************Creating TekRSASigan******************************"
        )
        logger.debug("Tekrsa: loading switches")
        switches = load_switches(settings.SWITCH_CONFIGS_DIR)
        sigan = TekRSASigan(switches = switches)
    else:
        logger.debug("Running migrations. Not creating signal analyzer.")
        sigan = None
except Exception as err:
    logger.error(f"Unable to create TekRSASigan: {err}")
    sigan = None
