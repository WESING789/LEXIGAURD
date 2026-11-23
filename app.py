import streamlit as st
from pypdf import PdfReader
from agent import auditor_app, sanitize_and_fingerprint, ask_doc_question
st.set_page_config(page_title="WE SEE ALL", layout="wide", initial_sidebar_state="collapsed")
st.markdown("""<style>
.lex-bar{background:linear-gradient(135deg,#050811,#0f172a 55%,#1e1b4b);border:1px solid rgba(56,189,248,0.35);border-radius:16px;padding:1.35rem 1.8rem;display:flex;justify-content:space-between;align-items:center;margin-bottom:0.85rem;box-shadow:0 12px 32px rgba(0,0,0,0.4)}
.lex-h1{font-size:2.05rem;font-weight:900;letter-spacing:3px;background:linear-gradient(90deg,#38bdf8,#a78bfa,#34d399);-webkit-background-clip:text;-webkit-text-fill-color:transparent;margin:0;line-height:1.1}
.lex-sub{color:#94a3b8;font-size:0.84rem;letter-spacing:0.4px;margin-top:0.25rem}
.good-card{background:rgba(16,185,129,0.12);border-left:4px solid #10b981;border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.6rem}
.bad-card{background:rgba(239,68,68,0.12);border-left:4px solid #ef4444;border-radius:8px;padding:0.8rem 1rem;margin-bottom:0.5rem}
.hint-box{background:rgba(56,189,248,0.08);border:1px solid rgba(56,189,248,0.25);border-radius:8px;padding:0.55rem 0.85rem;font-size:0.84rem;color:#cbd5e1;margin-bottom:0.6rem}
</style><div class="lex-bar"><div style="display:flex;align-items:center;gap:1.1rem"><svg width="54" height="54" viewBox="0 0 100 100" fill="none"><polygon points="50,5 89,27.5 89,72.5 50,95 11,72.5 11,27.5" stroke="#38bdf8" stroke-width="2.5" fill="rgba(56,189,248,0.07)"/><polygon points="50,15 80,68 20,68" stroke="#a78bfa" stroke-width="1.8" fill="none"/><polygon points="50,85 80,32 20,32" stroke="#34d399" stroke-width="1.8" fill="none"/><path d="M28 50C28 40 42 40 50 50C58 60 72 60 72 50C72 40 58 40 50 50C42 60 28 60 28 50Z" stroke="#f8fafc" stroke-width="3.2" stroke-linecap="round"/><circle cx="50" cy="50" r="3.5" fill="#38bdf8"/></svg><div><div class="lex-h1">WE SEE ALL</div><div class="lex-sub">Skip the fine print — catch hidden loopholes, contradictions &amp; traps instantly.</div></div></div><div style="color:#38bdf8;font-size:0.75rem;font-weight:700;letter-spacing:1px">3•6•9 SYMMETRY • SHA-256</div></div>""", unsafe_allow_html=True)
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
        st.markdown(f'<div class="hint-box"><b>Active:</b> {"🔒 Mask PII ON" if pii_on else "👁️ Mask PII OFF"} • {"🔍 Showing Loopholes & Fixes" if reveal_details else "📋 Summary View"}</div>', unsafe_allow_html=True)
        if run_btn and raw_text.strip():
            try:
                with st.spinner("Scanning document..."):
                    clean, meta = sanitize_and_fingerprint(raw_text, mask_pii=pii_on)
                    out = auditor_app.invoke({"contract_text": clean, "playbook_rules": playbook, "retries": 0, "hallucination_errors": [], "security_metadata": meta})
                    st.session_state.last_doc = clean
                    st.session_state.result, st.session_state.good, st.session_state.tldr, st.session_state.meta = out["report"].get("findings", []), out["report"].get("good", []), out["report"].get("tldr", []), meta
            except Exception as e: st.error(f"Scan Error: {e}")
    with c2:
        res, good, tldr, meta = st.session_state.result, st.session_state.good, st.session_state.tldr, st.session_state.meta
        if res is None: st.info("👈 Follow Steps 1–3 on the left, or click **Load Sample** then **Run Audit**.")
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
                for g in good: st.markdown(f'<div class="good-card"><b style="color:#34d399">✓ {g.get("topic","Fair Clause")}</b><br><i>"{g.get("exact_quote","")}"</i><br>{g.get("benefit_summary","")}</div>', unsafe_allow_html=True)
            if reveal_details or st.checkbox("Ask AI to Reveal Hidden Loopholes & Safer Fixes", value=False):
                st.markdown("#### Hidden Loopholes & Contradictions (Red = Risky)")
                if not shown: st.success("Safe to proceed — no loopholes flagged.")
                rep = f"# WE SEE ALL Report (Date: 23/11/2026)\nRisk Index: {score}/100\n\n"
                for i in shown:
                    st.markdown(f'<div class="bad-card"><b style="color:#f87171">⚠ [{i.get("risk_level","HIGH")}] {i.get("finding_type","TRAP")} — {i.get("clause_topic","Clause")}</b><br><i>"{i.get("exact_quote","")}"</i><br>{i.get("violation_reason","")}</div>', unsafe_allow_html=True)
                    st.code(i.get("suggested_redline", ""), language="text")
                    rep += f"## {i.get('clause_topic','')}\n- Fix: {i.get('suggested_redline','')}\n\n"
                st.download_button("Export Report", rep, "WE_SEE_ALL_Report.md", use_container_width=True)
            q = st.text_input("Ask a quick question about this document:", placeholder="e.g. Can they terminate me without notice? / Is my deposit refundable?")
            if q and st.session_state.last_doc:
                with st.spinner("Checking document..."): st.success(ask_doc_question(st.session_state.last_doc, q))
with t2:
    if st.session_state.result is not None: st.bar_chart({k: sum(1 for f in st.session_state.result if f.get("risk_level") == k) for k in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]})
    else: st.info("Run an audit first.")
with t3: st.json(st.session_state.meta or {"status": "Ready", "date": "23/11/2026", "format": "DD/MM/YYYY", "storage": "Zero-Retention Memory"})
with t4: st.markdown("### WE SEE ALL — User & Button Guide\n- **Architected & Engineered by:** **WESING** | **Date:** 23/11/2026 (DD/MM/YYYY)\n\n#### How Custom Priority Checks Work\n- **Leave Blank:** Scans the entire document broadly for all fair clauses, hidden loopholes, and contradictions.\n- **Type Your Concerns:** Checks your typed priorities FIRST, then flags any other major traps.\n\n#### Button Guide\n- **Load Sample:** Loads a realistic test document.\n- **Clear Workspace:** Clears all text & results.\n- **Strict Audit vs. Work Anyway:** Strict catches every loophole; Work Anyway flags major dealbreakers only.\n- **Mask PII:** Hides Aadhaar/PAN/Email/Phone before scanning.\n- **Show Loopholes & Fixes:** Reveals red trap alerts and safer replacement wording.")
