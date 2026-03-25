"""Tests for halt.core and halt.templates."""

import pytest

from halt import EvaluationResult, RuleEngine, StripeHalt


# ---------------------------------------------------------------------------
# EvaluationResult helpers
# ---------------------------------------------------------------------------


class TestEvaluationResult:
    def test_allowed_property(self):
        result = EvaluationResult(status="ALLOW", reason="ok")
        assert result.allowed is True
        assert result.blocked is False

    def test_blocked_property(self):
        result = EvaluationResult(status="BLOCKED", reason="no")
        assert result.blocked is True
        assert result.allowed is False

    def test_frozen(self):
        result = EvaluationResult(status="ALLOW", reason="ok")
        with pytest.raises((AttributeError, TypeError)):
            result.status = "BLOCKED"  # type: ignore[misc]


# ---------------------------------------------------------------------------
# RuleEngine – basic flow
# ---------------------------------------------------------------------------


class TestRuleEngineBasic:
    def test_empty_engine_allows_anything(self):
        engine = RuleEngine()
        result = engine.evaluate({"action": "charge", "amount": 100})
        assert result.status == "ALLOW"

    def test_non_dict_payload_is_blocked(self):
        engine = RuleEngine()
        result = engine.evaluate("not a dict")  # type: ignore[arg-type]
        assert result.blocked
        assert "dict" in result.reason.lower()

    def test_none_payload_is_blocked(self):
        engine = RuleEngine()
        result = engine.evaluate(None)  # type: ignore[arg-type]
        assert result.blocked


# ---------------------------------------------------------------------------
# RuleEngine – blocked_actions
# ---------------------------------------------------------------------------


class TestBlockedActions:
    def setup_method(self):
        self.engine = RuleEngine(blocked_actions=["delete_customer", "nuke"])

    def test_safe_action_passes(self):
        result = self.engine.evaluate({"action": "charge"})
        assert result.allowed

    def test_blocked_action_is_blocked(self):
        result = self.engine.evaluate({"action": "delete_customer"})
        assert result.blocked
        assert "delete_customer" in result.reason

    def test_another_blocked_action(self):
        result = self.engine.evaluate({"action": "nuke"})
        assert result.blocked

    def test_no_action_field_passes(self):
        """Payloads without an 'action' key should not trigger the action check."""
        result = self.engine.evaluate({"amount": 10})
        assert result.allowed


# ---------------------------------------------------------------------------
# RuleEngine – max_amount
# ---------------------------------------------------------------------------


class TestMaxAmount:
    def setup_method(self):
        self.engine = RuleEngine(max_amount=1000.0)

    def test_amount_under_limit_passes(self):
        result = self.engine.evaluate({"action": "charge", "amount": 500})
        assert result.allowed

    def test_amount_at_limit_passes(self):
        result = self.engine.evaluate({"action": "charge", "amount": 1000})
        assert result.allowed

    def test_amount_over_limit_is_blocked(self):
        result = self.engine.evaluate({"action": "charge", "amount": 1001})
        assert result.blocked
        assert "1001" in result.reason

    def test_no_amount_field_passes(self):
        result = self.engine.evaluate({"action": "charge"})
        assert result.allowed

    def test_non_numeric_amount_is_blocked(self):
        result = self.engine.evaluate({"action": "charge", "amount": "lots"})
        assert result.blocked


# ---------------------------------------------------------------------------
# RuleEngine – required_fields
# ---------------------------------------------------------------------------


class TestRequiredFields:
    def setup_method(self):
        self.engine = RuleEngine(required_fields=["action", "idempotency_key"])

    def test_all_required_fields_present_passes(self):
        result = self.engine.evaluate({"action": "charge", "idempotency_key": "abc"})
        assert result.allowed

    def test_missing_required_field_is_blocked(self):
        result = self.engine.evaluate({"action": "charge"})
        assert result.blocked
        assert "idempotency_key" in result.reason

    def test_missing_multiple_fields_blocks_on_first(self):
        result = self.engine.evaluate({})
        assert result.blocked
        assert "action" in result.reason


# ---------------------------------------------------------------------------
# RuleEngine – custom_rules
# ---------------------------------------------------------------------------


class TestCustomRules:
    def test_custom_rule_can_block(self):
        def no_test_mode(payload):
            if payload.get("mode") == "test":
                return "Test mode payloads are not allowed in production."
            return None

        engine = RuleEngine(custom_rules=[no_test_mode])
        assert engine.evaluate({"action": "charge", "mode": "live"}).allowed
        result = engine.evaluate({"action": "charge", "mode": "test"})
        assert result.blocked
        assert "test mode" in result.reason.lower()

    def test_custom_rule_returning_empty_string_allows(self):
        engine = RuleEngine(custom_rules=[lambda p: ""])
        assert engine.evaluate({"action": "charge"}).allowed


# ---------------------------------------------------------------------------
# StripeHalt – template
# ---------------------------------------------------------------------------


class TestStripeHalt:
    def setup_method(self):
        self.engine = StripeHalt()

    def test_safe_charge_passes(self):
        result = self.engine.evaluate({"action": "create_charge", "amount": 100})
        assert result.allowed

    def test_delete_customer_is_blocked(self):
        result = self.engine.evaluate({"action": "delete_customer"})
        assert result.blocked
        assert "delete_customer" in result.reason

    def test_delete_payment_method_is_blocked(self):
        result = self.engine.evaluate({"action": "delete_payment_method"})
        assert result.blocked

    def test_delete_subscription_is_blocked(self):
        result = self.engine.evaluate({"action": "delete_subscription"})
        assert result.blocked

    def test_amount_within_default_limit_passes(self):
        result = self.engine.evaluate({"action": "create_refund", "amount": 49_999})
        assert result.allowed

    def test_amount_exceeds_default_limit_is_blocked(self):
        result = self.engine.evaluate({"action": "create_refund", "amount": 50_001})
        assert result.blocked

    def test_missing_action_field_is_blocked(self):
        """StripeHalt requires the 'action' field."""
        result = self.engine.evaluate({"amount": 100})
        assert result.blocked
        assert "action" in result.reason

    def test_custom_max_amount(self):
        engine = StripeHalt(max_amount=100.0)
        assert engine.evaluate({"action": "create_charge", "amount": 50}).allowed
        assert engine.evaluate({"action": "create_charge", "amount": 101}).blocked

    def test_extra_blocked_actions(self):
        engine = StripeHalt(extra_blocked_actions=["create_payout"])
        result = engine.evaluate({"action": "create_payout"})
        assert result.blocked
