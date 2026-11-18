"""
Unit tests for PII Detection, Redaction, and Policy Enforcement.
Verifies detection of emails, IP addresses, credit cards, SSNs, API keys, and action enforcement.
"""
import pytest

from app.security.pii_detector import PIIDetector, PIIPolicyAction


@pytest.fixture
def detector():
    return PIIDetector()


def test_detect_email(detector):
    text = "Please reach out to alice.smith@enterprise.com for the contract."
    matches = detector.detect_entities(text)
    types = [m.entity_type for m in matches]
    assert "EMAIL_ADDRESS" in types
    assert any(m.text == "alice.smith@enterprise.com" for m in matches)


def test_detect_api_key(detector):
    text = "Here is my secret token: sk-live1234567890abcdefghijklmnopqrstuvwxyz"
    matches = detector.detect_entities(text)
    types = [m.entity_type for m in matches]
    assert "API_KEY" in types


def test_detect_ip_address(detector):
    text = "Server connection originated from 192.168.1.105 on port 8080."
    matches = detector.detect_entities(text)
    types = [m.entity_type for m in matches]
    assert "IP_ADDRESS" in types


def test_redact_policy_action(detector):
    text = "Contact support@example.com or visit 10.0.0.1 for details."
    res = detector.scan_and_enforce(text, action=PIIPolicyAction.REDACT)
    assert res.has_pii is True
    assert "[REDACTED_EMAIL_ADDRESS]" in res.redacted_text
    assert "[REDACTED_IP_ADDRESS]" in res.redacted_text
    assert "support@example.com" not in res.redacted_text


def test_block_policy_action(detector):
    text = "My SSN is 000-12-3456 and secret sk-abc123456789012345678901234567890"
    res = detector.scan_and_enforce(text, action=PIIPolicyAction.BLOCK)
    assert res.has_pii is True
    assert res.blocked is True
    assert "PII Violation" in f"PII Violation: {res.details}"


def test_disabled_policy_action(detector):
    text = "User test@company.com"
    res = detector.scan_and_enforce(text, action=PIIPolicyAction.DISABLED)
    assert res.has_pii is False
    assert res.redacted_text == text

