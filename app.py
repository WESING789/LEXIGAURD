import os
import json
import base64
from io import BytesIO
from datetime import datetime
import streamlit as st
from pypdf import PdfReader
from PIL import Image
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from agent import auditor_app, sanitize_and_fingerprint

st.set_page_config(page_title="LEXGUARDIAN | Legal & ID Shield", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")

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
    .lex-tag { color: #94a3b8; font-size: 0.9rem; margin-top: 0.2rem; }
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
            <div class="lex-tag">Zero-Trust Contract, KYC & DPDP Compliance Intelligence</div>
        </div>
    </div>
    <div class="lex-badge">🔒 Air-Gapped • Aadhaar/PAN Shield • SHA-256</div>
</div>
""", unsafe_allow_html=True)

PRESETS = {
    "🪪 Aadhaar / ID Card DPDP Privacy Audit": """1. Masked Aadhaar Rule (UIDAI / DPDP): Full 12-digit Aadhaar numbers MUST NOT be shared unmasked; only the last 4 digits should be visible.\n2. Purpose Limitation: ID documents must state why data is collected and must not include unnecessary family/biometric details.\n3. Identity Consistency: Name, DOB, and ID format (12-digit Aadhaar or 10-char PAN) must be valid and properly formatted.""",
    "🏢 Vendor & DPDP Contract Compliance": """1. Data Localization (DPDP Act): Personal data MUST be stored strictly in India. No third-party sharing without written consent.\n2. Liability Cap: Vendor liability must NOT be capped below 12 months of fees paid.\n3. Exit Rights: No auto-renewal without 30 days notice; client must have 30-day termination for convenience.""",
    "💼 Job Offer Letter Check": """1. Notice Period: Notice period must NOT exceed 60 days.\n2. Non-Compete: Post-employment non-compete clauses exceeding 6 months are unacceptable.\n3. IP Rights: Personal side-projects built outside work hours must remain employee property."""
}

SAMPLE_DOC = """SAMPLE KYC / ID SUBMISSION RECORD
Applicant Name: Aarav Sharma | DOB: 14-08-2002
Unmasked Aadhaar Number: 4589 2314 9876
PAN Card Number: ABCDE1234F | Phone: +91 9876543210
Clause: Applicant consents to vendor storing full unmasked Aadhaar copy permanently on overseas servers and sharing with marketing partners."""

def extract_text_from_image(img_file) -> str:
    if not os.getenv("GOOGLE_API_KEY"):
        return "IMAGE OCR REQUIRES CLOUD GEMINI KEY: Please upload a PDF/text on local mode or use the live Streamlit website for image/ID scanning."
    img = Image.open(img_file)
    buf = BytesIO()
    img.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    vision_llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    msg = HumanMessage(content=[
        {"type": "text", "text": "Transcribe all visible text, numbers, ID fields, and clauses from this document/ID image accurately."},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}
    ])
    return vision_llm.invoke([msg]).content

if "result" not in st.session_state:
    st.session_state.result = None
if "meta" not in st.session_state:
    st.session_state.meta = None

t_work, t_chart, t_sec, t_info = st.tabs(["⚖️ Audit Workspace", "📊 Risk Analytics", "🔐 Security Certificate", "ℹ️ Info"])

with t_work:
    c1, c2 = st.columns([1, 1.15], gap="large")
    with c1:
        preset_choice = st.selectbox("⚡ Quick Audit Mode:", list(PRESETS.keys()))
        playbook = st.text_area("Compliance Rules:", value=PRESETS[preset_choice], height=145)

        uploaded = st.file_uploader("📄 Upload Document or ID Image (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"])
        if uploaded:
            if uploaded.type == "application/pdf":
                reader = PdfReader(uploaded)
                raw_text = "\n".join([p.extract_text() or "" for p in reader.pages[:20]])
                st.caption(f"✅ Loaded PDF: {uploaded.name}")
            else:
                st.image(uploaded, caption="Uploaded ID / Document Preview", width=260)
                with st.spinner("Scanning ID/document text..."):
                    raw_text = extract_text_from_image(uploaded)
                st.caption("✅ Extracted text from image")
        else:
            raw_text = st.text_area("Or test sample KYC / ID text:", value=SAMPLE_DOC, height=175)

        b1, b2, b3 = st.columns([1.4, 1, 1], gap="small")
        with b1:
            run_btn = st.button("⚡ Run Audit", type="primary", use_container_width=True)
        with b2:
            pii_on = st.toggle("Auto-Mask IDs", value=False, help="Turn ON to redact Aadhaar/PAN before AI analysis; turn OFF to audit if an ID is dangerously exposed.")
        with b3:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.result = None
                st.session_state.meta = None
                st.rerun()

        if run_btn and raw_text.strip():
            with st.spinner("Auditing document & verifying citations..."):
                clean_txt, meta = sanitize_and_fingerprint(raw_text, mask_pii=pii_on)
                out = auditor_app.invoke({
                    "contract_text": clean_txt, "playbook_rules": playbook,
                    "retries": 0, "hallucination_errors": [], "security_metadata": meta
                })
                st.session_state.result = out["report"].get("findings", [])
                st.session_state.meta = meta

    with c2:
        findings, meta = st.session_state.result, st.session_state.meta
        if findings is None:
            st.info("👈 Upload a **PDF or ID Image (JPG/PNG)** or test the sample KYC text, then click **⚡ Run Audit**.")
        elif not findings:
            st.success("✅ Zero privacy or compliance violations detected!")
        else:
            weights = {"CRITICAL": 35, "HIGH": 25, "MEDIUM": 12, "LOW": 5}
            score = min(100, sum(weights.get(f["risk_level"], 10) for f in findings))
            m1, m2, m3 = st.columns(3)
            m1.metric("Risk Score", f"{score}/100", delta="High" if score >= 50 else "Low", delta_color="inverse")
            m2.metric("Violations", len(findings))
            m3.metric("PII Masked", meta["pii_redacted_count"])

            for item in findings:
                icon = "🚨" if item["risk_level"] == "CRITICAL" else ("🔴" if item["risk_level"] == "HIGH" else "🟡")
                with st.expander(f"{icon} [{item['risk_level']}] {item['clause_topic']}", expanded=True):
                    st.markdown(f"**Verified Quote:**\n> *\"{item['exact_quote']}\"*")
                    st.markdown(f"**Issue:** {item['violation_reason']}")
                    st.code(item["suggested_redline"], language="text")

with t_chart:
    if st.session_state.result:
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in st.session_state.result:
            counts[f["risk_level"]] = counts.get(f["risk_level"], 0) + 1
        st.bar_chart(counts)
    else:
        st.info("Run an audit first to view risk charts.")

with t_sec:
    st.json(st.session_state.meta or {"status": "Ready", "shield": "Aadhaar/PAN DPDP Guard Active"})

with t_info:
    st.markdown("""
    ### ⚖️ LEXGUARDIAN Enterprise Legal & ID Intelligence
    - **Architected & Engineered by:** **Vishal**
    - **Capabilities:** Contract Redlining, Aadhaar/PAN DPDP Privacy Auditing, Vision OCR for ID Images, and SHA-256 Audit Certificates.
    """)
