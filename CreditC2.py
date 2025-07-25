import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
from fpdf import FPDF

# --- Page Setup ---
st.set_page_config(page_title="Dyce Contract Decision Engine V2 2025", layout="wide")
VERSION = "V2 - 2025"
LOGO_PATH = "DYCE-DARK BG.png"
SIC_CODES_URL = "https://raw.githubusercontent.com/ChrisBeardsmore/Gas-Pricing/main/Sic%20Codes.xlsx"

# --- Styles ---
st.markdown("""
    <style>
        .stApp {
            background-color: white;
            color: rgb(15,42,52);
        }
        label, .stMarkdown, .css-1cpxqw2,
        .stRadio > div, div[data-baseweb="radio"] {
            color: rgb(15,42,52) !important;
        }
        div.stButton > button, div.stDownloadButton > button {
            background-color: rgb(222,0,185) !important;
            color: white !important;
        }
    </style>
""", unsafe_allow_html=True)

st.image(LOGO_PATH, width=200)
st.title(f"⚡ Dyce Contract Decision Engine V2 2025 ({VERSION})")

# --- Load SIC Codes ---
@st.cache_data
def load_sic():
    df = pd.read_excel(SIC_CODES_URL)
    df['SIC_Code'] = df['SIC_Code'].astype(str).str.strip()
    return df

sic_df = load_sic()

# --- Inputs ---
st.header("1️⃣ Business Details")
username = st.text_input("Username")  # NEW FIELD
company_name = st.text_input("Company Name")
creditsafe_score = st.number_input("Creditsafe Score", 0, 100)
recommended_limit = st.number_input("Creditsafe Recommended Limit (£)", 0.0)
years_trading = st.number_input("Years Trading", 0, 100)
smet_compatible = st.selectbox("Is Meter SMET-Compatible?", ["Yes", "No"])
has_ccjs = st.selectbox("Any CCJs or Defaults?", ["Yes", "No"])
payment_terms = st.selectbox(
    "Requested Payment Terms",
    ["7 Days Direct Debit", "14 Days DD", "14 Days BACS", "28 Days BACS"],
    index=0
)
contract_value = st.number_input("Total Contract Value (£)", 0.0)
annual_volume = st.number_input("Estimated Annual Volume (kWh)", 0.0)
contract_term = st.number_input("Contract Term (Years)", 1, 200)
number_of_sites = st.number_input("Number of Sites", 1, 200)

st.header("2️⃣ Pricing Details")
unit_margin = st.number_input("Unit Margin (p/kWh)", 0.0)
uplift_standing = st.number_input("Broker Uplift - Standing Charge (p/day)", 0.0)
uplift_unit = st.number_input("Broker Uplift - Unit Rate (p/kWh)", 0.0)

st.header("3️⃣ SIC Code")
sic_code = st.text_input("Enter SIC Code").strip()
sic_description, sic_risk = "Unknown", "Medium"

if sic_code:
    match = sic_df[sic_df['SIC_Code'] == sic_code]
    if not match.empty:
        sic_description = match.iloc[0]['SIC_Description']
        sic_risk = match.iloc[0]['Typical_Risk_Rating']
        st.markdown(f"**SIC Description:** {sic_description}")
        st.markdown(f"**Risk Rating:** {sic_risk}")
    else:
        sic_risk = st.selectbox("Manual Risk Rating", ["Low", "Medium", "High", "Very High"], index=1)

# --- Approver Logic ---
def get_required_approver(sites, spend, volume):
    if sites <= 20 and spend <= 50000 and volume <= 200000:
        return "Sales Admin"
    if sites <= 50 and spend <= 100000 and volume <= 400000:
        return "TPI/ Direct Sales Manager"
    if sites <= 75 and spend <= 250000 and volume <= 1000000:
        return "Commercial Manager"
    return "Managing Director"

