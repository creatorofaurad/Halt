"""Core rule engine for validating AI agent payloads."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class EvaluationResult:
    """Immutable result returned by :meth:`RuleEngine.evaluate`."""

    status: str  # "ALLOW" or "BLOCKED"
    reason: str

    @property
    def allowed(self) -> bool:
        return self.status == "ALLOW"

    @property
    def blocked(self) -> bool:
        return self.status == "BLOCKED"


class RuleEngine:
    """Deterministic rule engine that validates a JSON payload against constraints.

    Parameters
    ----------
    max_amount:
        If set, any payload whose ``amount`` field exceeds this value is blocked.
    blocked_actions:
        A collection of action names that must never be executed.
    required_fields:
        Field names that *must* be present in every payload.
    custom_rules:
        An optional list of callables ``(payload: dict) -> str | None``.
        Each callable should return a non-empty reason string when the payload
        should be blocked, or ``None`` / an empty string to allow it.
    """

    def __init__(
        self,
        *,
        max_amount: float | None = None,
        blocked_actions: list[str] | None = None,
        required_fields: list[str] | None = None,
        custom_rules: list[Any] | None = None,
    ) -> None:
        self.max_amount = max_amount
        self.blocked_actions: frozenset[str] = frozenset(blocked_actions or [])
        self.required_fields: list[str] = list(required_fields or [])
        self.custom_rules: list[Any] = list(custom_rules or [])

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(self, payload: dict) -> EvaluationResult:
        """Evaluate *payload* against all configured constraints.

        Returns an :class:`EvaluationResult` with ``status="ALLOW"`` when the
        payload passes every rule, or ``status="BLOCKED"`` with a human-readable
        ``reason`` on the first failing rule.
        """
        if not isinstance(payload, dict):
            return self._block("Payload must be a JSON object (dict).")

        # 1. Required fields check
        for field in self.required_fields:
            if field not in payload:
                return self._block(f"Missing required field: '{field}'.")

        # 2. Blocked actions check
        action = payload.get("action")
        if action is not None and action in self.blocked_actions:
            return self._block(f"Action '{action}' is explicitly blocked.")

        # 3. Amount ceiling check
        amount = payload.get("amount")
        if amount is not None and self.max_amount is not None:
            try:
                if float(amount) > self.max_amount:
                    return self._block(
                        f"Amount {amount} exceeds the maximum allowed value of"
                        f" {self.max_amount}."
                    )
            except (TypeError, ValueError):
                return self._block(
                    f"Amount field contains a non-numeric value: {amount!r}."
                )

        # 4. Custom rules
        for rule in self.custom_rules:
            reason = rule(payload)
            if reason:
                return self._block(reason)

        return EvaluationResult(status="ALLOW", reason="All rules passed.")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _block(reason: str) -> EvaluationResult:
        return EvaluationResult(status="BLOCKED", reason=reason)
