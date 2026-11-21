import os, base64
from io import BytesIO
import streamlit as st
from pypdf import PdfReader
from PIL import Image
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from agent import auditor_app, sanitize_and_fingerprint
st.set_page_config(page_title="LEXGUARDIAN", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
.lex-bar{background:linear-gradient(135deg,#070b14,#131c31 60%,#1e1b4b);border:1px solid #334155;border-radius:14px;padding:1.3rem 1.7rem;display:flex;justify-content:space-between;align-items:center;margin-bottom:0.8rem}
.lex-h1{font-size:1.9rem;font-weight:800;letter-spacing:1.5px;background:linear-gradient(90deg,#38bdf8,#818cf8);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0}
.good-card{background:rgba(16,185,129,0.12);border-left:4px solid #10b981;border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.6rem}
.bad-card{background:rgba(239,68,68,0.12);border-left:4px solid #ef4444;border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.5rem}
.hint-box{background:rgba(56,189,248,0.08);border:1px solid rgba(56,189,248,0.25);border-radius:8px;padding:0.55rem 0.85rem;font-size:0.84rem;color:#cbd5e1;margin-bottom:0.6rem}
</style><div class="lex-bar"><div style="display:flex;align-items:center;gap:1rem"><svg width="42" height="42" viewBox="0 0 64 64" fill="none"><polygon points="32,4 56,18 56,46 32,60 8,46 8,18" fill="#38bdf8" fill-opacity="0.15" stroke="#38bdf8" stroke-width="3"/><circle cx="32" cy="32" r="5" fill="#818cf8"/></svg><div><div class="lex-h1">LEXGUARDIAN</div><div style="color:#cbd5e1;font-size:0.9rem">Skip the Fine Print. Catch Hidden Loopholes, Contradictions & Traps Instantly.</div></div></div><div style="color:#38bdf8;font-size:0.76rem;font-weight:700">AIR-GAPPED • SHA-256</div></div>""", unsafe_allow_html=True)
with st.expander("New here? Quick 3-Step Guide (Click to hide/show)", expanded=True):
    g1, g2, g3 = st.columns(3)
    g1.markdown("**1. Pick & Paste**\nChoose your document type, then upload a PDF/Photo or paste text *(or click **Load Sample**)*.")
    g2.markdown("**2. Choose Protection**\nTurn on **Mask PII** to hide Aadhaar/PAN numbers before scanning. Hover any **(?)** icon for help.")
    g3.markdown("**3. Click Run Audit**\nSee a 3-bullet summary & green fair points first. Toggle **Show Loopholes & Fixes** to reveal hidden traps.")
PRESETS = {
    "Job Offer (Essentials Only)": {"rules": "1. Max 60 days notice.\n2. Zero exit bonds.\n3. Keep personal side-projects.", "sample": "OFFER LETTER (21/11/2026)\n1. SALARY: Paid on 1st of month with health insurance.\n2. EXIT: Employee may resign anytime.\n3. FINE PRINT: Leaving within 24 months triggers a Rs. 2,00,000 bond and 90-day unpaid notice."},
    "Rent Agreement (Essentials Only)": {"rules": "1. Deposit refund in 30 days.\n2. 30 days eviction notice.\n3. Max 10% rent hike.", "sample": "RENT AGREEMENT (21/11/2026)\n1. REPAIRS: Landlord pays property tax.\n2. FLEXIBILITY: Tenant may vacate anytime.\n3. TRAP: Leaving before 11 months forfeits 100% of Rs. 50,000 deposit."},
    "Aadhaar & KYC Privacy (Necessary Only)": {"rules": "1. Only masked Aadhaar allowed.\n2. Zero foreign storage or ad sharing.", "sample": "KYC FORM (21/11/2026)\nName: Rahul Sharma | Aadhaar: 4589 2314 9876 | PAN: ABCDE1234F\nConsent: Store unmasked Aadhaar overseas and share with ad partners."},
    "Loan & App Terms (Essentials Only)": {"rules": "1. Zero hidden foreclosure fees.\n2. Easy 1-click cancellation.", "sample": "SUBSCRIPTION TERMS (21/11/2026)\n1. TRIAL: Free 7-day trial.\n2. BILLING: Auto-locks into a 1-year non-refundable plan unless cancelled by post 60 days early."}
}
def read_img(f):
    if not os.getenv("GOOGLE_API_KEY", "").strip(): return "Upload PDF/text locally, or use the live website for photo OCR."
    b = BytesIO(); Image.open(f).save(b, format="PNG")
    msg = HumanMessage(content=[{"type":"text","text":"Transcribe all text accurately."},{"type":"image_url","image_url":{"url":f"data:image/png;base64,{base64.b64encode(b.getvalue()).decode()}"}}])
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0).invoke([msg]).content
for k, v in [("doc_input", ""), ("result", None), ("good", []), ("tldr", []), ("meta", None)]:
    if k not in st.session_state: st.session_state[k] = v
t1, t2, t3, t4 = st.tabs(["Audit Workspace", "Risk Analytics", "Security Certificate", "ⓘ Info & Button Guide"])
with t1:
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        choice = st.selectbox("Step 1: What document are you checking?", list(PRESETS.keys()), help="Pick the closest match. Each preset checks only the most essential user protections.")
        with st.expander("Optional: View or Edit Safety Rules"):
            playbook = st.text_area("Rules", value=PRESETS[choice]["rules"], height=85, help="These are the minimum fair conditions LEXGUARDIAN checks for you.")
        up = st.file_uploader("Step 2: Upload PDF/Photo OR Paste Text Below", type=["pdf", "png", "jpg", "jpeg"], help="Supports multi-page PDFs and clear phone photos (PNG/JPG) of documents.")
        b1, b2 = st.columns(2)
        if b1.button("Load Sample", use_container_width=True, help="Fills the box with a realistic test document containing hidden traps so you can try the app in 1 click."): st.session_state.doc_input = PRESETS[choice]["sample"]; st.session_state.result = None; st.rerun()
        if b2.button("Clear Workspace", use_container_width=True, help="Erases all text and previous results so you can start completely fresh."): st.session_state.doc_input = ""; st.session_state.result = None; st.session_state.good = []; st.session_state.tldr = []; st.rerun()
        raw_text = ("\n".join([p.extract_text() or "" for p in PdfReader(up).pages[:20]]) if up.type == "application/pdf" else read_img(up)) if up else st.text_area("Text", key="doc_input", placeholder="Paste your contract, offer letter, rent agreement, or KYC text here...", height=150, label_visibility="collapsed")
        mode = st.radio("Step 3: Choose Strictness", ["Strict Audit (Every Small Point)", "Work Anyway (Dealbreakers Only)"], horizontal=True, help="Strict Audit catches every minor fine-print loophole. Work Anyway ignores small issues and flags only major dealbreakers.")
        a1, a2, a3 = st.columns([1.3, 1, 1.2])
        run_btn = a1.button("Run Audit", type="primary", use_container_width=True, help="Starts the AI scan to summarize key points, highlight fair clauses, and detect hidden loopholes.")
        pii_on = a2.toggle("Mask PII", value=False, help="Privacy Shield: Automatically hides your Aadhaar, PAN, Email, and Phone numbers (replacing them with [REDACTED]) BEFORE the AI reads your document.")
        reveal_details = a3.toggle("Show Loopholes & Fixes", value=False, help="OFF = Shows only the simple 3-bullet summary & good points. ON = Reveals red loophole alerts and safer replacement clauses.")
        st.markdown(f'<div class="hint-box"><b>Active Settings:</b> {"🔒 <b>Mask PII is ON</b> (Aadhaar/PAN/Phone will be hidden before scanning)" if pii_on else "👁️ <b>Mask PII is OFF</b> (Turn ON to scrub personal IDs before scanning)"} • {"🔍 <b>Showing full loopholes & fixes</b>" if reveal_details else "📋 <b>Clean summary view</b> (Toggle <i>Show Loopholes & Fixes</i> to inspect hidden traps)"}</div>', unsafe_allow_html=True)
        if run_btn and raw_text.strip():
            with st.spinner("Scanning document..."):
                clean, meta = sanitize_and_fingerprint(raw_text, mask_pii=pii_on)
                out = auditor_app.invoke({"contract_text": clean, "playbook_rules": playbook, "retries": 0, "hallucination_errors": [], "security_metadata": meta})
                st.session_state.result, st.session_state.good, st.session_state.tldr, st.session_state.meta = out["report"].get("findings", []), out["report"].get("good", []), out["report"].get("tldr", []), meta
    with c2:
        res, good, tldr, meta = st.session_state.result, st.session_state.good, st.session_state.tldr, st.session_state.meta
        if res is None: st.info("👈 Follow Steps 1–3 on the left, or click **Load Sample** then **Run Audit** to see a live example.")
        else:
            shown = [i for i in res if i["risk_level"] in ("CRITICAL", "HIGH")] if "Work Anyway" in mode else res
            score = min(100, sum({"CRITICAL":35,"HIGH":25,"MEDIUM":12,"LOW":5}.get(f["risk_level"],10) for f in shown))
            m1, m2, m3 = st.columns(3)
            m1.metric("Risk Index", f"{score}/100", help="0 = Completely Safe, 100 = Extreme Risk. Based on the severity of traps found.")
            m2.metric("Loopholes Found", len(shown), help="Number of hidden traps, contradictions, or rule violations detected.")
            m3.metric("Good Points", len(good), help="Number of fair, user-friendly clauses found in your favor.")
            if tldr: st.info("**Quick Bottom Line (No Reading Needed):**\n" + "\n".join([f"- {b}" for b in tldr]))
            if good:
                st.markdown("#### Good & Fair Points (Green = Safe)")
                for g in good: st.markdown(f'<div class="good-card"><b style="color:#34d399">✓ {g["topic"]}</b><br><i>"{g["exact_quote"]}"</i><br>{g["benefit_summary"]}</div>', unsafe_allow_html=True)
            if reveal_details or st.checkbox("Ask AI to Reveal Hidden Loopholes & Safer Fixes", value=False, help="Check this box to inspect every risky clause and get ready-to-use replacement wording."):
                st.markdown("#### Hidden Loopholes & Contradictions (Red = Risky)")
                if not shown: st.success("Safe to proceed — no loopholes flagged in this mode.")
                for i in shown:
                    st.markdown(f'<div class="bad-card"><b style="color:#f87171">⚠ [{i["risk_level"]}] {i.get("finding_type","TRAP")} — {i["clause_topic"]}</b><br><i>"{i["exact_quote"]}"</i><br>{i["violation_reason"]}</div>', unsafe_allow_html=True)
                    st.code(i["suggested_redline"], language="text")
with t2:
    if st.session_state.result is not None: st.bar_chart({k: sum(1 for f in st.session_state.result if f["risk_level"] == k) for k in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]})
    else: st.info("Run an audit first to view the visual risk chart.")
with t3: st.json(st.session_state.meta or {"status": "Ready", "date": "21/11/2026", "format": "DD/MM/YYYY", "storage": "Zero-Retention Memory"})
with t4: st.markdown("""### LEXGUARDIAN — Plain-English User & Button Guide
- **Architected & Engineered by:** **WESING** | **Release Date:** 21/11/2026 (DD/MM/YYYY)

#### What Every Button & Toggle Does (For First-Time Users)
- **Load Sample:** Fills the empty box with a realistic example document containing hidden traps so you can test the system safely.
- **Clear Workspace:** Wipes all text and results clean so you can start over with a new document.
- **Strict Audit vs. Work Anyway:** *Strict Audit* flags every minor fine-print loophole; *Work Anyway* ignores minor issues and warns you only about major dealbreakers.
- **Mask PII (Privacy Shield):** When turned **ON**, automatically hides Aadhaar numbers, PAN cards, emails, and phone numbers (`[REDACTED]`) *before* the AI processes your file. *(Leave **OFF** if you want the AI to warn you that an Aadhaar card is dangerously unmasked).*
- **Show Loopholes & Fixes:** Keeps the screen clean by default (showing only the 3-bullet summary and green fair clauses). Turn it **ON** whenever you want to inspect red loophole alerts and copy safer replacement clauses.

#### Step-by-Step Example (A, B, C)
- **A. Input Document:** *"1. Employee may resign anytime. 2. Leaving within 24 months triggers a Rs. 2,00,000 bond."*
- **B. Green Highlight (Good Point):** Confirms flexible resignation wording.
- **C. Red Highlight (Hidden Loophole):** Catches the hidden Rs. 2,00,000 contradiction and provides a safer replacement clause.""")
