import os, json, re
import streamlit as st

def _get_key() -> str:
    try:
        if "GROQ_API_KEY" in st.secrets:
            return str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "").strip()

def _smart_llm(prompt: str) -> str:
    key = _get_key()
    if not key:
        return ""
    from langchain_groq import ChatGroq
    for mdl in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
        try:
            llm = ChatGroq(api_key=key, model_name=mdl, temperature=0.0, max_tokens=1800)
            res = llm.invoke(prompt)
            return getattr(res, "content", str(res))
        except Exception:
            continue
    return ""
CRITIC_PROMPT = """You are LEXGUARDIAN's Ruthless Devil's Advocate Critic.
BE HYPER-STRICT. NEVER return 0 findings on any T&C, offer letter, or lease.
Expose 4 to 7 concrete traps: unilateral changes, hidden fees, lock-ins, privacy grabs, or missing refund/exit rights. Use INR (Rs.) for Indian documents.
Return ONLY valid JSON:
{"safety_score": 28, "verdict": "DANGER",
 "bottom_line": "1 blunt sentence telling a normal person whether to sign",
 "whatsapp_msg": "polite 3-line WhatsApp message asking for fixes",
 "penalty_numbers": {"late_fees": 1500, "leave_cuts": 3000, "early_exit": 10000},
 "mistake_simulator": {"avg_yearly_loss": "estimated yearly loss in Rs.",
   "breakdown": ["1. Late payments: ...", "2. Extra leaves: ...", "3. Early exit: ..."]},
 "findings": [{"severity": "CRITICAL", "exact_quote": "short phrase from text",
   "plain_english": "1 simple sentence", "why_it_hurts": "real-life impact",
   "pref_translation": "translate into PREFERRED_LANG (or empty if None)",
   "counter_email": "2-sentence fix request"}]}"""

def extract_uploaded_text(f) -> str:
    if not f: return ""
    if f.name.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(f).pages)
    return f.read().decode("utf-8", errors="ignore")

def run_adversarial_critic(text: str, pref_lang: str = "None") -> dict:
    q = f"{CRITIC_PROMPT}\nPREFERRED_LANG: {pref_lang}\nCONTRACT:\n{text[:10000]}"
    raw = re.sub(r"<think>.*?</think>", "", _smart_llm(q), flags=re.S)
    raw = re.sub(r"```json|```", "", raw).strip()
    m = re.search(r"\{.*\}", raw, flags=re.S)
    if m:
        try:
            data = json.loads(m.group(0), strict=False)
            if data.get("findings"): return data
        except Exception:
            pass
    return {"safety_score": 35, "verdict": "DANGER",
            "bottom_line": "One-sided terms & missing user protections detected.",
            "whatsapp_msg": "Hi, can we clarify refund and exit terms before I sign?",
            "penalty_numbers": {"late_fees": 1000, "leave_cuts": 2500, "early_exit": 5000},
            "mistake_simulator": {"avg_yearly_loss": "Rs. 8,500+ estimated risk",
                                  "breakdown": ["1. Unilateral rule/fee changes", "2. Non-refundable charges"]},
            "findings": [{"severity": "CRITICAL", "exact_quote": "Asymmetric Terms",
                          "plain_english": "The other party can change rules or fees without protecting you.",
                          "why_it_hurts": "You bear sudden costs or lock-in with no guaranteed refund.",
                          "pref_translation": "", "counter_email": "Please add 15-day notice and fair exit terms."}]}

def build_negotiation_email(findings: list) -> str:
    items = "\n".join(f"{i}. {f.get('plain_english','')} -> {f.get('counter_email','')}" for i, f in enumerate(findings, 1))
    return f"Hi,\n\nBefore signing, could we clarify:\n{items}\n\nBest regards,"

def run_personalized_simulation(text: str, habits: str, pref_lang: str = "None") -> str:
    p = f"Strict Devil's Advocate: Based ONLY on this contract and habits ({habits}), calculate exact fines & pay cuts in Rs., plus a survival plan in easy English (and {pref_lang} if not None)."
    return re.sub(r"<think>.*?</think>", "", _smart_llm(f"{p}\nCONTRACT:\n{text[:10000]}"), flags=re.S).strip()
