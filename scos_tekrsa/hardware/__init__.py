import logging
from scos_tekrsa.hardware.tekrsa_sigan import TekRSASigan

logger = logging.getLogger(__name__)
logger.debug('Creating TekRSASigan')
sigan = TekRSASigan()
