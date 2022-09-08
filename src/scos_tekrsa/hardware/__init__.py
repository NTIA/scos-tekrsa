import logging

from scos_actions.actions.interfaces.signals import register_component_with_status

from scos_tekrsa.hardware.tekrsa_sigan import TekRSASigan

logger = logging.getLogger(__name__)
try:
    logger.info(
        "*********************Creating TekRSASigan******************************"
    )
    sigan = TekRSASigan()
    register_component_with_status.send(sigan, component=sigan)
except Exception as err:
    logger.error(f"Unable to create TekRSASigan: {err}")
    sigan = None
