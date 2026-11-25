import streamlit as st, critic_engine

def inject_luxury_w_theme():
    st.markdown("""<style>
    @keyframes orbitCW { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    @keyframes orbitCCW { 0% { transform: rotate(360deg); } 100% { transform: rotate(0deg); } }
    .spin-cw { position:absolute; inset:0; transform-origin:50% 50%; animation:orbitCW 1.4s linear infinite; }
    .spin-ccw { position:absolute; inset:0; transform-origin:50% 50%; animation:orbitCCW 1.1s linear infinite; }
    .stApp { background: radial-gradient(circle at top, #0F121D 0%, #06070A 100%); color: #F1F5F9; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #00F5D4 !important; color: #00F5D4 !important; }
    .stButton>button { background: linear-gradient(135deg, #FF2A6D 0%, #9D174D 100%); color: #FFF; border: 1px solid #00F5D4; border-radius: 10px; font-weight: 700; }
    </style>""", unsafe_allow_html=True)

def dual_overlap_loader(msg: str = "LEXGUARDIAN is auditing every clause..."):
    return f"""<div style="display:flex;align-items:center;gap:16px;padding:14px 18px;border:1px solid #00F5D4;border-radius:12px;background:#090C14;margin:10px 0;">
    <div style="position:relative;width:54px;height:54px;flex-shrink:0;">
      <div class="spin-cw"><svg width="54" height="54" viewBox="0 0 100 100"><polygon points="50,5 91,27 91,73 50,95 9,73 9,27" fill="none" stroke="#00F5D4" stroke-width="5"/><ellipse cx="50" cy="50" rx="42" ry="14" fill="none" stroke="#E2E8F0" stroke-width="3"/></svg></div>
      <div class="spin-ccw"><svg width="54" height="54" viewBox="0 0 100 100"><ellipse cx="50" cy="50" rx="14" ry="42" fill="none" stroke="#FF2A6D" stroke-width="4.5"/><path d="M24 34 L38 72 L50 48 L62 72 L76 34" fill="none" stroke="#FF2A6D" stroke-width="6" stroke-linecap="round"/></svg></div>
    </div><b style="color:#F8FAFC;">{msg}</b></div>"""

def render_yinyang_loader(msg: str = "Devil's Advocate is cross-examining every clause..."):
    return f"""<div style="display:flex;align-items:center;gap:16px;padding:14px 18px;border:1px solid #FF2A6D;border-radius:12px;background:#090C14;margin:10px 0;">
    <div style="position:relative;width:54px;height:54px;flex-shrink:0;">
      <div class="spin-cw"><svg width="54" height="54" viewBox="0 0 100 100"><circle cx="50" cy="50" r="34" fill="#0B0E17" stroke="#E2E8F0" stroke-width="4"/><path d="M50 16 A34 34 0 0 1 50 84 A17 17 0 0 1 50 50 A17 17 0 0 0 50 16 Z" fill="#FF2A6D"/><circle cx="50" cy="33" r="5" fill="#0B0E17"/><circle cx="50" cy="67" r="5" fill="#E2E8F0"/></svg></div>
      <div class="spin-ccw"><svg width="54" height="54" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" fill="none" stroke="#FF2A6D" stroke-width="3.5" stroke-dasharray="28 16"/><ellipse cx="50" cy="50" rx="46" ry="15" fill="none" stroke="#00F5D4" stroke-width="2.5"/></svg></div>
    </div><b style="color:#F8FAFC;">{msg}</b></div>"""
