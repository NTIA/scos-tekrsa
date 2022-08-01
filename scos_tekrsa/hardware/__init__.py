import logging

from scos_tekrsa.hardware.tekrsa_sigan import TekRSASigan

logger = logging.getLogger(__name__)
try:
    logger.info(
        "*********************Creating TekRSASigan******************************"
    )
    sigan = TekRSASigan()
except Exception as err:
    logger.error(f"Unable to create TekRSASigan: {err}")
    sigan = None
