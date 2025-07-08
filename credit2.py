import streamlit as st

st.set_page_config(page_title="Energy Customer Credit Decision Engine", layout="centered")

st.title("⚡ Energy Customer Credit Decision Engine")

st.markdown("""
This tool will help you assess a customer's credit position using your scoring policy. 
Please enter the details below and click **Run Credit Decision**.
""")

# Inputs
creditsafe_score = st.number_input("Creditsafe Score (0-100)", min_value=0, max_value=100, value=75)
years_trading = st.number_input("Years Trading", min_value=0, max_value=100, value=3)
sector_risk = st.selectbox("Sector Risk", ["Low", "Medium", "High", "Very High"], index=1)
annual_consumption = st.number_input("Annual Consumption (MWh)", min_value=0.0, step=1.0, value=200.0)
contract_value = st.number_input("Contract Value (£)", min_value=0.0, step=1000.0, value=30000.0)

# Credit Decision Engine Logic
def credit_decision_engine(customer_data):
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
        mapping = {"Low": 100, "Medium": 75, "High": 50, "Very High": 25}
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
        decision = "✅ Approved"
    elif total_score >= 60:
        decision = "⚠️ Approved with Stipulations"
    elif total_score >= 40:
        decision = "🔍 Refer / Manual Review"
    else:
        decision = "❌ Decline"

    return {
        "decision": decision,
        "total_score": round(total_score, 1),
        "criteria_scores": {
            "Creditsafe": round(s1, 1),
            "Years Trading": round(s2, 1),
            "Sector Risk": round(s3, 1),
            "Annual Consumption": round(s4, 1),
            "Contract Value": round(s5, 1)
        }
    }

# Run button
if st.button("Run Credit Decision"):
    with st.spinner("Calculating..."):
        result = credit_decision_engine({
            "creditsafe_score": creditsafe_score,
            "years_trading": years_trading,
            "sector_risk": sector_risk,
            "annual_consumption_mwh": annual_consumption,
            "contract_value": contract_value
        })
        st.success(f"**Decision: {result['decision']}**")
        st.metric("Total Score", result["total_score"])
        st.subheader("Breakdown of Scores")
        st.json(result["criteria_scores"])