# --- Decision Engine (core logic preserved) ---
def run_decision():
    reasons = []
    decision = "Approved"
    approver = None
    three_month_exposure = contract_value / contract_term / 4

    # Declines
    if creditsafe_score < 30 and smet_compatible == "No":
        decision = "Declined"
        reasons.append("Declined: Credit score below 30 and meter not SMET-compatible.")
    if has_ccjs == "Yes":
        decision = "Declined"
        reasons.append("Declined: CCJs/defaults present.")
    if three_month_exposure > recommended_limit:
        decision = "Declined"
        reasons.append("Declined: 3-month exposure exceeds recommended limit.")

    # Yu Energy message (text-only; does not override decision block here)
    if creditsafe_score < 30 and smet_compatible == "Yes":
        reasons.append("Credit Score below Dyce minimum - price with YU Energy only")

    # Referral checks (only if not Declined)
    if decision != "Declined":
        if creditsafe_score < 60:
            reasons.append("Referral: Low credit score.")
        if sic_risk in ["High", "Very High"]:
            reasons.append("Referral: High sector risk.")
        if payment_terms != "7 Days Direct Debit":
            reasons.append("Referral: Non-standard payment terms.")
        if unit_margin < 0.5:
            reasons.append("Referral: Unit margin below minimum.")
        if uplift_standing > 5.0:
            reasons.append("Referral: Standing uplift too high.")
        if uplift_unit > 1.0:
            reasons.append("Referral: Unit rate uplift too high.")
        if years_trading < 1:
            reasons.append("Referral: Insufficient trading history.")

        approver = get_required_approver(number_of_sites, contract_value, annual_volume)

    # If the final decision is Approved, hide "Referral:" reasons on screen
    if decision == "Approved":
        reasons = [r for r in reasons if not r.startswith("Referral:")]

    return decision, (approver if decision != "Declined" else None), reasons

# --- PDF Export ---
class PDF(FPDF):
    def header(self):
        self.image(LOGO_PATH, x=10, y=8, w=50)
        self.ln(35)
    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.set_text_color(15, 42, 52)
        self.cell(0, 10, f'Report generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', 0, 0, 'C')

def export_pdf(data, decision, approver, reasons):
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(15, 42, 52)
    pdf.cell(0, 10, "Dyce Credit Decision Report", ln=True)

    # Username, Company Name, Date
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Username: {username}", ln=True)
    pdf.cell(0, 10, f"Company Name: {company_name}", ln=True)
    pdf.cell(0, 10, f"Date: {datetime.now().strftime('%d %B %Y')}", ln=True)

    pdf.ln(5)
    for k, v in data.items():
        if "£" in k:
            pdf.cell(0, 10, f"{k}: £{v:,.2f}", ln=True)
        else:
            pdf.cell(0, 10, f"{k}: {v}", ln=True)

    pdf.ln(5)
    pdf.cell(0, 10, f"Decision: {decision}", ln=True)
    if approver:
        pdf.cell(0, 10, f"Approver Required: {approver}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Reasons / Stipulations:", ln=True)
    pdf.set_font("Arial", '', 12)
    for r in reasons:
        pdf.multi_cell(0, 10, f"- {r}")

    buffer = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin1')
    buffer.write(pdf_bytes)
    buffer.seek(0)
    return buffer

# --- Run Decision ---
if st.button("Run Decision Engine"):
    decision, approver, reasons = run_decision()
    st.subheader("Decision Result")
    st.markdown(f"**Final Decision:** {decision}")
    if approver:
        st.markdown(f"**Required Approver:** {approver}")
        if approver == "Managing Director":
            st.markdown("📧 Please email the PDF report to **Tenderapprovals@dyce-energy.co.uk**")

    for r in reasons:
        st.markdown(f"- {r}")

    result_data = {
        "Company Name": company_name,
        "Creditsafe Score": creditsafe_score,
        "Creditsafe Recommended Limit (£)": recommended_limit,
        "Total Contract Value (£)": contract_value,
        "Estimated Annual Volume (kWh)": annual_volume,
        "Number of Sites": number_of_sites,
        "SIC Code": sic_code,
        "SIC Description": sic_description,
        "Risk Rating": sic_risk
    }

    pdf_file = export_pdf(result_data, decision, approver, reasons)
    st.download_button("Download PDF Report", pdf_file, "Credit_Decision_Report.pdf", "application/pdf")
