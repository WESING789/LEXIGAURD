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
