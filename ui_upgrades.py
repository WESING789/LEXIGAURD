import streamlit as st, critic_engine

def inject_luxury_w_theme():
    st.markdown("""<style>
    @keyframes spinCW { to { transform: rotate(360deg); } }
    @keyframes spinCCW { to { transform: rotate(-360deg); } }
    .stApp { background: radial-gradient(circle at top, #0F121D 0%, #06070A 100%); color: #F1F5F9; }
    .stTabs [aria-selected="true"] { border-bottom: 2px solid #00F5D4 !important; color: #00F5D4 !important; }
    .stButton>button { background: linear-gradient(135deg, #FF2A6D, #9D174D); color: #FFF; border: 1px solid #00F5D4; border-radius: 10px; font-weight: 700; }
    </style>""", unsafe_allow_html=True)

def dual_overlap_loader(msg: str = "Auditing every clause..."):
    return f"""<div style="display:flex;align-items:center;gap:14px;padding:12px;border:1px solid #00F5D4;border-radius:12px;background:#090C14;">
    <div style="position:relative;width:44px;height:44px;"><svg width="44" height="44" viewBox="0 0 100 100" style="position:absolute;animation:spinCW 1.4s linear infinite;">
    <polygon points="50,5 92,28 92,72 50,95 8,72 8,28" fill="none" stroke="#00F5D4" stroke-width="5"/></svg>
    <svg width="44" height="44" viewBox="0 0 100 100" style="position:absolute;animation:spinCCW 1.1s linear infinite;">
    <path d="M24 34 L38 72 L50 48 L62 72 L76 34" fill="none" stroke="#FF2A6D" stroke-width="6"/></svg></div><b>{msg}</b></div>"""

def render_yinyang_loader(msg: str = "Devil's Advocate is cross-examining..."):
    return f"""<div style="display:flex;align-items:center;gap:14px;padding:12px;border:1px solid #FF2A6D;border-radius:12px;background:#090C14;">
    <div style="position:relative;width:44px;height:44px;"><svg width="44" height="44" viewBox="0 0 100 100" style="position:absolute;animation:spinCW 1s linear infinite;">
    <circle cx="50" cy="50" r="41" fill="#0B0E17" stroke="#E2E8F0" stroke-width="4"/><path d="M50 9 A41 41 0 0 1 50 91 A20.5 20.5 0 0 1 50 50 A20.5 20.5 0 0 0 50 9 Z" fill="#FF2A6D"/>
    <circle cx="50" cy="29.5" r="6" fill="#0B0E17"/><circle cx="50" cy="70.5" r="6" fill="#E2E8F0"/></svg>
    <svg width="44" height="44" viewBox="0 0 100 100" style="position:absolute;animation:spinCCW 1.6s linear infinite;">
    <circle cx="50" cy="50" r="47" fill="none" stroke="#00F5D4" stroke-width="2.5" stroke-dasharray="26 14"/></svg></div><b>{msg}</b></div>"""
def render_devils_advocate_suite(txt: str, pref_lang: str):
    res = st.session_state.get("da_res")
    if not res: return
    score, verdict = int(res.get("safety_score", 50)), res.get("verdict", "CAUTION")
    col = "#00F5D4" if score >= 75 else ("#F472B6" if score >= 45 else "#FF2A6D")
    st.markdown(f"<div style='border:1px solid #00F5D4;border-radius:12px;padding:14px;background:#090C14;margin:8px 0;'><b>DEVIL'S ADVOCATE:</b> <b style='color:{col};'>{score}/100 ({verdict})</b><p>{res.get('bottom_line','')}</p></div>", unsafe_allow_html=True)
    sim = res.get("mistake_simulator", {})
    if sim:
        items = "".join(f"<li>{x}</li>" for x in sim.get("breakdown", []))
        st.markdown(f"<div style='border:1px solid #00F5D4;border-radius:12px;padding:12px;background:rgba(255,42,109,0.08);'><b>MISTAKE SIMULATOR:</b> <b style='color:#FF2A6D;'>{sim.get('avg_yearly_loss','')}</b><ul>{items}</ul></div>", unsafe_allow_html=True)
    for i, f in enumerate(res.get("findings", []), 1):
        tr = f"<div style='color:#00F5D4;margin-top:4px;'><b>[{pref_lang}]:</b> {f.get('pref_translation','')}</div>" if pref_lang != "None" and f.get("pref_translation") else ""
        st.markdown(f"<div style='border-left:4px solid #FF2A6D;padding:10px;background:#0B0F19;margin:8px 0;'><b>#{i} {f.get('plain_english','')}</b><br><small>{f.get('why_it_hurts','')}</small>{tr}<br><code>{f.get('exact_quote','')}</code></div>", unsafe_allow_html=True)
    with st.expander("1-Click WhatsApp & Email Replies"):
        st.code(res.get("whatsapp_msg", ""), language="text")
        st.code(critic_engine.build_negotiation_email(res.get("findings", [])), language="text")
    c1, c2, c3 = st.columns(3)
    late, leaves, ex = c1.slider("Late/yr:", 0, 12, 2), c2.slider("Leaves/yr:", 0, 20, 4), c3.selectbox("Early exit?", ["No", "Maybe", "Yes"])
    note = st.text_input("Specific situation:")
    if st.button("GENERATE MY PERSONALIZED BEST PLAN"):
        ld = st.empty(); ld.markdown(render_yinyang_loader("Simulating your habits..."), unsafe_allow_html=True)
        st.session_state["pers_plan"] = critic_engine.run_personalized_simulation(txt, f"Late:{late}, Leaves:{leaves}, Exit:{ex}. {note}", pref_lang); ld.empty()
    if st.session_state.get("pers_plan"): st.info(st.session_state["pers_plan"])
