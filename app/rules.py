def apply_rules(amount: float, location: str = None):
    """
    Returns (decision, rule_name, fraud_risk)
    """

    # Default
    decision = "ACCEPTED"
    fraud = 0
    rule_name = "NO_RULE_TRIGGERED"

    # Rule 1 – Very large amount
    if amount > 5000:
        decision = "REVIEW"
        fraud += 40
        rule_name = "HIGH_AMOUNT"

    # Rule 2 – suspicious location
    if location and location.lower() in ["nigeria", "russia", "unknown"]:
        decision = "REJECTED"
        fraud += 60
        rule_name = "SUSPICIOUS_LOCATION"

    return decision, rule_name, fraud
