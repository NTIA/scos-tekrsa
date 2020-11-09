from scos_tekrsa.hardware.tekrsa_radio import RSARadio
from scos_tekrsa.settings import RUNNING_TESTS

if not RUNNING_TESTS:
	radio = RSARadio()