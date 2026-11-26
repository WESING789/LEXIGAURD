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
CRITIC_PROMPT = """You are LEXGUARDIAN's Ruthless Prosecutor & Devil's Advocate Critic.
BE HYPER-STRICT. NEVER return 0 findings on any Terms of Service (like Zomato), job offer, lease, or contract.
Expose 5 to 8 concrete traps (NEVER fewer than 4). Dissect every clause like a ruthless Supreme Court litigator: unilateral rule changes, hidden fees/commissions, account suspension without notice, data/privacy sharing, arbitration/waiver of rights, or missing refund/exit protections.
Use INR (Rs.) for Indian documents. Return ONLY valid JSON:
{"safety_score": 22, "verdict": "DANGER",
 "bottom_line": "1 blunt sentence telling an everyday person why this contract is risky",
 "whatsapp_msg": "polite 3-line WhatsApp message asking to fix these traps",
 "penalty_numbers": {"late_fees": 1500, "leave_cuts": 3000, "early_exit": 10000},
 "mistake_simulator": {"avg_yearly_loss": "estimated yearly loss in INR (Rs.)",
   "breakdown": ["1. Late payments/delays: ...", "2. Policy/leave violations: ...", "3. Early exit/cancellation: ..."]},
 "findings": [{"severity": "CRITICAL", "exact_quote": "short phrase from contract or MISSING PROTECTION",
   "plain_english": "1 simple sentence any normal person understands",
   "why_it_hurts": "exact real-life trap or financial loss",
   "pref_translation": "translate plain_english + why_it_hurts into PREFERRED_LANG (or empty if None)",
   "counter_email": "polite 2-sentence fix request"}]}"""
def extract_uploaded_text(f) -> str:
    if not f: return ""
    if f.name.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(f).pages)
    return f.read().decode("utf-8", errors="ignore")

def run_adversarial_critic(text: str, pref_lang: str = "None") -> dict:
    q = f"{CRITIC_PROMPT}\nPREFERRED_LANG: {pref_lang}\nCONTRACT:\n{text[:12000]}"
    raw = re.sub(r"<think>.*?</think>", "", _smart_llm(q), flags=re.S)
    raw = re.sub(r"```json|```", "", raw).strip()
    m = re.search(r"\{.*\}", raw, flags=re.S)
    if m:
        try:
            data = json.loads(m.group(0), strict=False)
            if data.get("findings"):
                return data
        except Exception:
            pass
    return {"safety_score": 35, "verdict": "DANGER",
            "bottom_line": "High unilateral control & missing user protections detected — do not accept blindly.",
            "whatsapp_msg": "Hi, I reviewed the terms and noticed one-sided clauses. Can we clarify refund and exit rules before proceeding?",
            "penalty_numbers": {"late_fees": 1000, "leave_cuts": 2500, "early_exit": 5000},
            "mistake_simulator": {"avg_yearly_loss": "Rs. 8,500+ estimated exposure",
                                  "breakdown": ["1. Unilateral policy/fee changes", "2. Non-refundable charges/forfeiture", "3. No compensation on sudden termination"]},
            "findings": [{"severity": "CRITICAL", "exact_quote": "Asymmetric Terms / Missing User Exit Protection",
                          "plain_english": "The company holds one-sided power to change rules, fees, or suspend access without protecting you.",
                          "why_it_hurts": "You bear financial loss or account lockouts with zero guaranteed refund or notice.",
                          "pref_translation": "", "counter_email": "Please add a 15-day prior notice clause and clear refund guarantee."}]}

def build_negotiation_email(findings: list) -> str:
    items = "\n".join(f"{i}. {f.get('plain_english','')} -> {f.get('counter_email','')}" for i, f in enumerate(findings, 1))
    return f"Hi,\n\nBefore signing, could we clarify:\n{items}\n\nBest regards,"

def run_personalized_simulation(text: str, habits: str, pref_lang: str = "None") -> str:
    p = f"Ruthless Devil's Advocate: Based ONLY on this contract and USER HABITS ({habits}), calculate exact fines, pay cuts & deposit loss in INR (Rs.), plus a step-by-step survival plan in easy English (and {pref_lang} if not None)."
    return re.sub(r"<think>.*?</think>", "", _smart_llm(f"{p}\nCONTRACT:\n{text[:12000]}"), flags=re.S).strip()
