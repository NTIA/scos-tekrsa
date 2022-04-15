import logging
from scos_tekrsa.hardware.tekrsa_sigan import TekRSASigan

logger = logging.getLogger(__name__)
try:
    logger.debug('*********************Creating TekRSASigan******************************')
    sigan = TekRSASigan()
except:
    logger.error('Unable to create TekRSASigan')
    sigan = None