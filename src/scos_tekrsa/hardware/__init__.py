import logging

from scos_actions.signals import (
    register_component_with_status,
    register_signal_analyzer
)

from scos_tekrsa.hardware.tekrsa_sigan import TekRSASigan

logger = logging.getLogger(__name__)
try:
    logger.debug(
        "*********************Creating TekRSASigan******************************"
    )
    sigan = TekRSASigan()
    register_component_with_status.send(sigan, component=sigan)
    register_signal_analyzer.send(sigan, signal_analyzer=sigan)
except Exception as err:
    logger.error(f"Unable to create TekRSASigan: {err}")
    sigan = None
