# `halt`

**Deterministic safety rails for probabilistic AI.**

[![PyPI version](https://img.shields.io/badge/pypi-v0.1.0-blue)](https://pypi.org/project/halt-ai/) [![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT) [![Latency](https://img.shields.io/badge/latency-0.01s-success)](#)

### The Problem
You are giving an LLM the keys to your Stripe API, your SendGrid account, or your production database using function calling. 

Eventually, it will hallucinate. It will confidently refund $5,000 instead of $50, or `DROP TABLE` instead of `SELECT`. Writing custom `if/else` spaghetti code to catch every possible edge case is unscalable and guarantees you will miss a catastrophic failure.

### The Solution
`halt` is a zero-dependency, local rule engine. It sits directly between your LLM's output and your execution layer. It intercepts the raw JSON action, validates it against strict, human-defined constraints, and acts as a mathematical firewall. 

Zero AI. Zero machine learning. Pure deterministic logic. **It catches the bullet before it hits your API.**

---

### Installation

```bash
pip install halt-ai
```

### The 3-Line Integration

Stop writing custom validators. Define your policy once, wrap your LLM output, and ship your agent safely.

```python
from halt import RuleEngine
from halt.templates import StripeHalt

# 1. Define your strict deterministic limits (Do this once)
payment_policy = RuleEngine(
    max_amount=50.00,
    blocked_actions=["cancel_subscription_bulk", "delete_customer"],
    require_human_approval=["issue_credit"]
)

# 2. Intercept the LLM's raw output (The Hallucination)
llm_output = {
    "action": "refund", 
    "amount": 5000.00, 
    "customer_id": "cus_123"
} 

# 3. Halt the execution before it hits reality
decision = payment_policy.evaluate(llm_output)

if decision.status == "BLOCKED":
    print(f"Execution Halted: {decision.reason}")
    # Trigger LLM self-correction by feeding the reason back to the prompt
```

### Out-of-the-Box Threat Templates

You do not have to map every API vulnerability yourself. `halt` ships with battle-tested schemas for the most dangerous integrations.

* **`StripeHalt`:** Automatically blocks high-value refunds, customer deletion, and bulk subscription cancellations.
* **`SQLHalt`:** Intercepts payload strings and strictly rejects `DROP`, `DELETE WITHOUT WHERE`, and unauthorized table mutations.
* **`MailHalt`:** Prevents rapid-fire email loops, restricts sending domains, and flags restricted keywords in draft bodies.
* **`ShellHalt`:** Safely sandboxes LLM terminal execution, blocking `rm -rf`, outbound network calls, and unauthorized directory traversal.

### Why use `halt`?

1. **Zero Dependencies:** It will not bloat your project.
2. **Microsecond Latency:** Evaluates payloads in `~0.01s`. It will not slow down your agent's execution loop.
3. **Type-Coercion Safe:** AI agents often hallucinate data types (e.g., sending an amount as the string `"50"` instead of the integer `50`). `halt` automatically catches and sanitizes these anomalies before they crash your app.

### License
MIT License. Free for solo developers, indie hackers, and open-source projects.
