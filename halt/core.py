import json
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union

@dataclass
class Decision:
    status: str  # "ALLOW" or "BLOCKED"
    reason: str
    payload: Optional[Dict[str, Any]] = None

class RuleEngine:
    def __init__(
        self, 
        max_amount: Optional[float] = None, 
        blocked_actions: Optional[List[str]] = None,
        require_human_approval: Optional[List[str]] = None
    ):
        self.max_amount = max_amount
        self.blocked_actions = set(blocked_actions or [])
        self.require_human_approval = set(require_human_approval or [])

    def evaluate(self, raw_input: Union[str, Dict[str, Any]]) -> Decision:
        # 1. Safely parse payload (Agents often return raw strings)
        if isinstance(raw_input, str):
            try:
                payload = json.loads(raw_input)
            except json.JSONDecodeError:
                return Decision("BLOCKED", "Fatal: LLM output is not valid JSON.")
        else:
            payload = raw_input

        if not isinstance(payload, dict):
            return Decision("BLOCKED", "Fatal: Payload must be a JSON object.")

        # 2. Extract core intent
        action = payload.get("action")
        if not action:
            return Decision("BLOCKED", "Missing required field: 'action'.")

        # 3. Enforce Blacklist
        if action in self.blocked_actions:
            return Decision("BLOCKED", f"Action '{action}' is strictly prohibited.")

        if action in self.require_human_approval:
            return Decision("BLOCKED", f"Action '{action}' requires human-in-the-loop approval.")

        # 4. Enforce Financial Limits
        amount = payload.get("amount")
        if amount is not None:
            # Agents hallucinate strings for numbers. We catch that.
            if not isinstance(amount, (int, float)):
                try:
                    amount = float(amount)
                except ValueError:
                    return Decision("BLOCKED", "Amount must be a numeric value.")
            
            if self.max_amount is not None and amount > self.max_amount:
                return Decision("BLOCKED", f"Amount {amount} exceeds hard limit of {self.max_amount}.")

        return Decision("ALLOW", "Passed all deterministic checks.", payload)