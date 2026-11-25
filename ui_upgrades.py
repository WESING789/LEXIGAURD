import streamlit as st, critic_engine

def inject_luxury_w_theme():
    st.markdown("""<style>
    .stApp { background: radial-gradient(circle at top, #0F121D 0%, #06070A 100%); color: #F1F5F9; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #00F5D4 !important; color: #00F5D4 !important; text-shadow: 0 0 10px rgba(0,245,212,0.6); }
    .stButton>button { background: linear-gradient(135deg, #FF2A6D 0%, #9D174D 100%); color: #FFF; border: 1px solid #00F5D4; border-radius: 10px; font-weight: 700; box-shadow: 0 0 14px rgba(0,245,212,0.25); }
    div[data-testid="stExpander"], .stTextArea textarea, .stTextInput input { border: 1px solid rgba(0,245,212,0.45) !important; background: #0B0E17 !important; border-radius: 10px !important; }
    </style>""", unsafe_allow_html=True)

def render_devils_advocate_suite(txt: str, pref_lang: str):
    res = st.session_state.get("da_res")
    if not res: return
    score, verdict = int(res.get("safety_score", 50)), res.get("verdict", "CAUTION")
    sc_col = "#00F5D4" if score >= 75 else ("#F472B6" if score >= 45 else "#FF2A6D")
    st.markdown(f"""<div style="border:1px solid #00F5D4;box-shadow:0 0 15px rgba(0,245,212,0.18);border-radius:12px;padding:16px;background:#090C14;margin:10px 0;">
    <b style="color:#E2E8F0;">DEVIL'S ADVOCATE SCORE:</b> <b style="color:{sc_col};font-size:1.25rem;">{score}/100 — {verdict}</b>
    <p style="color:#CBD5E1;margin:6px 0 0 0;">{res.get('bottom_line','')}</p></div>""", unsafe_allow_html=True)
    sim = res.get("mistake_simulator", {})
    if sim:
        items = "".join(f"<li style='color:#E2E8F0;'>{x}</li>" for x in sim.get("breakdown", []))
        st.markdown(f"""<div style="border:1px solid rgba(0,245,212,0.5);border-radius:12px;padding:14px;background:rgba(255,42,109,0.07);margin-bottom:12px;">
        <b style="color:#F472B6;">REAL-WORLD MISTAKE SIMULATOR (Average Yearly Loss):</b> <b style="color:#FF2A6D;">{sim.get('avg_yearly_loss','Check clauses')}</b>
        <ul style="margin:6px 0 0 18px;">{items}</ul></div>""", unsafe_allow_html=True)
    for i, f in enumerate(res.get("findings", []), 1):
        extra = f"<div style='margin-top:6px;padding:6px 10px;border:1px solid rgba(0,245,212,0.4);border-radius:6px;color:#00F5D4;'><b>[{pref_lang}]:</b> {f.get('pref_translation','')}</div>" if pref_lang != "None" and f.get("pref_translation") else ""
        st.markdown(f"""<div style="border:1px solid rgba(0,245,212,0.35);border-left:4px solid #FF2A6D;padding:12px;background:#0B0F19;border-radius:8px;margin-bottom:10px;">
        <b style="color:#F472B6;">#{i} [{f.get('severity','HIGH')}] Simple Breakdown:</b> <span style="color:#F8FAFC;">{f.get('plain_english','')}</span><br>
        <small style="color:#94A3B8;"><b>Real-Life Impact:</b> {f.get('why_it_hurts','')}</small>{extra}<br><code style="color:#00F5D4;">"{f.get('exact_quote','')}"</code></div>""", unsafe_allow_html=True)
    with st.expander("1-Click Copy: Polite WhatsApp & Counter-Negotiation Email"):
        st.code(res.get("whatsapp_msg", ""), language="text")
        st.code(critic_engine.build_negotiation_email(res.get("findings", [])), language="text")
    st.markdown("<b style='color:#00F5D4;'>TELL US YOUR REAL-LIFE HABITS — GET A PERSONALIZED RISK PLAN:</b>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    late, leaves, ex = c1.slider("Late payments/yr:", 0, 12, 2, key="hab_late"), c2.slider("Extra leaves/yr:", 0, 20, 4, key="hab_leaves"), c3.selectbox("Leave before lock-in?", ["No", "Maybe", "Yes"], key="hab_exit")
    note = st.text_input("Any specific situation? (e.g. 'May relocate in 6 months'):", key="hab_note")
    if st.button("GENERATE MY PERSONALIZED BEST PLAN", key="hab_go"):
        with st.spinner("Calculating your exact personalized risk..."):
            st.session_state["pers_plan"] = critic_engine.run_personalized_simulation(txt, f"Late: {late}/yr, Leaves: {leaves}/yr, Early exit: {ex}. {note}", pref_lang)
    if st.session_state.get("pers_plan"): st.info(st.session_state["pers_plan"])

def render_yinyang_loader(msg: str = "Devil's Advocate is cross-examining every clause..."):
    return f"""<style>@keyframes yySpin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}</style>
    <div style="display:flex;align-items:center;gap:14px;padding:14px 18px;border:1px solid rgba(0,245,212,0.45);border-radius:12px;background:#090C14;margin:10px 0;box-shadow:0 0 18px rgba(255,42,109,0.2);">
      <svg width="38" height="38" viewBox="0 0 100 100" style="animation:yySpin 1.1s linear infinite;">
        <circle cx="50" cy="50" r="46" fill="#0B0E17" stroke="#E2E8F0" stroke-width="4"/>
        <path d="M50 4 A46 46 0 0 1 50 96 A23 23 0 0 1 50 50 A23 23 0 0 0 50 4 Z" fill="#FF2A6D"/>
        <circle cx="50" cy="27" r="7" fill="#0B0E17"/><circle cx="50" cy="73" r="7" fill="#E2E8F0"/>
      </svg>
      <span style="color:#F1F5F9;font-weight:700;letter-spacing:0.5px;">{msg}</span></div>"""

def dual_overlap_loader(msg: str = "LEXGUARDIAN is auditing every clause..."):
    return f"""<div style="display:flex;align-items:center;gap:16px;padding:16px 20px;border:1px solid #00F5D4;border-radius:14px;background:#090C14;margin:12px 0;box-shadow:0 0 22px rgba(0,245,212,0.22);">
      <div style="position:relative;width:48px;height:48px;flex-shrink:0;">
        <svg width="48" height="48" viewBox="0 0 100 100" style="position:absolute;top:0;left:0;animation:spinCW 1.6s linear infinite;mix-blend-mode:screen;">
          <polygon points="50,5 92,28 92,72 50,95 8,72 8,28" fill="none" stroke="#00F5D4" stroke-width="5"/>
          <ellipse cx="50" cy="50" rx="40" ry="16" fill="none" stroke="#E2E8F0" stroke-width="3"/>
        </svg>
        <svg width="48" height="48" viewBox="0 0 100 100" style="position:absolute;top:0;left:0;animation:spinCCW 1.2s linear infinite;mix-blend-mode:screen;">
          <ellipse cx="50" cy="50" rx="16" ry="40" fill="none" stroke="#FF2A6D" stroke-width="4"/>
          <path d="M24 34 L38 72 L50 48 L62 72 L76 34" fill="none" stroke="#F472B6" stroke-width="5" stroke-linecap="round"/>
        </svg>
      </div><span style="color:#F8FAFC;font-weight:700;letter-spacing:0.6px;">{msg}</span></div>"""

def render_yinyang_loader(msg: str = "Devil's Advocate is cross-examining every clause..."):
    return f"""<div style="display:flex;align-items:center;gap:16px;padding:16px 20px;border:1px solid #FF2A6D;border-radius:14px;background:#090C14;margin:12px 0;box-shadow:0 0 22px rgba(255,42,109,0.28);">
      <div style="position:relative;width:46px;height:46px;flex-shrink:0;">
        <svg width="46" height="46" viewBox="0 0 100 100" style="position:absolute;top:0;left:0;animation:spinCW 1.1s linear infinite;">
          <circle cx="50" cy="50" r="42" fill="#0B0E17" stroke="#E2E8F0" stroke-width="4"/>
          <path d="M50 8 A42 42 0 0 1 50 92 A21 21 0 0 1 50 50 A21 21 0 0 0 50 8 Z" fill="#FF2A6D"/>
          <circle cx="50" cy="29" r="6" fill="#0B0E17"/><circle cx="50" cy="71" r="6" fill="#E2E8F0"/>
        </svg>
        <svg width="46" height="46" viewBox="0 0 100 100" style="position:absolute;top:0;left:0;animation:spinCCW 1.8s linear infinite;">
          <circle cx="50" cy="50" r="47" fill="none" stroke="#00F5D4" stroke-width="2.5" stroke-dasharray="28 16"/>
        </svg>
      </div><span style="color:#F8FAFC;font-weight:700;letter-spacing:0.6px;">{msg}</span></div>"""

def render_devils_advocate_suite(txt: str, pref_lang: str):
    res = st.session_state.get("da_res")
    if not res: return
    score, verdict = int(res.get("safety_score", 50)), res.get("verdict", "CAUTION")
    sc_col = "#00F5D4" if score >= 75 else ("#F472B6" if score >= 45 else "#FF2A6D")
    st.markdown(f"""<div style="border:1px solid #00F5D4;box-shadow:0 0 15px rgba(0,245,212,0.18);border-radius:12px;padding:16px;background:#090C14;margin:10px 0;">
    <b style="color:#E2E8F0;">DEVIL'S ADVOCATE SCORE:</b> <b style="color:{sc_col};font-size:1.25rem;">{score}/100 — {verdict}</b>
    <p style="color:#CBD5E1;margin:6px 0 0 0;">{res.get('bottom_line','')}</p></div>""", unsafe_allow_html=True)
    sim = res.get("mistake_simulator", {})
    if sim:
        items = "".join(f"<li style='color:#E2E8F0;'>{x}</li>" for x in sim.get("breakdown", []))
        st.markdown(f"""<div style="border:1px solid rgba(0,245,212,0.5);border-radius:12px;padding:14px;background:rgba(255,42,109,0.07);margin-bottom:12px;">
        <b style="color:#F472B6;">REAL-WORLD MISTAKE SIMULATOR (Average Yearly Loss):</b> <b style="color:#FF2A6D;">{sim.get('avg_yearly_loss','Check clauses')}</b>
        <ul style="margin:6px 0 0 18px;">{items}</ul></div>""", unsafe_allow_html=True)
    for i, f in enumerate(res.get("findings", []), 1):
        extra = f"<div style='margin-top:6px;padding:6px 10px;border:1px solid rgba(0,245,212,0.4);border-radius:6px;color:#00F5D4;'><b>[{pref_lang}]:</b> {f.get('pref_translation','')}</div>" if pref_lang != "None" and f.get("pref_translation") else ""
        st.markdown(f"""<div style="border:1px solid rgba(0,245,212,0.35);border-left:4px solid #FF2A6D;padding:12px;background:#0B0F19;border-radius:8px;margin-bottom:10px;">
        <b style="color:#F472B6;">#{i} [{f.get('severity','HIGH')}] Simple Breakdown:</b> <span style="color:#F8FAFC;">{f.get('plain_english','')}</span><br>
        <small style="color:#94A3B8;"><b>Real-Life Impact:</b> {f.get('why_it_hurts','')}</small>{extra}<br><code style="color:#00F5D4;">"{f.get('exact_quote','')}"</code></div>""", unsafe_allow_html=True)
    with st.expander("1-Click Copy: Polite WhatsApp & Counter-Negotiation Email"):
        st.code(res.get("whatsapp_msg", ""), language="text")
        st.code(critic_engine.build_negotiation_email(res.get("findings", [])), language="text")
    st.markdown("<b style='color:#00F5D4;'>TELL US YOUR REAL-LIFE HABITS — GET A PERSONALIZED RISK PLAN:</b>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    late, leaves, ex = c1.slider("Late payments/yr:", 0, 12, 2, key="hab_late"), c2.slider("Extra leaves/yr:", 0, 20, 4, key="hab_leaves"), c3.selectbox("Leave before lock-in?", ["No", "Maybe", "Yes"], key="hab_exit")
    note = st.text_input("Any specific situation? (e.g. 'May relocate in 6 months'):", key="hab_note")
    if st.button("GENERATE MY PERSONALIZED BEST PLAN", key="hab_go"):
        _ld2 = st.empty(); _ld2.markdown(render_yinyang_loader("Simulating your personal habits against every penalty..."), unsafe_allow_html=True)
        st.session_state["pers_plan"] = critic_engine.run_personalized_simulation(txt, f"Late: {late}/yr, Leaves: {leaves}/yr, Early exit: {ex}. {note}", pref_lang); _ld2.empty()
    if st.session_state.get("pers_plan"): st.info(st.session_state["pers_plan"])
