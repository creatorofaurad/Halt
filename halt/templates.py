"""Pre-configured rule-engine templates for common third-party APIs."""

from __future__ import annotations

from .core import RuleEngine

# ---------------------------------------------------------------------------
# Stripe
# ---------------------------------------------------------------------------

#: Actions that must never be executed against the Stripe API.
_STRIPE_BLOCKED_ACTIONS: list[str] = [
    "delete_customer",
    "delete_payment_method",
    "delete_product",
    "delete_price",
    "delete_subscription",
]

#: Default maximum refund amount in the smallest currency unit (e.g., cents).
#: Equivalent to $500.00 USD.
_STRIPE_DEFAULT_MAX_REFUND: float = 50_000.0


class StripeHalt(RuleEngine):
    """A :class:`~halt.core.RuleEngine` pre-configured with strict Stripe rules.

    Out-of-the-box protections
    --------------------------
    * Blocks all destructive customer/subscription/product actions.
    * Caps refund and charge amounts at *max_amount* (default: 50 000 cents).
    * Requires an ``action`` field on every payload.

    Parameters
    ----------
    max_amount:
        Override the default maximum amount (in the smallest currency unit).
        Defaults to :data:`_STRIPE_DEFAULT_MAX_REFUND` (50 000 cents / $500).
    extra_blocked_actions:
        Additional action names to block on top of the built-in list.
    custom_rules:
        Extra callable rules forwarded directly to :class:`~halt.core.RuleEngine`.
    """

    def __init__(
        self,
        *,
        max_amount: float = _STRIPE_DEFAULT_MAX_REFUND,
        extra_blocked_actions: list[str] | None = None,
        custom_rules: list | None = None,
    ) -> None:
        blocked = list(_STRIPE_BLOCKED_ACTIONS) + list(extra_blocked_actions or [])
        super().__init__(
            max_amount=max_amount,
            blocked_actions=blocked,
            required_fields=["action"],
            custom_rules=custom_rules,
        )
