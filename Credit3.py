import streamlit as st

st.set_page_config(page_title="Energy Customer Credit Decision Engine", layout="centered")

st.title("⚡ Energy Customer Credit Decision Engine")

st.markdown("""
This tool helps assess a customer's credit profile using a scoring framework.
""")

# --- Admin Section ---
admin_password = "admin123"  # change this to whatever you like
show_settings = False

with st.sidebar:
    st.header("🔒 Admin Controls")
    entered_pw = st.text_input("Enter Admin Password", type="password")
    if entered_pw == admin_password:
        st.success("Admin access granted")
        show_settings = True
    else:
        st.warning("Enter password to adjust criteria")

# --- Default weights and thresholds ---
# Fallback defaults
default_weights = {
    "creditsafe": 0.4,
    "years_trading": 0.15,
    "sector_risk": 0.15,
    "annual_consumption": 0.15,
    "contract_value": 0.15
}

default_thresholds = {
    "approve": 80,
    "stipulations": 60,
    "refer": 40
}

# If admin, allow them to change settings
if show_settings:
    st.sidebar.subheader("Adjust Scoring Weights")
    weight_creditsafe = st.sidebar.slider("Creditsafe Weight", 0.0, 1.0, default_weights['creditsafe'], step=0.05)
    weight_years_trading = st.sidebar.slider("Years Trading Weight", 0.0, 1.0, default_weights['years_trading'], step=0.05)
    weight_sector_risk = st.sidebar.slider("Sector Risk Weight", 0.0, 1.0, default_weights['sector_risk'], step=0.05)
    weight_annual_consumption = st.sidebar.slider("Annual Consumption Weight", 0.0, 1.0, default_weights['annual_consumption'], step=0.05)
    weight_contract_value = st.sidebar.slider("Contract Value Weight", 0.0, 1.0, default_weights['contract_value'], step=0.05)
    
    st.sidebar.subheader("Adjust Thresholds")
    approve_threshold = st.sidebar.slider("Approval Threshold", 0, 100, default_thresholds['approve'])
    stipulations_threshold = st.sidebar.slider("Stipulations Threshold", 0, 100, default_thresholds['stipulations'])
    refer_threshold = st.sidebar.slider("Refer Threshold", 0, 100, default_thresholds['refer'])
else:
    # fallback to defaults
    weight_creditsafe = default_weights['creditsafe']
    weight_years_trading = default_weights['years_trading']
    weight_sector_risk = default_weights['sector_risk']
    weight_annual_consumption = default_weights['annual_consumption']
    weight_contract_value = default_weights['contract_value']
    approve_threshold = default_thresholds['approve']
    stipulations_threshold = default_thresholds['stipulations']
    refer_threshold = default_thresholds['refer']

# --- Input Section ---
st.header("Customer Details")

creditsafe_score = st.number_input("Creditsafe Score (0-100)", min_value=0, max_value=100, value=75)
years_trading = st.number_input("Years Trading", min_value=0, max_value=100, value=3)
sector_risk = st.selectbox("Sector Risk", ["Low", "Medium", "High", "Very High"], index=1)
annual_consumption = st.number_input("Annual Consumption (MWh)", min_value=0.0, step=1.0, value=200.0)
contract_value = st.number_input("Contract Value (£)", min_value=0.0, step=1000.0, value=30000.0)

# --- Credit Decision Engine ---
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
    s1 = score_creditsafe(customer_data['creditsafe_score']) * weight_creditsafe
    s2 = score_years_trading(customer_data['years_trading']) * weight_years_trading
    s3 = score_sector(customer_data['sector_risk']) * weight_sector_risk
    s4 = score_consumption(customer_data['annual_consumption_mwh']) * weight_annual_consumption
    s5 = score_contract_value(customer_data['contract_value']) * weight_contract_value

    total_score = s1 + s2 + s3 + s4 + s5

    if total_score >= approve_threshold:
        decision = "✅ Approved"
    elif total_score >= stipulations_threshold:
        decision = "⚠️ Approved with Stipulations"
    elif total_score >= refer_threshold:
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

# --- Run Button ---
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
