import logging

from scos_tekrsa.hardware.tekrsa_sigan import TekRSASigan
from scos_tekrsa import settings

logger = logging.getLogger(__name__)
try:
    if not settings.RUNNING_MIGRATIONS:
        logger.debug(
            "*********************Creating TekRSASigan******************************"
        )
        sigan = TekRSASigan()
    else:
        logger.debug("Running migrations. Not creating signal analyzer.")
        sigan = None
except Exception as err:
    logger.error(f"Unable to create TekRSASigan: {err}")
    sigan = None
