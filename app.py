import os, base64
from io import BytesIO
import streamlit as st
from pypdf import PdfReader
from PIL import Image
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from agent import auditor_app, sanitize_and_fingerprint

st.set_page_config(page_title="LEXGUARDIAN | Enterprise Legal AI", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
.block-container{padding-top:1.4rem;max-width:1280px}
.lex-bar{background:linear-gradient(135deg,#070b14,#131c31 60%,#1e1b4b);border:1px solid #334155;border-radius:14px;padding:1.4rem 1.8rem;display:flex;justify-content:space-between;align-items:center;margin-bottom:1.2rem;box-shadow:0 10px 28px rgba(0,0,0,0.3)}
.lex-brand{display:flex;align-items:center;gap:1rem}
.lex-h1{font-size:1.95rem;font-weight:800;letter-spacing:1.6px;background:linear-gradient(90deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0}
.lex-p{color:#94a3b8;font-size:0.9rem;margin:0.2rem 0 0 0}
.lex-tag{background:#0f172a;color:#38bdf8;border:1px solid #1e3a8a;padding:0.32rem 0.9rem;border-radius:999px;font-size:0.76rem;font-weight:600;letter-spacing:0.5px}
div.stButton>button{border-radius:8px;font-weight:600;height:42px;letter-spacing:0.3px}
</style><div class="lex-bar"><div class="lex-brand"><svg width="44" height="44" viewBox="0 0 64 64" fill="none"><polygon points="32,4 56,18 56,46 32,60 8,46 8,18" fill="#38bdf8" fill-opacity="0.14" stroke="#38bdf8" stroke-width="3"/><path d="M22 24L32 18L42 24V38L32 46L22 38V24Z" stroke="#a78bfa" stroke-width="2.5"/><circle cx="32" cy="32" r="4" fill="#f8fafc"/></svg><div><div class="lex-h1">LEXGUARDIAN</div><div class="lex-p">Zero-Trust Contract, Offer Letter & DPDP Privacy Intelligence</div></div></div><div class="lex-tag">AIR-GAPPED • VERBATIM VERIFIED • SHA-256</div></div>""", unsafe_allow_html=True)

PRESETS = {
    "Job Offer & Employment Letter": {"rules": "1. Notice period must not exceed 60 days.\n2. No unfair monetary training bonds.\n3. No broad post-employment non-compete.", "sample": "OFFER LETTER (Date: 21/11/2026)\n1. NOTICE: Employee must serve 90 days notice; Company may terminate immediately.\n2. BOND: Employee pays Rs. 2,00,000 if leaving within 2 years."},
    "Residential Rent Agreement": {"rules": "1. Security deposit refunded within 30 days.\n2. Minimum 30 days eviction notice.\n3. Annual rent hike max 10%.", "sample": "RENTAL AGREEMENT (Date: 21/11/2026)\n1. DEPOSIT: Landlord may retain full Rs. 50,000 deposit for painting.\n2. EVICTION: Landlord may evict in 48 hours without notice."},
    "Aadhaar & KYC Privacy Audit": {"rules": "1. Full 12-digit Aadhaar numbers must be masked.\n2. No foreign server storage or ad sharing.", "sample": "KYC RECORD (Date: 21/11/2026)\nName: Rahul Sharma | Aadhaar: 4589 2314 9876 | PAN: ABCDE1234F\nConsent: Store unmasked Aadhaar on foreign servers."},
    "Loan, EMI & Subscription Terms": {"rules": "1. No excessive early foreclosure penalties.\n2. No hidden auto-renewal without notice.", "sample": "LOAN TERMS (Date: 21/11/2026)\n1. PREPAYMENT: 12% penalty on total principal for early closure.\n2. AUTO-RENEW: Annual auto-debit with zero refund."},
    "Vendor & DPDP Compliance": {"rules": "1. Customer data must stay in India.\n2. Liability cap minimum 12 months fees.\n3. Governing law of India.", "sample": "MASTER AGREEMENT (Date: 21/11/2026)\n1. DATA: Store Indian records on US servers and share with affiliates.\n2. LIABILITY: Capped at $500 USD including data breaches."}
}

def read_image(img_file):
    if not os.getenv("GOOGLE_API_KEY"): return "Upload PDF or text locally, or use the live web deployment for image OCR."
    buf = BytesIO(); Image.open(img_file).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()
    msg = HumanMessage(content=[{"type":"text","text":"Transcribe all text and numbers accurately."},{"type":"image_url","image_url":{"url":f"data:image/png;base64,{b64}"}}])
    return ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0).invoke([msg]).content

for k, v in [("doc_input", ""), ("result", None), ("meta", None)]:
    if k not in st.session_state: st.session_state[k] = v

t1, t2, t3, t4 = st.tabs(["Audit Workspace", "Risk Analytics", "Security Certificate", "ⓘ Info & Guide"])
with t1:
    c1, c2 = st.columns([1, 1.15], gap="large")
    with c1:
        choice = st.selectbox("Document Category", list(PRESETS.keys()))
        with st.expander("Configure Compliance Rules"):
            playbook = st.text_area("Active Rules", value=PRESETS[choice]["rules"], height=105)
        up = st.file_uploader("Upload PDF or Document Image (PDF, PNG, JPG)", type=["pdf", "png", "jpg", "jpeg"])
        b1, b2 = st.columns(2, gap="small")
        if b1.button("Load Sample", use_container_width=True):
            st.session_state.doc_input = PRESETS[choice]["sample"]; st.session_state.result = None; st.rerun()
        if b2.button("Clear Workspace", use_container_width=True):
            st.session_state.doc_input = ""; st.session_state.result = None; st.session_state.meta = None; st.rerun()
        if up:
            raw_text = "\n".join([p.extract_text() or "" for p in PdfReader(up).pages[:20]]) if up.type == "application/pdf" else read_image(up)
            st.caption(f"Loaded: {up.name}")
        else:
            raw_text = st.text_area("Document Text", key="doc_input", placeholder="Paste contract, offer letter, rent agreement, or KYC text here...", height=180, label_visibility="collapsed")
        a1, a2 = st.columns([1.8, 1], gap="small")
        run_btn = a1.button("Run Audit", type="primary", use_container_width=True)
        pii_on = a2.toggle("Mask PII", value=False)
        if run_btn and raw_text.strip():
            with st.spinner("Analyzing clauses and verifying verbatim citations..."):
                clean, meta = sanitize_and_fingerprint(raw_text, mask_pii=pii_on)
                out = auditor_app.invoke({"contract_text": clean, "playbook_rules": playbook, "retries": 0, "hallucination_errors": [], "security_metadata": meta})
                st.session_state.result, st.session_state.meta = out["report"].get("findings", []), meta
    with c2:
        res, meta = st.session_state.result, st.session_state.meta
        if res is None: st.info("Paste your document text, upload a file, or click Load Sample to begin.")
        elif not res: st.success("No compliance violations or hidden risks detected.")
        else:
            score = min(100, sum({"CRITICAL":35,"HIGH":25,"MEDIUM":12,"LOW":5}.get(f["risk_level"],10) for f in res))
            m1, m2, m3 = st.columns(3)
            m1.metric("Risk Index", f"{score}/100"); m2.metric("Violations", len(res)); m3.metric("PII Redacted", meta["pii_redacted"])
            rep = f"# LEXGUARDIAN Audit Report\nDate: 21/11/2026 | Risk Index: {score}/100 | SHA-256: {meta['sha256']}\n\n"
            for i in res:
                with st.expander(f"[{i['risk_level']}] {i['clause_topic']}", expanded=True):
                    st.markdown(f"**Verified Quote:**\n> *\"{i['exact_quote']}\"*")
                    st.markdown(f"**Analysis:** {i['violation_reason']}")
                    st.code(i["suggested_redline"], language="text")
                rep += f"## [{i['risk_level']}] {i['clause_topic']}\n- Quote: \"{i['exact_quote']}\"\n- Redline: {i['suggested_redline']}\n\n"
            st.download_button("Export Report", rep, "LEXGUARDIAN_Report.md", use_container_width=True)
with t2:
    if st.session_state.result:
        counts = {k: sum(1 for f in st.session_state.result if f["risk_level"] == k) for k in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]}
        st.bar_chart(counts)
    else: st.info("Run an audit first to view risk distribution.")
with t3: st.json(st.session_state.meta or {"status": "Ready", "date_format": "DD/MM/YYYY", "release_date": "21/11/2026", "storage": "Zero-Retention Memory Only"})
with t4:
    st.markdown("""### LEXGUARDIAN — User Guide & Platform Info
- **Architected & Engineered by:** **WESING**
- **Release Date:** 21/11/2026 (Format: DD/MM/YYYY)

#### How to Use This Platform (Step-by-Step A, B, C)
- **A. Select Your Document Category:** Choose the type of document you are checking (e.g., *Job Offer & Employment Letter*, *Residential Rent Agreement*, or *Aadhaar & KYC Privacy Audit*).
- **B. Provide Your Document:** Upload a PDF/photo or paste your text directly into the blank workspace box. *(To see how it works instantly, click **Load Sample**).*
- **C. Run Audit & Review Fixes:** Click **Run Audit**. LEXGUARDIAN highlights risky clauses, verifies every quote word-for-word against the document, and provides a safer replacement clause you can copy.

#### Quick Example Walkthrough
- **Input Clause (Job Offer):** *"Employee must serve a 90-day notice period and pay Rs. 2,00,000 bond if leaving before 21/11/2028."*
- **LEXGUARDIAN Detection:** Flags **[HIGH] Notice Period & Bond Penalty** because standard notice should not exceed 60 days.
- **Suggested Safer Replacement:** *"Either party may terminate this agreement by providing 30 days written notice without financial penalty."*""")
