import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

# --- UI Setup ---
st.set_page_config(page_title="Dyce Contract Decision Engine V2", layout="wide")
st.markdown("""
    <style>
        .stApp {
            background-color: white;
            color: rgb(15,42,52);
        }
        label, .css-1cpxqw2, .css-1y4p8pa {
            color: rgb(15,42,52) !important;
        }
        div.stButton > button, div.stDownloadButton > button {
            background-color: rgb(222,0,185) !important;
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

st.image("DYCE-DARK BG.png", width=200)
st.title("⚡ Dyce Contract Decision Engine V2")

# --- Load SIC Codes ---
SIC_CODES_URL = "https://raw.githubusercontent.com/ChrisBeardsmore/Gas-Pricing/main/Sic%20Codes.xlsx"
@st.cache_data
def load_sic_codes():
    df = pd.read_excel(SIC_CODES_URL)
    df['SIC_Code'] = df['SIC_Code'].astype(str).str.strip()
    return df
sic_df = load_sic_codes()

# --- Load Approval Matrix ---
APPROVAL_MATRIX_URL = "https://raw.githubusercontent.com/ChrisBeardsmore/Gas-Pricing/main/Credit_Decision_Config_Template.xlsx"
@st.cache_data
def load_approval_matrix():
    df = pd.read_excel(APPROVAL_MATRIX_URL)
    return df
matrix_df = load_approval_matrix()

# --- Sidebar Config ---
st.sidebar.header("🔧 Configuration")
approve_threshold = st.sidebar.number_input("Credit Score Threshold for Approval", 0, 100, 80)
refer_threshold = st.sidebar.number_input("Credit Score Threshold for Referral", 0, 100, 60)
min_unit_margin = st.sidebar.number_input("Minimum Unit Margin (p/kWh)", 0.0, 10.0, 0.5)
max_days_to_pay = st.sidebar.number_input("Max Payment Terms (Days)", 1, 90, 14)

# --- Input Section ---
st.header("1️⃣ Customer Details")
business_type = st.selectbox("Business Type", ["Sole Trader", "Partnership", "Limited Company"])
years_trading = st.number_input("Years Trading", 0)
credit_score = st.number_input("Creditsafe Score", 0, 100)
smet_compatible = st.selectbox("Is Meter SMET Compatible?", ["Yes", "No"])
payment_terms = st.selectbox("Requested Payment Terms", ["14 Days DD", "14 Days BACS", "30 Days BACS", ">30 Days BACS"])

st.header("2️⃣ Contract Details")
number_of_sites = st.number_input("Number of Sites", 1)
annual_volume = st.number_input("Annual Consumption (kWh)", 0.0)
contract_value = st.number_input("Contract Value (\u00a3)", 0.0)
contract_term = st.number_input("Contract Term (Years)", 1, 10)
unit_margin = st.number_input("Proposed Unit Margin (p/kWh)", 0.0)

st.header("3️⃣ SIC Code")
sic_code = st.text_input("SIC Code (5-digit)").strip()
sic_description = "Unknown"
sic_risk = "Medium"
if sic_code:
    match = sic_df[sic_df['SIC_Code'] == sic_code]
    if not match.empty:
        sic_description = match.iloc[0]['SIC_Description']
        sic_risk = match.iloc[0]['Typical_Risk_Rating']
        st.markdown(f"**SIC Description:** {sic_description}")
        st.markdown(f"**Risk Rating:** {sic_risk}")
    else:
        sic_risk = st.selectbox("Manual SIC Risk", ["Low", "Medium", "High", "Very High"], index=1)

# --- Decision Logic ---
def run_decision():
    reasons = []
    recommendation = "Approved"

    # Hard declines
    if credit_score < refer_threshold:
        if credit_score < 30 and smet_compatible == "Yes":
            recommendation = "Approved with Yu Energy Only"
            reasons.append("Credit Score <30: Only Yu Energy permitted due to SMET compatibility")
        else:
            recommendation = "Declined"
            reasons.append("Credit Score below minimum threshold")
    
    # Referrals
    elif refer_threshold <= credit_score < approve_threshold:
        recommendation = "Refer"
        reasons.append("Credit Score requires referral")

    if business_type != "Limited Company" and years_trading < 1:
        recommendation = "Refer"
        reasons.append("Insufficient trading history for Sole Trader/Partnership")
    elif business_type == "Limited Company" and years_trading < 2:
        recommendation = "Refer"
        reasons.append("Insufficient trading history for Limited Company")

    if payment_terms != "14 Days DD" and payment_terms != "14 Days BACS":
        recommendation = "Refer"
        reasons.append("Payment terms exceed acceptable")

    if sic_risk in ["High", "Very High"]:
        recommendation = "Refer"
        reasons.append("SIC Risk too high")

    if unit_margin < min_unit_margin:
        recommendation = "Refer"
        reasons.append("Margin below minimum allowed")

    # Exposure test
    exposure_estimate = contract_value / contract_term / 4  # Approx. 3 months
    exposure_passed = exposure_estimate <= contract_value

    # Approval matrix
    approver = "Managing Director"
    for _, row in matrix_df.iterrows():
        if (number_of_sites <= row['Max_Sites'] and
            contract_value <= row['Max_Spend'] and
            annual_volume <= row['Max_Annual_kWh']):
            approver = row['Approver']
            break

    if recommendation == "Approved with Yu Energy Only":
        approver = "Yu Energy Only"
    elif recommendation == "Declined":
        approver = None
    elif approver == "Managing Director":
        reasons.append("Approval by Managing Director required – please email PDF report to md@dyceenergy.com")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return recommendation, approver, reasons, exposure_estimate, exposure_passed, timestamp

# --- PDF Report ---
class PDF(FPDF):
    def header(self):
        self.image("DYCE-DARK BG.png", x=10, y=8, w=50)
        self.ln(30)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(100)
        self.cell(0, 10, f"Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 0, 'C')

def export_to_pdf(inputs, result):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(15, 42, 52)
    pdf.cell(0, 10, "Dyce Credit Decision Report", ln=True, align='C')
    pdf.ln(10)

    pdf.set_font("Arial", '', 12)
    for k, v in inputs.items():
        pdf.multi_cell(0, 8, f"{k}: {v}")

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, f"Decision: {result[0]}", ln=True)
    if result[1]:
        pdf.cell(0, 10, f"Approver: {result[1]}", ln=True)
    pdf.cell(0, 10, f"Exposure Estimate: £{round(result[3],2)}", ln=True)
    pdf.cell(0, 10, f"Exposure OK: {'Yes' if result[4] else 'No'}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, "Reasons:", ln=True)
    for reason in result[2]:
        pdf.multi_cell(0, 8, f"- {reason}")

    buffer = BytesIO()
    pdf.output(buffer)
    buffer.seek(0)
    return buffer

# --- Run Decision ---
if st.button("Run Decision Engine"):
    inputs = {
        "Business Type": business_type,
        "Years Trading": years_trading,
        "Credit Score": credit_score,
        "Meter SMET Compatible": smet_compatible,
        "Payment Terms": payment_terms,
        "Sites": number_of_sites,
        "Annual Volume (kWh)": annual_volume,
        "Contract Value": contract_value,
        "Contract Term": contract_term,
        "Unit Margin": unit_margin,
        "SIC Code": sic_code,
        "SIC Description": sic_description,
        "SIC Risk": sic_risk
    }

    result = run_decision()

    st.subheader("Decision Result")
    st.write(f"**Decision:** {result[0]}")
    if result[1]:
        st.write(f"**Approver:** {result[1]}")
    st.write(f"**Exposure Estimate:** £{round(result[3],2)}")
    st.write(f"**Exposure Acceptable:** {'Yes' if result[4] else 'No'}")

    st.markdown("**Reasons:**")
    for r in result[2]:
        st.markdown(f"- {r}")

    pdf_file = export_to_pdf(inputs, result)
    st.download_button("Download PDF Report", pdf_file, file_name="Dyce_Credit_Report.pdf", mime="application/pdf")
