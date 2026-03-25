import pytest
from halt.core import RuleEngine
from halt.templates import StripeHalt

def test_allow_safe_action():
    engine = RuleEngine(max_amount=100)
    payload = {"action": "refund", "amount": 50}
    decision = engine.evaluate(payload)
    
    assert decision.status == "ALLOW"
    assert decision.payload["amount"] == 50

def test_block_blacklisted_action():
    engine = RuleEngine(blocked_actions=["delete_database"])
    payload = {"action": "delete_database"}
    decision = engine.evaluate(payload)
    
    assert decision.status == "BLOCKED"
    assert "strictly prohibited" in decision.reason

def test_block_exceeding_amount():
    engine = RuleEngine(max_amount=50)
    payload = {"action": "refund", "amount": 5000}
    decision = engine.evaluate(payload)
    
    assert decision.status == "BLOCKED"
    assert "exceeds hard limit" in decision.reason

def test_catch_llm_string_hallucination():
    # LLMs often send numbers as strings. The engine MUST catch and convert this.
    engine = RuleEngine(max_amount=50)
    payload = {"action": "refund", "amount": "5000"} 
    decision = engine.evaluate(payload)
    
    assert decision.status == "BLOCKED"
    assert "exceeds hard limit" in decision.reason

def test_catch_broken_json():
    engine = RuleEngine()
    bad_json = '{"action": "refund", "amount": 50' # Missing closing brace
    decision = engine.evaluate(bad_json)
    
    assert decision.status == "BLOCKED"
    assert "not valid JSON" in decision.reason

def test_stripe_template_blocks_customer_deletion():
    engine = StripeHalt()
    payload = {"action": "delete_customer", "customer_id": "cus_123"}
    decision = engine.evaluate(payload)
    
    assert decision.status == "BLOCKED"
    assert "strictly prohibited" in decision.reason