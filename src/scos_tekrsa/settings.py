import logging
import sys
from pathlib import Path

from environs import Env
from scos_actions.settings import *

logger = logging.getLogger(__name__)
env = Env()

CONFIG_DIR = Path(__file__).parent.resolve() / "configs"

__cmd = Path(sys.argv[0]).name

RUNNING_TESTS = "test" in __cmd
DEVICE_MODEL = env("DEVICE_MODEL", default="RSA507A")
MOCK_SIGAN = env.bool("MOCK_SIGAN", default=False) or RUNNING_TESTS
MOCK_SIGAN_RANDOM = env.bool("MOCK_SIGAN_RANDOM", default=False)
RUNNING_MIGRATIONS = env.bool("RUNNING_MIGRATIONS", default=False)
if RUNNING_TESTS:
    logging.basicConfig(level=logging.DEBUG)
SIGAN_MODULE = env.str("SIGAN_MODULE", default=None)
SIGAN_CLASS = env.str("SIGAN_CLASS", default=None)
if RUNNING_TESTS:
    SIGAN_MODULE = "scos_tekrsa.hardware.tekrsa_sigan"
    SIGAN_CLASS = "TekRSASigan"
logger.debug(f"scos-tekrsa: SIGAN_MODULE:{SIGAN_MODULE}")
logger.debug(f"scos-tekrsa: SIGAN_CLASS:{SIGAN_CLASS}")
