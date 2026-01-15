def explain_reason(amount, rule_name, fraud_score):
    reasons = []

    if amount > 5000:
        reasons.append("High amount compared to typical spending")

    if rule_name == "SUSPICIOUS_LOCATION":
        reasons.append("Transaction from suspicious location")

    if fraud_score > 70:
        reasons.append("ML Model flagged as anomaly")

    if not reasons:
        reasons.append("Normal behavior")

    return reasons
