import os
import base64
from io import BytesIO
import streamlit as st
from pypdf import PdfReader
from PIL import Image
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from agent import auditor_app, sanitize_and_fingerprint

st.set_page_config(page_title="LEXGUARDIAN | Smart Document & ID Checker", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .block-container { padding-top: 1.4rem; max-width: 1300px; }
    .lex-hero {
        background: linear-gradient(135deg, #090e1a 0%, #172033 100%);
        border: 1px solid #334155; border-radius: 16px; padding: 1.4rem 1.8rem;
        display: flex; align-items: center; justify-content: space-between; margin-bottom: 1.2rem;
    }
    .lex-left { display: flex; align-items: center; gap: 1rem; }
    .lex-name {
        font-size: 2rem; font-weight: 800; letter-spacing: 1px;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0;
    }
    .lex-tag { color: #cbd5e1; font-size: 0.95rem; margin-top: 0.2rem; }
    .lex-badge {
        background: rgba(16, 185, 129, 0.14); color: #34d399;
        border: 1px solid #10b981; padding: 0.3rem 0.85rem;
        border-radius: 999px; font-size: 0.78rem; font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; background: #0f172a; padding: 6px; border-radius: 12px; }
    .stTabs [data-baseweb="tab"] { height: 42px; border-radius: 8px; padding: 0 18px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background: linear-gradient(90deg, #2563eb, #4f46e5) !important; color: white !important; }
    div.stButton > button { border-radius: 10px; font-weight: 600; height: 45px; }
    div.stButton > button[kind="primary"] { background: linear-gradient(90deg, #2563eb, #6366f1); border: none; color: white; }
</style>
<div class="lex-hero">
    <div class="lex-left">
        <svg width="46" height="46" viewBox="0 0 64 64" fill="none">
            <path d="M32 4L8 14V30C8 46.5 18.2 61.2 32 64C45.8 61.2 56 46.5 56 30V14L32 4Z" fill="#38bdf8" fill-opacity="0.18" stroke="#38bdf8" stroke-width="3"/>
            <path d="M32 18V46M20 26H44M20 26L15 36H25L20 26ZM44 26L39 36H49L44 26Z" stroke="#f8fafc" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div>
            <div class="lex-name">LEXGUARDIAN</div>
            <div class="lex-tag">Spot Hidden Traps in Contracts, Job Offers, Rent Agreements & IDs Before You Sign</div>
        </div>
    </div>
    <div class="lex-badge">🔒 Private • Instant Trap Detector • Aadhaar/PAN Safe</div>
</div>
""", unsafe_allow_html=True)

PRESETS = {
    "💼 Job Offer / Internship Letter": {
        "rules": "1. Notice Period: Must NOT exceed 60 days and must apply equally to both sides.\n2. Training Bond / Penalty: Huge monetary bonds for leaving early are unfair.\n3. Non-Compete: Blocking a candidate from working in the same industry after leaving is unfair.\n4. Side Projects: Personal work done outside office hours belongs to the employee.",
        "sample": "OFFER LETTER\n1. NOTICE PERIOD: Employee must serve a 90-day notice period to resign, whereas Company may terminate immediately without notice.\n2. BOND: Employee must pay Rs. 2,00,000 if leaving within 2 years.\n3. NON-COMPETE: Employee cannot join any tech company in India for 2 years after leaving."
    },
    "🏠 House Rent / PG Agreement": {
        "rules": "1. Security Deposit: Deposit must be refunded within 15-30 days of vacating without arbitrary deductions.\n2. Eviction Notice: Landlord must give at least 30 days notice before asking tenant to vacate.\n3. Rent Hike: Annual rent increase should not exceed 5% to 10%.",
        "sample": "RESIDENTIAL RENTAL AGREEMENT\n1. DEPOSIT: Landlord may withhold the entire Rs. 50,000 security deposit for normal wear and tear or painting.\n2. VACATING: Landlord can ask Tenant to vacate within 48 hours without reason, while Tenant must give 3 months notice.\n3. RENT INCREASE: Landlord may increase rent by 25% every 6 months."
    },
    "🪪 Aadhaar / ID Card Safety Check": {
        "rules": "1. Masked Aadhaar Rule: Full 12-digit Aadhaar numbers MUST NOT be shared unmasked; only the last 4 digits should be visible.\n2. Data Sharing: ID copies must not be shared with third-party advertisers or stored overseas.",
        "sample": "KYC VERIFICATION FORM\nName: Rahul Sharma | Aadhaar: 4589 2314 9876 | PAN: ABCDE1234F\nConsent: Company may store unmasked Aadhaar copy permanently on foreign servers and share with marketing partners."
    },
    "💳 Loan / EMI / Subscription Terms": {
        "rules": "1. Hidden Fees: Foreclosure or early repayment penalties must be transparent and reasonable.\n2. Auto-Renewal: Subscriptions must NOT auto-renew without clear prior reminder and easy 1-click cancellation.",
        "sample": "LOAN & SUBSCRIPTION TERMS\n1. PREPAYMENT: Borrower will be charged a 12% penalty on total loan amount for early closure.\n2. AUTO-DEBIT: Membership auto-renews annually with zero refund and requires sending a physical letter 90 days prior to cancel."
    },
    "🏢 Business Vendor & DPDP Compliance": {
        "rules": "1. Data Localization (DPDP Act): Customer data MUST stay in India.\n2. Liability Cap: Vendor liability must NOT be capped below 12 months of fees.\n3. Governing Law: Laws of India with jurisdiction in Bengaluru or New Delhi.",
        "sample": "MASTER SERVICES AGREEMENT\n1. DATA: Vendor stores all Indian user records on US servers and shares telemetry with ad affiliates.\n2. LIABILITY: Vendor total liability is capped at $500 USD even for data breaches."
    }
}
