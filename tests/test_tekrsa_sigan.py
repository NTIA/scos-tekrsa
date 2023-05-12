"""Test aspects of SignalAnalyzerInterface with mocked Tektronix RSA."""

from collections import Counter

import numpy as np
import pytest

import scos_tekrsa.hardware.tekrsa_constants as rsa_constants
from scos_tekrsa.hardware import sigan
from scos_tekrsa.hardware.mocks.rsa_block import (
    MAX_CENTER_FREQ,
    MAX_IQ_BW,
    MIN_CENTER_FREQ,
    MIN_IQ_BW,
    TIMES_TO_FAIL,
)


class TestTekRSA:
    # Ensure we write the test cal file and use mocks
    setup_complete = False

    @pytest.fixture(autouse=True)
    def setup_mock_tekrsa(self):
        """Create mock Tektronix RSA 507A"""
        if self.setup_complete:
            return
        self.rx = sigan
        self.CORRECT_ALLOWED_SR = rsa_constants.IQSTREAM_ALLOWED_SR
        self.CORRECT_ALLOWED_BW = rsa_constants.IQSTREAM_ALLOWED_BW
        self.CORRECT_SR_BW_MAP = rsa_constants.IQSTREAM_SR_BW_MAP
        self.CORRECT_MAX_REFERENCE_LEVEL = rsa_constants.MAX_REFERENCE_LEVEL
        self.CORRECT_MIN_REFERENCE_LEVEL = rsa_constants.MIN_REFERENCE_LEVEL
        self.CORRECT_MAX_ATTENUATION = rsa_constants.MAX_ATTENUATION
        self.CORRECT_MIN_ATTENUATION = rsa_constants.MIN_ATTENUATION
        self.setup_complete = True

    def test_sigan_constants(self):
        # Check that the SignalAnalyzerInterface loads constants correctly
        assert Counter(self.CORRECT_ALLOWED_SR) == Counter(self.rx.ALLOWED_SR)
        assert self.rx.max_sample_rate == max(self.CORRECT_ALLOWED_SR)
        assert Counter(self.CORRECT_ALLOWED_BW) == Counter(self.rx.ALLOWED_BW)
        assert self.CORRECT_SR_BW_MAP == self.rx.SR_BW_MAP
        assert self.rx.max_reference_level == self.CORRECT_MAX_REFERENCE_LEVEL
        assert self.rx.min_reference_level == self.CORRECT_MIN_REFERENCE_LEVEL
        assert self.rx.max_attenuation == self.CORRECT_MAX_ATTENUATION
        assert self.rx.min_attenuation == self.CORRECT_MIN_ATTENUATION

    def test_get_constraints(self):
        # get_constraints runs at the end of the connect
        # method, whether using a real or mocked RSA. These are
        # device-dependent. Here the values are compared to those
        # set for the mock RSA, which just ensures get_constraints()
        # has run successfully on initialization.
        assert self.rx.min_frequency == MIN_CENTER_FREQ
        assert self.rx.max_frequency == MAX_CENTER_FREQ
        assert self.rx.min_iq_bandwidth == MIN_IQ_BW
        assert self.rx.max_iq_bandwidth == MAX_IQ_BW
        assert self.rx.get_constraints() is None

    # Test SignalAnalyzerInterface properties

    def test_is_available(self):
        assert self.rx.is_available == True
        assert isinstance(self.rx.is_available, bool)

    def test_sample_rate(self):
        assert isinstance(self.rx.sample_rate, (float, int))

        for sr in self.CORRECT_ALLOWED_SR:
            setattr(self.rx, "sample_rate", sr)
            assert self.rx.sample_rate == sr
            # Bandwidth should update when sample rate is set
            assert self.rx.iq_bandwidth == self.CORRECT_SR_BW_MAP[sr]

        with pytest.raises(ValueError):
            # Requested sample rate too high
            setattr(self.rx, "sample_rate", self.rx.max_sample_rate + 1)

        with pytest.raises(ValueError):
            # Requested sample rate invalid
            setattr(self.rx, "sample_rate", max(self.CORRECT_ALLOWED_SR) - 1)

    def test_iq_bandwidth(self):
        assert isinstance(self.rx.iq_bandwidth, (float, int))

        for bw in self.CORRECT_ALLOWED_BW:
            setattr(self.rx, "iq_bandwidth", bw)
            assert self.rx.iq_bandwidth == bw
            # Sample rate should update when bandwidth is set
            assert self.rx.sample_rate == rsa_constants.IQSTREAM_BW_SR_MAP[bw]

        with pytest.raises(ValueError):
            # Requested bandwidth invalid
            setattr(self.rx, "iq_bandwidth", max(self.CORRECT_ALLOWED_BW) + 1)

    def test_frequency(self):
        assert isinstance(self.rx.frequency, (float, int))

        for cf in np.linspace(self.rx.min_frequency, self.rx.max_frequency, 10):
            setattr(self.rx, "frequency", cf)
            assert self.rx.frequency == cf

    def test_reference_level(self):
        assert isinstance(self.rx.reference_level, (float, int))

        for rl in np.linspace(
            self.rx.min_reference_level, self.rx.max_reference_level, 10
        ):
            setattr(self.rx, "reference_level", rl)
            assert self.rx.reference_level == rl

    def test_attenuation(self):
        assert isinstance(self.rx.attenuation, (float, int))

        for a in np.linspace(self.rx.min_attenuation, self.rx.max_attenuation, 10):
            setattr(self.rx, "attenuation", a)
            assert self.rx.attenuation == a

        with pytest.raises(ValueError):
            # Requested attenuation too high
            setattr(self.rx, "attenuation", self.rx.max_attenuation + 1)

        # Test handling for RSA without manual attenuator
        old_dev_name = self.rx.device_name
        setattr(self.rx, "device_name", "RSA306B")
        assert self.rx.attenuation is None
        setattr(self.rx, "attenuation", 50)
        assert self.rx.attenuation is None
        setattr(self.rx, "device_name", old_dev_name)

    def test_preamp_enable(self):
        assert isinstance(self.rx.preamp_enable, bool)

        setattr(self.rx, "preamp_enable", False)
        assert self.rx.preamp_enable == False
        setattr(self.rx, "preamp_enable", True)
        assert self.rx.preamp_enable == True

        # Test handling for RSA without preamp
        old_dev_name = self.rx.device_name
        setattr(self.rx, "device_name", "RSA306B")
        assert self.rx.preamp_enable is None
        setattr(self.rx, "preamp_enable", False)
        assert self.rx.preamp_enable is None
        setattr(self.rx, "device_name", old_dev_name)

    def test_acquire_samples_retry(self):
        # Not enough retries = acquisition should fail
        # The mocked IQ capture function will fail the first
        # TIMES_TO_FAIL times it is called consecutively.

        # With retries=0, IQ capture should fail TIMES_TO_FAIL times
        for i in range(TIMES_TO_FAIL):
            with pytest.raises(RuntimeError):
                _ = self.rx.acquire_time_domain_samples(
                    100, retries=0, cal_adjust=False
                )

        # With retries>TIMES_TO_FAIL, IQ capture should succeed
        # In this case, IQ capture fails TIMES_TO_FAIL times within
        # acquire_time_domain_samples, which handles the retry logic until
        # the IQ acquisition succeeds.
        self.rx.rsa.set_times_to_fail(TIMES_TO_FAIL)  # Reset times_failed
        _ = self.rx.acquire_time_domain_samples(
            100, retries=TIMES_TO_FAIL + 1, cal_adjust=False
        )

    def test_acquire_samples(self):
        setattr(self.rx, "iq_bandwidth", max(self.CORRECT_ALLOWED_BW))

        # Test non-data measurement result components
        r = self.rx.acquire_time_domain_samples(
            int(self.rx.iq_bandwidth * 0.001), cal_adjust=False
        )
        assert r["frequency"] == self.rx.frequency
        assert r["overload"] == False
        assert r["reference_level"] == self.rx.reference_level
        assert r["sample_rate"] == self.rx.sample_rate
        assert r["attenuation"] == self.rx.attenuation
        assert r["preamp_enable"] == self.rx.preamp_enable
        assert isinstance(r["capture_time"], str)  # Can't predict this value

        # Attenuation/preamp keys should not exist for RSA30X
        old_dev_name = self.rx.device_name
        setattr(self.rx, "device_name", "RSA306B")
        r = self.rx.acquire_time_domain_samples(
            int(self.rx.iq_bandwidth * 0.001), cal_adjust=False
        )
        with pytest.raises(KeyError):
            _ = r["attenuation"]
        with pytest.raises(KeyError):
            _ = r["preamp_enable"]
        setattr(self.rx, "device_name", old_dev_name)

        # Acquire n_samps resulting in integer number of milliseconds
        for duration_ms in [1, 2, 3, 7, 10]:
            n_samps = int(self.rx.iq_bandwidth * duration_ms * 0.001)
            result = self.rx.acquire_time_domain_samples(n_samps, cal_adjust=False)
            assert len(result["data"]) == n_samps

        # Acquire n_samps resulting in non-integer milliseconds
        for duration_ms in [1.1, 2.02, 3.3, 7.007, 10.05]:
            n_samps = int(self.rx.iq_bandwidth * duration_ms * 0.001)
            result = self.rx.acquire_time_domain_samples(n_samps, cal_adjust=False)
            assert len(result["data"]) == n_samps

        # Calibration data is not loaded, cal_adjust should fail
        with pytest.raises(Exception):
            _ = self.rx.acquire_time_domain_samples(100)

        # Non-integer n_samps should fail
        with pytest.raises(ValueError):
            _ = self.rx.acquire_time_domain_samples(1.01, cal_adjust=False)

        # Test with skipping samples
        r = self.rx.acquire_time_domain_samples(
            int(self.rx.iq_bandwidth * 0.001), 100, cal_adjust=False
        )
        assert len(r["data"]) == int(self.rx.iq_bandwidth * 0.001)
