import pandas as pd

def credit_decision_engine(customer_data):
    """
    customer_data: dict with keys:
      - creditsafe_score
      - years_trading
      - sector_risk (Low, Medium, High, Very High)
      - annual_consumption_mwh
      - contract_value
    returns: decision (Approved / Approved with Stipulations / Refer / Decline) and the total score
    """
    
    # scoring bands
    def score_creditsafe(cs):
        if cs >= 80:
            return 100
        elif cs >= 60:
            return 75
        elif cs >= 40:
            return 50
        else:
            return 25

    def score_years_trading(yt):
        if yt > 5:
            return 100
        elif yt >= 2:
            return 75
        elif yt >= 1:
            return 50
        else:
            return 25

    def score_sector(sr):
        mapping = {'Low': 100, 'Medium': 75, 'High': 50, 'Very High': 25}
        return mapping.get(sr, 50)

    def score_consumption(mwh):
        if mwh < 100:
            return 100
        elif mwh <= 250:
            return 75
        elif mwh <= 500:
            return 50
        else:
            return 25

    def score_contract_value(val):
        if val < 25000:
            return 100
        elif val <= 50000:
            return 75
        elif val <= 100000:
            return 50
        else:
            return 25

    # apply scoring
    s1 = score_creditsafe(customer_data['creditsafe_score']) * 0.4
    s2 = score_years_trading(customer_data['years_trading']) * 0.15
    s3 = score_sector(customer_data['sector_risk']) * 0.15
    s4 = score_consumption(customer_data['annual_consumption_mwh']) * 0.15
    s5 = score_contract_value(customer_data['contract_value']) * 0.15

    total_score = s1 + s2 + s3 + s4 + s5

    if total_score >= 80:
        decision = "Approved"
    elif total_score >= 60:
        decision = "Approved with Stipulations"
    elif total_score >= 40:
        decision = "Refer / Manual Review"
    else:
        decision = "Decline"

    return {
        "decision": decision,
        "total_score": total_score,
        "criteria_scores": {
            "creditsafe": s1,
            "years_trading": s2,
            "sector_risk": s3,
            "annual_consumption": s4,
            "contract_value": s5
        }
    }

# Example usage
test_customer = {
    "creditsafe_score": 72,
    "years_trading": 3,
    "sector_risk": "Medium",
    "annual_consumption_mwh": 200,
    "contract_value": 30000
}

result = credit_decision_engine(test_customer)
print(result)
