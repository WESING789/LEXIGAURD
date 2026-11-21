import json
from datetime import datetime
import streamlit as st
from pypdf import PdfReader
from agent import auditor_app, sanitize_and_fingerprint

st.set_page_config(page_title="LEXGUARDIAN | Legal AI", page_icon="⚖️", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .block-container { padding-top: 1.4rem; max-width: 1300px; }
    .lex-hero {
        background: linear-gradient(135deg, #090e1a 0%, #172033 100%);
        border: 1px solid #334155;
        border-radius: 16px;
        padding: 1.4rem 1.8rem;
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 1.2rem;
    }
    .lex-left { display: flex; align-items: center; gap: 1rem; }
    .lex-name {
        font-size: 2rem; font-weight: 800; letter-spacing: 1px;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0;
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
    div.stButton > button { border-radius: 10px; font-weight: 600; height: 45px; transition: all 0.2s ease; }
    div.stButton > button:hover { transform: translateY(-2px); }
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
            <div class="lex-tag">Zero-Trust Contract & Compliance Intelligence</div>
        </div>
    </div>
    <div class="lex-badge">🔒 Air-Gapped • DPDP PII Shield • SHA-256</div>
</div>
""", unsafe_allow_html=True)

PRESETS = {
    "🏢 Vendor & DPDP Compliance": """1. Data Localization (DPDP Act): Personal data MUST be stored strictly in India. No third-party sharing without written consent.\n2. Liability Cap: Vendor liability must NOT be capped below 12 months of fees paid.\n3. Exit Rights: No auto-renewal without 30 days notice; client must have 30-day termination for convenience.\n4. Governing Law: Laws of India with jurisdiction in Bengaluru or New Delhi.""",
    "💼 Job Offer Letter Check": """1. Notice Period: Notice period must NOT exceed 60 days and must apply equally to both employer and employee.\n2. Non-Compete: Post-employment non-compete clauses exceeding 6 months or blocking entire industries are unacceptable.\n3. IP Rights: Personal side-projects built outside work hours on personal devices must remain employee property.\n4. Salary & Probation: Probation must not exceed 6 months; variable pay terms must be clearly defined.""",
    "🤝 Freelance / Client Contract": """1. Payment Terms: Invoices must be paid within 15 to 30 days with late fee protection.\n2. Scope Creep: Revisions must be capped at 2 rounds; extra work requires written change orders.\n3. IP Transfer: Full copyright transfers ONLY after 100% final payment is received."""
}

SAMPLE_CONTRACT = """MASTER SERVICES AGREEMENT
1. DATA HANDLING: Vendor processes Client customer records (contact kiran@example.com, Aadhaar 2345 6789 0123) across US and Singapore servers and may share telemetry with ad affiliates.
2. LIMITATION OF LIABILITY: Vendor's total liability shall not exceed $500 USD, including for data breaches.
3. RENEWAL: Automatically renews for 3-year terms unless notified 180 days prior. Client cannot terminate for convenience.
4. JURISDICTION: Governed by the laws of Delaware, USA."""

if "result" not in st.session_state:
    st.session_state.result = None
if "meta" not in st.session_state:
    st.session_state.meta = None
if "history" not in st.session_state:
    st.session_state.history = []

t_work, t_chart, t_hist, t_sec, t_info = st.tabs([
    "⚖️ Audit Workspace", "📊 Risk Analytics", "🕒 Audit History", "🔐 Security Certificate", "ℹ️ Info"
])

with t_work:
    c1, c2 = st.columns([1, 1.15], gap="large")
    with c1:
        preset_choice = st.selectbox("⚡ Quick Rule Preset:", list(PRESETS.keys()))
        playbook = st.text_area("Compliance Rules:", value=PRESETS[preset_choice], height=155)

        uploaded = st.file_uploader("📄 Upload Contract PDF (Optional)", type=["pdf"])
        if uploaded:
            reader = PdfReader(uploaded)
            raw_text = "\n".join([p.extract_text() or "" for p in reader.pages[:20]])
            doc_name = uploaded.name
            st.caption(f"✅ Loaded {min(len(reader.pages), 20)} page(s) from {doc_name}")
        else:
            raw_text = st.text_area("Or edit sample contract:", value=SAMPLE_CONTRACT, height=175)
            doc_name = "Sample_MSA_Contract"

        b1, b2, b3 = st.columns([1.4, 1, 1], gap="small")
        with b1:
            run_btn = st.button("⚡ Run Audit", type="primary", use_container_width=True)
        with b2:
            pii_on = st.toggle("PII Mask", value=True)
        with b3:
            clear_btn = st.button("🗑️ Clear", use_container_width=True)

        if clear_btn:
            st.session_state.result = None
            st.session_state.meta = None
            st.rerun()

        if run_btn and raw_text.strip():
            with st.spinner("Masking PII • Auditing clauses • Verifying quotes..."):
                clean_txt, meta = sanitize_and_fingerprint(raw_text) if pii_on else (
                    raw_text, {"sha256": "OFF", "pii_redacted_count": 0, "timestamp_utc": datetime.now().strftime("%H:%M:%S"), "air_gapped": True}
                )
                out = auditor_app.invoke({
                    "contract_text": clean_txt, "playbook_rules": playbook,
                    "retries": 0, "hallucination_errors": [], "security_metadata": meta
                })
                findings = out["report"].get("findings", [])
                st.session_state.result = findings
                st.session_state.meta = meta
                st.session_state.history.insert(0, {"doc": doc_name, "time": meta["timestamp_utc"], "risks": len(findings)})

    with c2:
        findings, meta = st.session_state.result, st.session_state.meta
        if findings is None:
            st.info("👈 Choose a preset or upload a PDF, then click **⚡ Run Audit**.")
        elif not findings:
            st.success("✅ Zero violations found! Contract matches your rules.")
        else:
            weights = {"CRITICAL": 35, "HIGH": 25, "MEDIUM": 12, "LOW": 5}
            score = min(100, sum(weights.get(f["risk_level"], 10) for f in findings))
            m1, m2, m3 = st.columns(3)
            m1.metric("Risk Score", f"{score}/100", delta="High" if score >= 50 else "Low", delta_color="inverse")
            m2.metric("Violations", len(findings))
            m3.metric("PII Masked", meta["pii_redacted_count"])

            md = f"# LEXGUARDIAN Report\n**SHA-256:** `{meta['sha256']}` | **Score:** {score}/100\n\n"
            for i, item in enumerate(findings, 1):
                icon = "🚨" if item["risk_level"] == "CRITICAL" else ("🔴" if item["risk_level"] == "HIGH" else "🟡")
                with st.expander(f"{icon} [{item['risk_level']}] {item['clause_topic']}", expanded=True):
                    st.markdown(f"**Verified Quote:**\n> *\"{item['exact_quote']}\"*")
                    st.markdown(f"**Issue:** {item['violation_reason']}")
                    st.code(item["suggested_redline"], language="text")
                md += f"### {i}. [{item['risk_level']}] {item['clause_topic']}\n- Quote: \"{item['exact_quote']}\"\n- Fix: `{item['suggested_redline']}`\n\n"

            e1, e2 = st.columns(2, gap="small")
            with e1:
                st.download_button("📥 Download Report (.md)", md, "LEXGUARDIAN_Report.md", use_container_width=True)
            with e2:
                st.download_button("🧾 Download Data (.json)", json.dumps({"meta": meta, "findings": findings}, indent=2), "LEXGUARDIAN.json", use_container_width=True)

with t_chart:
    if st.session_state.result:
        counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
        for f in st.session_state.result:
            counts[f["risk_level"]] = counts.get(f["risk_level"], 0) + 1
        st.bar_chart(counts)
    else:
        st.info("Run an audit first to view risk charts.")

with t_hist:
    if st.session_state.history:
        st.table(st.session_state.history)
    else:
        st.info("Your session audit history will appear here.")

with t_sec:
    st.json(st.session_state.meta or {"status": "Ready", "network": "127.0.0.1 Localhost Only", "engine": "Air-Gapped"})

with t_info:
    st.markdown("""
    ### ⚖️ LEXGUARDIAN Enterprise Legal AI
    - **Architected & Engineered by:** **Vishal**
    - **Security Architecture:** 100% offline local LLM inference, XML prompt-injection sandboxing, automatic Indian/Global PII masking, and SHA-256 tamper-evident audit logs.
    """)
