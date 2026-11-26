import streamlit as st
from pypdf import PdfReader
from agent import sanitize_and_fingerprint, run_audit_with_critic, ask_doc_question
import critic_engine, ui_upgrades

st.set_page_config(page_title="LEXGUARDIAN — WE SEE ALL", layout="wide")
ui_upgrades.inject_luxury_theme()

st.markdown("""<div style="display:flex;align-items:center;gap:14px;padding:6px 0 12px 0;">
  <svg width="46" height="46" viewBox="0 0 100 100" fill="none">
    <polygon points="50,5 91,27 91,73 50,95 9,73 9,27" stroke="#00F5D4" stroke-width="4" fill="#0B0E17"/>
    <circle cx="50" cy="50" r="18" stroke="#FF2A6D" stroke-width="3.5" fill="none"/>
  </svg>
  <div>
    <div style="font-size:1.75rem;font-weight:900;letter-spacing:3px;color:#F8FAFC;">LEXGUARDIAN</div>
    <div style="font-size:0.82rem;letter-spacing:3px;color:#00F5D4;">
      <svg width="20" height="20" viewBox="0 0 100 100" fill="none" style="vertical-align:middle;margin-right:4px;">
        <path d="M10 22 L28 84 L50 42 L72 84 L90 22 L76 22 L66 58 L50 28 L34 58 L24 22 Z" fill="#E2E8F0" stroke="#00F5D4" stroke-width="4"/>
      </svg> WE SEE ALL
    </div>
  </div>
</div>""", unsafe_allow_html=True)

PRESETS = {
    "Platform T&Cs (Zomato Style)": "TERMS OF SERVICE\n1. ACCESS: Enjoy food delivery services.\n2. FEES & RULES: Platform may modify commissions, fees, or suspend accounts anytime without prior notice. All charges are non-refundable.",
    "Job Offer (Full Scan)": "OFFER LETTER\n1. SALARY: Paid on 1st of month with medical cover.\n2. EXIT: Employee may resign anytime.\n3. FINE PRINT: Leaving within 24 months triggers a Rs. 2,00,000 bond and 90-day unpaid notice.",
    "Rent Agreement (Full Scan)": "RENT AGREEMENT\n1. REPAIRS: Landlord pays property tax.\n2. EXIT: Tenant may vacate anytime.\n3. TRAP: Leaving before 11 months forfeits 100% of Rs. 50,000 deposit.",
    "Aadhaar & KYC Privacy": "KYC FORM\nName: Rahul Sharma | Aadhaar: 4589 2314 9876 | PAN: ABCDE1234F\nConsent: Store unmasked Aadhaar overseas and share with ad partners."
}

for k, v in [("doc_input", ""), ("last_doc", ""), ("result", None), ("good", []), ("tldr", []), ("meta", None)]:
    if k not in st.session_state:
        st.session_state[k] = v
t1, t2, t3, t4 = st.tabs(["Audit Workspace", "Risk Analytics", "Security Certificate", "Info & Button Guide"])

