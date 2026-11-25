import os, json, re, urllib.request
import streamlit as st

def _get_key() -> str:
    try:
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "")

def _smart_llm(prompt: str) -> str:
    key = _get_key()
    if key:
        for mdl in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                body = {"model": mdl, "temperature": 0.0, "max_tokens": 1600, "messages": [{"role": "user", "content": prompt}]}
                hdrs = {"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
                req = urllib.request.Request("https://groq.com", data=json.dumps(body).encode(), headers=hdrs)
                with urllib.request.urlopen(req, timeout=22) as r:
                    return json.loads(r.read().decode())["choices"]["message"]["content"]
            except Exception:
                continue
    try:
        import agent
        return agent.invoke_llm(prompt)
    except Exception as e:
        return json.dumps({"safety_score": 25, "verdict": "DANGER", "bottom_line": f"API Notice: {e}", "findings": []})
CRITIC_PROMPT = """You are LEXGUARDIAN's Ruthless Devil's Advocate Legal Critic. Be STRICT. Never ignore fine print, asymmetric rules, bonds, deposit forfeitures, unilateral edits, or missing refund/exit rights. Even if a contract looks friendly, expose EVERY hidden trap.
Return ONLY valid JSON:
{"safety_score": 25, "verdict": "DANGER", "bottom_line": "1 blunt sentence telling an everyday person why to be careful",
 "whatsapp_msg": "polite 3-line WhatsApp message asking to fix the traps",
 "penalty_numbers": {"late_fees": 1500, "leave_cuts": 3000, "early_exit": 10000},
 "mistake_simulator": {"avg_yearly_loss": "estimated yearly loss in Rs/$", "breakdown": ["1. Late payments: ...", "2. Extra leaves: ...", "3. Early exit: ..."]},
 "findings": [{"severity": "CRITICAL", "exact_quote": "verbatim phrase from text or MISSING CLAUSE", "plain_english": "1 simple sentence",
   "why_it_hurts": "how the other party can weaponize this", "pref_translation": "translate into PREFERRED_LANG (or empty if None)", "counter_email": "2-sentence fix request"}]}"""

def extract_uploaded_text(f) -> str:
    if not f: return ""
    if f.name.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(f).pages)
    return f.read().decode("utf-8", errors="ignore")

def run_adversarial_critic(text: str, pref_lang: str = "None") -> dict:
    raw = re.sub(r"<think>.*?</think>", "", _smart_llm(f"{CRITIC_PROMPT}\nPREFERRED_LANG: {pref_lang}\nCONTRACT:\n{text[:12000]}"), flags=re.S)
    m = re.search(r"\{.*\}", raw, flags=re.S)
    if not m:
        return {"safety_score": 40, "verdict": "CAUTION", "bottom_line": "Strict scan incomplete — please retry.", "findings": []}
    return json.loads(m.group(0))

def build_negotiation_email(findings: list) -> str:
    items = "\n".join(f"{i}. {f.get('plain_english','')} -> {f.get('counter_email','')}" for i, f in enumerate(findings, 1))
    return f"Hi,\n\nBefore signing, could we clarify:\n{items or 'Looks balanced!'}\n\nBest regards,"

def run_personalized_simulation(text: str, habits: str, pref_lang: str = "None") -> str:
    p = f"Strict Devil's Advocate: Based ONLY on this contract and USER HABITS ({habits}), calculate exact fines, pay cuts & deposit loss, and give a clear survival plan in easy English (plus {pref_lang} if not None)."
    return re.sub(r"<think>.*?</think>", "", _smart_llm(f"{p}\nCONTRACT:\n{text[:12000]}"), flags=re.S).strip()
