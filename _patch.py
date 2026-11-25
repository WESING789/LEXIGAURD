import re, os
w_svg = '<svg width="24" height="24" viewBox="0 0 100 100" fill="none" style="vertical-align:middle;margin:0 4px;"><path d="M10 22 L28 84 L50 42 L72 84 L90 22 L76 22 L66 58 L50 28 L34 58 L24 22 Z" fill="url(#plat)" stroke="#00F5D4" stroke-width="3"/><defs><linearGradient id="plat" x1="0" y1="0" x2="100" y2="100"><stop offset="0%" stop-color="#FFF"/><stop offset="100%" stop-color="#94A3B8"/></linearGradient></defs></svg>'
s = open("app.py").read()
for g in ["#D4AF37", "#d4af37", "#C5A059", "#c5a059", "#E5C158", "#F5D061", "#FFD700"]:
    s = s.replace(g, "#FF2A6D")
s = re.sub(r"(?i)sym+et+e?ry", w_svg, s)
s = s.replace("t1, t2, t3, t4 =", "ui_upgrades.inject_luxury_w_theme()\nt1, t2, t3, t4 =")
s = re.sub(r"^(\s*)with st\.spinner\(([^)]+)\):", r"\1_mld = st.empty()\n\1_mld.markdown(ui_upgrades.dual_overlap_loader(\2), unsafe_allow_html=True)\n\1if True:", s, flags=re.M)
da = '''
    st.markdown("---")
    st.markdown("### <span style='color:#00F5D4;'>DEVIL'S ADVOCATE — RUTHLESS CONTRACT CRITIC</span>", unsafe_allow_html=True)
    _u1, _u2 = st.columns(2)
    _pdf, _paste = _u1.file_uploader("Upload PDF or TXT:", type=["pdf", "txt"], key="da_pdf"), _u2.text_area("Or Paste Contract Text:", height=110, key="da_in")
    _lang = st.selectbox("Extra Language Block (Optional):", ["None", "Hinglish", "Hindi", "Tamil", "Marathi", "Bengali", "Spanish"], key="da_lang")
    _txt = (critic_engine.extract_uploaded_text(_pdf) if _pdf else "") or _paste
    if st.button("UNLEASH DEVIL'S ADVOCATE", key="da_go") and _txt.strip():
        _ld = st.empty(); _ld.markdown(ui_upgrades.render_yinyang_loader(), unsafe_allow_html=True)
        st.session_state["da_res"] = critic_engine.run_adversarial_critic(_txt, pref_lang=_lang); st.session_state["pers_plan"] = ""; _ld.empty()
    ui_upgrades.render_devils_advocate_suite(_txt, _lang)
with t2:'''
open("app.py", "w").write("import critic_engine, ui_upgrades\n" + s.replace("with t2:", da, 1))
if os.path.exists("head.html"): open("head.html", "w").write(re.sub(r"(?i)sym+et+e?ry", w_svg, open("head.html").read()))
