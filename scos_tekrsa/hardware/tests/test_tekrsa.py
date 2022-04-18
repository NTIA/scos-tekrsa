"""Test aspects of SignalAnalyzerInterface with mocked Tektronix RSA."""

import pytest

from scos_tekrsa.hardware import sigan


class TestTekRSA:
    # Ensure we write the test cal file and use mocks
    setup_complete = False

    @pytest.fixture(autouse=True)
    def setup_mock_tekrsa(self):
        """Create mock Tektronix RSA 306B"""
        if self.setup_complete:
            return
        
        if not sigan.is_available:
            raise RuntimeError("Receiver is not available.")
        self.rx = sigan
        self.setup_complete = True

    