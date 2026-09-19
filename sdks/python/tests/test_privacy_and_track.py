"""PII guard + resilient tracking."""

from __future__ import annotations

import pytest

from mallard_sdk import Mallard, PIIError, assert_no_pii


def test_pii_key_rejected() -> None:
    with pytest.raises(PIIError):
        assert_no_pii({"email": "x@y.com"})


def test_pii_email_value_rejected() -> None:
    with pytest.raises(PIIError):
        assert_no_pii({"contact": "x@y.com"})


def test_clean_props_ok() -> None:
    assert_no_pii({"sku_count": 3, "country": "US"})  # no raise


def test_track_rejects_pii() -> None:
    client = Mallard()
    with pytest.raises(PIIError):
        client.track("user-1", "signup", props={"email": "x@y.com"})


def test_get_variant_requires_pseudonymous_unit() -> None:
    with pytest.raises(PIIError):
        Mallard().get_variant("exp", "x@y.com")


def test_flush_never_throws_when_unreachable() -> None:
    client = Mallard(base_url="http://127.0.0.1:9")  # nothing listening
    client.track("user-1", "purchase", value=42.0, props={"sku_count": 3})
    client.flush()  # must not raise
