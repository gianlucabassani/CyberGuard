"""Durable, compatibility-safe engagement intent contract."""

import pytest
from pydantic import ValidationError

import api
from auth import Principal


def test_engagement_purpose_contract_accepts_known_values_and_rejects_unknown():
    request = api.EngagementIntentRequest(engagement_purpose="benchmark")
    assert request.engagement_purpose == "benchmark"

    with pytest.raises(ValidationError, match="engagement_purpose"):
        api.EngagementIntentRequest(engagement_purpose="marketing")


def test_engagement_intent_is_append_only_audit_context(monkeypatch):
    recorded = []
    monkeypatch.setattr(
        api.db,
        "record_event",
        lambda *args, **kwargs: recorded.append((args, kwargs)),
    )
    request = api.EngagementIntentRequest(engagement_purpose="discovery")

    api._record_engagement_intent(
        "arena-1",
        request,
        Principal(name="operator-1", role="operator"),
        source="target",
    )

    assert recorded == [
        (
            (
                "arena-1",
                "engagement_intent",
                {
                    "schema": "nidavellir.engagement-intent/v1",
                    "purpose": "discovery",
                    "source": "target",
                },
            ),
            {"actor": "operator-1"},
        )
    ]


def test_omitted_engagement_intent_preserves_compatibility(monkeypatch):
    monkeypatch.setattr(
        api.db,
        "record_event",
        lambda *args, **kwargs: pytest.fail("compatibility request recorded intent"),
    )
    api._record_engagement_intent(
        "arena-1",
        api.EngagementIntentRequest(),
        Principal(name="legacy-client", role="operator"),
        source="challenge",
    )
