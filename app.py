import streamlit as st
from pypdf import PdfReader
from agent import auditor_app, sanitize_and_fingerprint, ask_doc_question
st.set_page_config(page_title="LEXGUARDIAN | WE SEE ALL", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
@keyframes spin369 { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
@keyframes pulseLux { 0%, 100% { opacity: 0.85; } 50% { opacity: 1; } }
.stApp { background: radial-gradient(circle at top right, #17140d 0%, #070a12 45%, #05070d 100%); }
.lex-bar{background:linear-gradient(135deg,#070911 0%,#111622 55%,#1a160e 100%);border:1px solid rgba(251,191,36,0.45);border-radius:16px;padding:1.45rem 1.9rem;display:flex;justify-content:space-between;align-items:center;margin-bottom:0.95rem;box-shadow:0 14px 36px rgba(0,0,0,0.65)}
.lex-h1{font-size:2.15rem;font-weight:900;letter-spacing:3.8px;background:linear-gradient(180deg,#ffffff 0%,#e2e8f0 48%,#94a3b8 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;line-height:1.05}
.lex-motto{font-size:1.02rem;font-weight:800;letter-spacing:3px;background:linear-gradient(90deg,#99f6e4 0%,#2dd4bf 45%,#06b6d4 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin-top:0.28rem}
.lex-sub{color:#cbd5e1;font-size:0.81rem;letter-spacing:0.35px;margin-top:0.18rem}
.lex-badge{background:rgba(251,191,36,0.10);color:#fde68a;border:1px solid rgba(251,191,36,0.45);padding:0.35rem 0.95rem;border-radius:999px;font-size:0.74rem;font-weight:700;letter-spacing:1.1px}
div.stButton > button { background: linear-gradient(135deg, #1c1912 0%, #292214 100%) !important; color: #fde68a !important; border: 1px solid rgba(251,191,36,0.55) !important; border-radius: 10px !important; font-weight: 700 !important; height: 44px !important; letter-spacing: 0.6px !important; transition: all 0.25s ease !important; }
div.stButton > button:hover { background: linear-gradient(135deg, #2d2514 0%, #3f3218 100%) !important; border-color: #fbbf24 !important; transform: translateY(-2px) !important; }
div.stButton > button[kind="primary"] { background: linear-gradient(135deg, #fde68a 0%, #f59e0b 50%, #b45309 100%) !important; color: #090d16 !important; border: 1px solid #fef3c7 !important; box-shadow: 0 6px 22px rgba(245,158,11,0.38) !important; }
div.stDownloadButton > button { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%) !important; color: #5eead4 !important; border: 1px solid rgba(45,212,191,0.5) !important; border-radius: 10px !important; font-weight: 700 !important; }
.stTabs [data-baseweb="tab-list"] { background: rgba(15,23,42,0.85); border: 1px solid rgba(251,191,36,0.28); border-radius: 12px; padding: 5px; }
.stTabs [aria-selected="true"] { background: linear-gradient(90deg, rgba(245,158,11,0.25), rgba(45,212,191,0.2)) !important; color: #fde68a !important; border-bottom: 2px solid #fbbf24 !important; }
.lux-loader{background:linear-gradient(135deg,rgba(15,23,42,0.96),rgba(28,24,14,0.96));border:1px solid rgba(251,191,36,0.55);border-radius:12px;padding:1.25rem;text-align:center;margin:0.8rem 0;animation:pulseLux 2s infinite}
.lux-spin{display:inline-block;animation:spin369 2.6s linear infinite}
.good-card{background:linear-gradient(135deg,rgba(16,185,129,0.12),rgba(251,191,36,0.04));border:1px solid rgba(251,191,36,0.22);border-left:4px solid #10b981;border-radius:10px;padding:0.85rem 1rem;margin-bottom:0.65rem}
.bad-card{background:linear-gradient(135deg,rgba(239,68,68,0.13),rgba(251,191,36,0.04));border:1px solid rgba(251,191,36,0.22);border-left:4px solid #ef4444;border-radius:10px;padding:0.85rem 1rem;margin-bottom:0.55rem}
.hint-box{background:linear-gradient(90deg,rgba(251,191,36,0.09),rgba(45,212,191,0.06));border:1px solid rgba(251,191,36,0.32);border-radius:9px;padding:0.6rem 0.9rem;font-size:0.84rem;color:#fef3c7;margin-bottom:0.6rem}
</style><div class="lex-bar"><div style="display:flex;align-items:center;gap:1.25rem"><svg width="62" height="62" viewBox="0 0 100 100" fill="none"><defs><linearGradient id="platSilver" x1="0" y1="0" x2="100" y2="100"><stop offset="0%" stop-color="#ffffff"/><stop offset="50%" stop-color="#cbd5e1"/><stop offset="100%" stop-color="#64748b"/></linearGradient><linearGradient id="tealGlow" x1="0" y1="50" x2="100" y2="50"><stop offset="0%" stop-color="#5eead4"/><stop offset="100%" stop-color="#06b6d4"/></linearGradient></defs><polygon points="50,4 90,27 90,73 50,96 10,73 10,27" stroke="url(#platSilver)" stroke-width="2.4" fill="rgba(251,191,36,0.05)"/><polygon points="50,14 81,68 19,68" stroke="rgba(251,191,36,0.45)" stroke-width="1.4" fill="none"/><polygon points="50,86 81,32 19,32" stroke="rgba(45,212,191,0.45)" stroke-width="1.4" fill="none"/><path d="M22 39 H40 L50 50 L60 61 H78 A11 11 0 0 0 78 39 H60 L50 50 L40 61 H22 A11 11 0 0 1 22 39 Z" stroke="url(#tealGlow)" stroke-width="3.6" stroke-linejoin="round" fill="none"/><circle cx="50" cy="50" r="3.2" fill="#fde68a"/></svg><div><div class="lex-h1">LEXGUARDIAN</div><div class="lux-motto">WE SEE ALL</div><div class="lex-sub">Skip the fine print — catch hidden loopholes, contradictions &amp; traps instantly.</div></div></div><div class="lux-badge">3•6•9 SYMMETRY • SHA-256</div></div>
""", unsafe_allow_html=True)
with st.expander("New here? Quick 3-Step Guide (Click to hide/show)", expanded=True):
    g1, g2, g3 = st.columns(3)
    g1.markdown("**1. Pick & Paste**\nChoose document type, upload PDF or paste text *(or click **Load Sample**)*.")
    g2.markdown("**2. Set Priorities & Privacy**\nLeave custom rules blank to scan the whole file, or type specific checks first. Turn on **Mask PII** to hide IDs.")
    g3.markdown("**3. Run Audit**\nGet a verdict, 3-bullet summary & green fair points first. Toggle **Show Loopholes & Fixes** for hidden traps.")

PRESETS = {
    "Job Offer (Full Scan)": "OFFER LETTER (23/11/2026)\n1. SALARY: Paid on 1st of month with medical insurance.\n2. EXIT: Employee may resign anytime.\n3. FINE PRINT: Leaving within 24 months triggers a Rs. 2,00,000 bond and 90-day unpaid notice.",
    "Rent Agreement (Full Scan)": "RENT AGREEMENT (23/11/2026)\n1. REPAIRS: Landlord pays property tax.\n2. FLEXIBILITY: Tenant may vacate anytime.\n3. TRAP: Leaving before 11 months forfeits 100% of Rs. 50,000 deposit.",
    "Aadhaar & KYC Privacy (Full Scan)": "KYC FORM (23/11/2026)\nName: Rahul Sharma | Aadhaar: 4589 2314 9876 | PAN: ABCDE1234F\nConsent: Store unmasked Aadhaar overseas and share with ad partners.",
    "Loan & App Terms (Full Scan)": "SUBSCRIPTION TERMS (23/11/2026)\n1. TRIAL: Free 7-day trial.\n2. BILLING: Auto-locks into a 1-year non-refundable plan unless cancelled by post 60 days early."
}
for k, v in [("doc_input", ""), ("last_doc", ""), ("result", None), ("good", []), ("tldr", []), ("meta", None)]:
    if k not in st.session_state: st.session_state[k] = v
t1, t2, t3, t4 = st.tabs(["Audit Workspace", "Risk Analytics", "Security Certificate", "ⓘ Info & Button Guide"])
with t1:
    c1, c2 = st.columns([1, 1.2], gap="large")
    with c1:
        choice = st.selectbox("Step 1: Document Category", list(PRESETS.keys()))
        with st.expander("Optional: Custom Priority Checks (Leave blank to scan full document)"):
            playbook = st.text_area("Custom Priorities", value="", placeholder="e.g. Check if notice period is over 60 days or deposit is non-refundable... (disappears when you type)", height=85, label_visibility="collapsed")
        up = st.file_uploader("Step 2: Upload PDF OR Paste Text Below", type=["pdf"])
        b1, b2 = st.columns(2)
        if b1.button("Load Sample", use_container_width=True): st.session_state.doc_input = PRESETS[choice]; st.session_state.result = None; st.rerun()
        if b2.button("Clear Workspace", use_container_width=True): st.session_state.doc_input = ""; st.session_state.last_doc = ""; st.session_state.result = None; st.session_state.good = []; st.session_state.tldr = []; st.rerun()
        raw_text = "\n".join([p.extract_text() or "" for p in PdfReader(up).pages[:15]]) if up else st.text_area("Text", key="doc_input", placeholder="Paste contract, offer letter, rent agreement, or terms here...", height=150, label_visibility="collapsed")
        mode = st.radio("Step 3: Choose Strictness", ["Strict Audit (Every Small Point)", "Work Anyway (Dealbreakers Only)"], horizontal=True)
        a1, a2, a3 = st.columns([1.3, 1, 1.2])
        run_btn = a1.button("Run Audit", type="primary", use_container_width=True)
        pii_on = a2.toggle("Mask PII", value=False)
        reveal_details = a3.toggle("Show Loopholes & Fixes", value=False)
        st.markdown(f'<div class="hint-box"><b>Active:</b> {"Mask PII ON (IDs Scrubbed)" if pii_on else "Mask PII OFF"} • {"Showing Loopholes & Fixes" if reveal_details else "Summary View"}</div>', unsafe_allow_html=True)
        if run_btn and raw_text.strip():
            loader = st.empty()
            loader.markdown('<div class="lux-loader"><div class="lux-spin"><svg width="42" height="42" viewBox="0 0 64 64" fill="none"><path d="M18 10H46L34 32L46 54H18L30 32L18 10Z" stroke="#cbd5e1" stroke-width="3" fill="rgba(203,213,225,0.12)"/><path d="M16 32C16 25 26 25 32 32C38 39 48 39 48 32C48 25 38 25 32 32C26 39 16 39 16 32Z" stroke="#2dd4bf" stroke-width="2.5"/></svg></div><div style="color:#5eead4;font-weight:700;margin-top:0.4rem">Please wait — scanning fine print &amp; detecting hidden loopholes...</div></div>', unsafe_allow_html=True)
            try:
                clean, meta = sanitize_and_fingerprint(raw_text, mask_pii=pii_on)
                out = auditor_app.invoke({"contract_text": clean, "playbook_rules": playbook, "retries": 0, "hallucination_errors": [], "security_metadata": meta})
                st.session_state.last_doc = clean
                st.session_state.result, st.session_state.good, st.session_state.tldr, st.session_state.meta = out["report"].get("findings", []), out["report"].get("good", []), out["report"].get("tldr", []), meta
            except Exception as e: st.error(f"Scan Error: {e}")
            finally: loader.empty()
    with c2:
        res, good, tldr, meta = st.session_state.result, st.session_state.good, st.session_state.tldr, st.session_state.meta
        if res is None: st.info("!!! Follow Steps 1–3 on the left, or click **Load Sample** then **Run Audit**.")
        else:
            shown = [i for i in res if i.get("risk_level") in ("CRITICAL", "HIGH")] if "Work Anyway" in mode else res
            score = min(100, sum({"CRITICAL":35,"HIGH":25,"MEDIUM":12,"LOW":5}.get(f.get("risk_level","MEDIUM"),10) for f in shown))
            if score >= 50: st.error(f"VERDICT: HIGH RISK ({score}/100) — Do not sign without fixing highlighted traps.")
            elif score > 0: st.warning(f"VERDICT: CAUTION ({score}/100) — Review highlighted clauses before signing.")
            else: st.success("VERDICT: LOOKS SAFE (0/100) — No major traps detected.")
            m1, m2, m3 = st.columns(3); m1.metric("Risk Index", f"{score}/100"); m2.metric("Loopholes Found", len(shown)); m3.metric("Good Points", len(good))
            if tldr: st.info("**Quick Bottom Line (Skip Reading):**\n" + "\n".join([f"- {b}" for b in tldr]))
            if good:
                st.markdown("#### Good & Fair Points (Green = Safe)")
                for g in good: st.markdown(f'<div class="good-card"><b style="color:#34d399">[SAFE] {g.get("topic","Fair Clause")}</b><br><i>"{g.get("exact_quote","")}"</i><br>{g.get("benefit_summary","")}</div>', unsafe_allow_html=True)
            if reveal_details or st.checkbox("Ask AI to Reveal Hidden Loopholes & Safer Fixes", value=False):
                st.markdown("#### Hidden Loopholes & Contradictions (Red = Risky)")
                if not shown: st.success("Safe to proceed — no loopholes flagged.")
                rep = f"# LEXGUARDIAN — WE SEE ALL Report (Date: 23/11/2026)\nRisk Index: {score}/100\n\n"
                for i in shown:
                    st.markdown(f'<div class="bad-card"><b style="color:#f87171">[RISK: {i.get("risk_level","HIGH")}] {i.get("finding_type","TRAP")} — {i.get("clause_topic","Clause")}</b><br><i>"{i.get("exact_quote","")}"</i><br>{i.get("violation_reason","")}</div>', unsafe_allow_html=True)
                    st.code(i.get("suggested_redline", ""), language="text")
                    rep += f"## {i.get('clause_topic','')}\n- Fix: {i.get('suggested_redline','')}\n\n"
                st.download_button("Export Report", rep, "LEXGUARDIAN_Report.md", use_container_width=True)
            q = st.text_input("Ask a quick question about this document:", placeholder="e.g. Can they terminate me without notice? / Is my deposit refundable?")
            if q and st.session_state.last_doc:
                with st.spinner("Checking document..."): st.success(ask_doc_question(st.session_state.last_doc, q))
with t2:
    if st.session_state.result is not None: st.bar_chart({k: sum(1 for f in st.session_state.result if f.get("risk_level") == k) for k in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]})
    else: st.info("Run an audit first.")
with t3: st.json(st.session_state.meta or {"status": "Ready", "date": "23/11/2026", "format": "DD/MM/YYYY", "storage": "Zero-Retention Memory"})
with t4: st.markdown("### LEXGUARDIAN — WE SEE ALL\n- **Architected & Engineered by:** **WESING** | **Date:** 23/11/2026 (DD/MM/YYYY)\n\n#### How Custom Priority Checks Work\n- **Leave Blank:** Scans the entire document broadly for all fair clauses, hidden loopholes, and contradictions.\n- **Type Your Concerns:** Checks your typed priorities FIRST, then flags any other major traps.\n\n#### Button Guide\n- **Load Sample:** Loads a realistic test document.\n- **Clear Workspace:** Clears all text & results.\n- **Strict Audit vs. Work Anyway:** Strict catches every loophole; Work Anyway flags major dealbreakers only.\n- **Mask PII:** Hides Aadhaar/PAN/Email/Phone before scanning.\n- **Show Loopholes & Fixes:** Reveals red trap alerts and safer replacement wording.")