def render_devils_advocate_suite(txt: str, pref_lang: str):
    res = st.session_state.get("da_res")
    if not res: return
    score, verdict = int(res.get("safety_score", 50)), res.get("verdict", "CAUTION")
    col = "#00F5D4" if score >= 75 else ("#F472B6" if score >= 45 else "#FF2A6D")
    st.markdown(f"<div style='border:1px solid #00F5D4;border-radius:12px;padding:14px;background:#090C14;margin:8px 0;'><b>DEVIL'S ADVOCATE REPORT:</b> <b style='color:{col};font-size:1.2rem;'>{score}/100 — {verdict}</b><p style='margin:4px 0 0 0;'>{res.get('bottom_line','')}</p></div>", unsafe_allow_html=True)
    sim = res.get("mistake_simulator", {})
    if sim:
        items = "".join(f"<li>{x}</li>" for x in sim.get("breakdown", []))
        st.markdown(f"<div style='border:1px solid #00F5D4;border-radius:12px;padding:12px;background:rgba(255,42,109,0.08);margin-bottom:8px;'><b>AVERAGE REAL-WORLD MISTAKE BILL:</b> <b style='color:#FF2A6D;'>{sim.get('avg_yearly_loss','')}</b><ul>{items}</ul></div>", unsafe_allow_html=True)
    for i, f in enumerate(res.get("findings", []), 1):
        tr = f"<div style='color:#00F5D4;margin-top:4px;'><b>[{pref_lang}]:</b> {f.get('pref_translation','')}</div>" if pref_lang != "None" and f.get("pref_translation") else ""
        st.markdown(f"<div style='border-left:4px solid #FF2A6D;padding:10px;background:#0B0F19;margin:8px 0;'><b>#{i} [{f.get('severity','HIGH')}] {f.get('plain_english','')}</b><br><small>{f.get('why_it_hurts','')}</small>{tr}<br><code>{f.get('exact_quote','')}</code></div>", unsafe_allow_html=True)
    with st.expander("1-Click Copy: Polite WhatsApp & Counter-Negotiation Email"):
        st.code(res.get("whatsapp_msg", ""), language="text")
        st.code(critic_engine.build_negotiation_email(res.get("findings", [])), language="text")
    st.markdown("<b style='color:#00F5D4;'>PERSONALIZED HABIT SIMULATOR (Adjust Your Real-Life Habits):</b>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    late, leaves, ex = c1.slider("Late payments/yr:", 0, 12, 2, key="hl"), c2.slider("Extra leaves/yr:", 0, 20, 4, key="hv"), c3.selectbox("Leave before lock-in?", ["No", "Maybe", "Yes"], key="he")
    note = st.text_input("Any specific situation?", key="hn")
    if st.button("GENERATE MY PERSONALIZED BEST PLAN", key="hb"):
        ld = st.empty(); ld.markdown(render_yinyang_loader("Simulating your personal habits..."), unsafe_allow_html=True)
        st.session_state["pers_plan"] = critic_engine.run_personalized_simulation(txt, f"Late:{late}/yr, Leaves:{leaves}/yr, Exit:{ex}. {note}", pref_lang); ld.empty()
    if st.session_state.get("pers_plan"): st.info(st.session_state["pers_plan"])

def render_risk_analytics():
    da = st.session_state.get("da_res") or {}
    good_cnt = max(1, len(st.session_state.get("good", [])))
    findings = da.get("findings", [])
    if not da and not st.session_state.get("result"):
        st.info("Run an Audit or Devil's Advocate scan in Audit Workspace first to unlock live charts.")
        return
    score = int(da.get("safety_score", 60))
    crit = sum(1 for x in findings if x.get("severity") == "CRITICAL")
    high = sum(1 for x in findings if x.get("severity") == "HIGH")
    med = sum(1 for x in findings if x.get("severity") not in ("CRITICAL", "HIGH"))
    m1, m2, m3 = st.columns(3)
    m1.metric("Overall Safety Score", f"{score}/100", da.get("verdict", "CAUTION"))
    m2.metric("Hidden Traps Found", len(findings), f"{crit} Critical")
    m3.metric("Safe Clauses Verified", good_cnt, "Protected")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Safe Clauses vs. Risk Traps (Pie Chart)")
        tot = good_cnt + max(1, len(findings))
        deg = int((good_cnt / tot) * 360)
        st.markdown(f"<div style='display:flex;align-items:center;gap:18px;padding:14px;border:1px solid #00F5D4;border-radius:12px;background:#090C14;'><div style='width:110px;height:110px;border-radius:50%;background:conic-gradient(#00F5D4 0deg {deg}deg, #FF2A6D {deg}deg 360deg);'></div><div><p style='color:#00F5D4;margin:4px 0;'><b>Safe Clauses:</b> {good_cnt} ({int(deg/3.6)}%)</p><p style='color:#FF2A6D;margin:4px 0;'><b>Risk Traps:</b> {len(findings)} ({100-int(deg/3.6)}%)</p></div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown("#### Trap Severity Breakdown (Bar Chart)")
        st.bar_chart({"Count": {"1. Critical": crit, "2. High": high, "3. Medium": med}}, color="#FF2A6D")
    pens = da.get("penalty_numbers", {"late_fees": 0, "leave_cuts": 0, "early_exit": 0})
    st.markdown("#### Estimated Financial Penalty Exposure (Bar Chart)")
    st.bar_chart({"Estimated Loss (Rs/$)": {"Late Fees": pens.get("late_fees", 0), "Leave Cuts": pens.get("leave_cuts", 0), "Early Exit Penalty": pens.get("early_exit", 0)}}, color="#00F5D4")
    st.success(f"**Plain-English Takeaway:** {da.get('bottom_line', 'Review highlighted traps before signing.')}")
