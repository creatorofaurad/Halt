from .core import RuleEngine

class StripeHalt(RuleEngine):
    """
    Pre-configured threat model for Stripe API interactions.
    """
    def __init__(self, max_refund_usd: float = 50.00):
        super().__init__(
            max_amount=max_refund_usd,
            blocked_actions=[
                "delete_customer", 
                "cancel_subscription_bulk",
                "delete_invoice"
            ],
            require_human_approval=[
                "issue_credit",
                "create_payout"
            ]
        )