with t1:
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        choice = st.selectbox("Step 1: Document Category", list(PRESETS.keys()))
        with st.expander("Optional: Custom Priority Checks"):
            playbook = st.text_area("Priorities", value="", placeholder="e.g. Check notice period or deposit rules...", height=75, label_visibility="collapsed")
        up = st.file_uploader("Step 2: Upload PDF OR Paste Text Below", type=["pdf"])
        b1, b2 = st.columns(2)
        if b1.button("Load Sample", use_container_width=True):
            st.session_state.doc_input = PRESETS[choice]; st.session_state.result = None; st.rerun()
        if b2.button("Clear Workspace", use_container_width=True):
            st.session_state.doc_input = ""; st.session_state.last_doc = ""; st.session_state.result = None; st.session_state.good = []; st.session_state.tldr = []; st.session_state["da_res"] = None; st.rerun()
        raw_text = "\n".join([p.extract_text() or "" for p in PdfReader(up).pages[:15]]) if up else st.text_area("Text", key="doc_input", placeholder="Paste contract, offer letter, rent agreement, or T&Cs here...", height=150, label_visibility="collapsed")
        mode = st.radio("Step 3: Choose Strictness", ["Strict Audit (Every Small Point)", "Work Anyway (Dealbreakers Only)"], horizontal=True)
        a1, a2, a3 = st.columns([1.3, 1, 1.2])
        run_btn = a1.button("Run Audit", type="primary", use_container_width=True)
        pii_on = a2.toggle("Mask PII", value=False)
        reveal_details = a3.toggle("Show Loopholes & Fixes", value=True)
        if run_btn and raw_text.strip():
            loader = st.empty()
            loader.markdown(ui_upgrades.squared_infinity_loader(), unsafe_allow_html=True)
            try:
                clean, meta = sanitize_and_fingerprint(raw_text, mask_pii=pii_on)
                rep, da = run_audit_with_critic(clean, playbook)
                st.session_state.last_doc = clean
                st.session_state.result = rep["findings"]
                st.session_state.good = rep["good"]
                st.session_state.tldr = rep["tldr"]
                st.session_state.meta = meta
                st.session_state["da_res"] = da
            except Exception as e:
                st.error(f"Scan Error: {e}")
            finally:
                loader.empty()
    with c2:
        res, good, tldr = st.session_state.result, st.session_state.good, st.session_state.tldr
        if res is None:
            st.info("Follow Steps 1-3 on the left, or click Load Sample then Run Audit.")
        else:
            shown = [i for i in res if i.get("risk_level") in ("CRITICAL", "HIGH")] if "Work Anyway" in mode else res
            score = min(100, sum({"CRITICAL": 35, "HIGH": 25, "MEDIUM": 12, "LOW": 5}.get(f.get("risk_level", "HIGH"), 15) for f in shown))
            if score >= 50: st.error(f"VERDICT: HIGH RISK ({score}/100) — Do not sign without fixing highlighted traps.")
            elif score > 0: st.warning(f"VERDICT: CAUTION ({score}/100) — Review highlighted clauses before signing.")
            else: st.success("VERDICT: LOOKS SAFE (0/100)")
            m1, m2, m3 = st.columns(3)
            m1.metric("Risk Index", f"{score}/100"); m2.metric("Loopholes Found", len(shown)); m3.metric("Good Points", len(good))
            if tldr: st.info("**Quick Bottom Line:**\n" + "\n".join([f"- {b}" for b in tldr]))
            if good:
                st.markdown("#### Good & Fair Points (Green = Safe)")
                for g in good: st.markdown(f'<div class="good-card"><b style="color:#00F5D4">[SAFE] {g.get("topic","Fair Clause")}</b><br><i>"{g.get("exact_quote","")}"</i><br>{g.get("benefit_summary","")}</div>', unsafe_allow_html=True)
            if reveal_details:
                st.markdown("#### Hidden Loopholes & Contradictions (Red = Risky)")
                for i in shown:
                    st.markdown(f'<div class="bad-card"><b style="color:#FF2A6D">[RISK: {i.get("risk_level","HIGH")}] {i.get("finding_type","TRAP")} — {i.get("clause_topic","Clause")}</b><br><i>"{i.get("exact_quote","")}"</i><br>{i.get("violation_reason","")}</div>', unsafe_allow_html=True)
                    st.code(i.get("suggested_redline", ""), language="text")
            q = st.text_input("Ask a quick question about this document:", placeholder="e.g. Is my deposit refundable?")
            if q and st.session_state.last_doc:
                st.write(ask_doc_question(st.session_state.last_doc, q))

    st.markdown("---")
    st.markdown("### DEVIL'S ADVOCATE — RUTHLESS CONTRACT CRITIC")
    u1, u2 = st.columns(2)
    pdf = u1.file_uploader("Upload PDF/TXT (or auto-uses Audit doc):", type=["pdf", "txt"], key="da_pdf")
    paste = u2.text_area("Or Paste Contract Text:", height=100, key="da_txt")
    b1, b2, b3 = st.columns([2, 1.5, 1])
    lang = b1.selectbox("Extra Language Block:", ["None", "Hinglish", "Hindi", "Tamil", "Marathi", "Bengali", "Spanish"], key="da_lang")
    txt = (critic_engine.extract_uploaded_text(pdf) if pdf else "") or paste.strip() or st.session_state.get("last_doc", "") or st.session_state.get("doc_input", "")
    ui_upgrades.sync_da_workspace(txt)
    if b3.button("Reset Workspace", key="da_clr"):
        st.session_state["da_res"] = None; st.session_state["pers_plan"] = ""; st.session_state["da_hash"] = ""
    if b2.button("UNLEASH DEVIL'S ADVOCATE", key="da_go") and txt.strip():
        ld = st.empty(); ld.markdown(ui_upgrades.render_yinyang_loader(), unsafe_allow_html=True)
        st.session_state["da_res"] = critic_engine.run_adversarial_critic(txt, lang); st.session_state["pers_plan"] = ""; ld.empty()
    ui_upgrades.render_devils_advocate_suite(txt, lang)

with t2:
    ui_upgrades.render_risk_analytics()

with t3:
    meta = st.session_state.get("meta")
    if not meta:
        st.info("Run an Audit in Audit Workspace to generate a cryptographic SHA-256 Security Certificate.")
    else:
        st.success("CRYPTOGRAPHIC AUDIT CERTIFICATE VERIFIED")
        st.json(meta)

with t4:
    st.markdown("### How to Use LEXGUARDIAN\n1. **Audit Workspace:** Upload a PDF or paste text, toggle **Mask PII**, and click **Run Audit**.\n2. **Devil's Advocate:** Review the `0-100` Safety Score, `₹ (INR)` Mistake Bill, and Personalized Habit Simulator.\n3. **Risk Analytics:** View Donut & Bar charts of your contract's risk exposure.")
