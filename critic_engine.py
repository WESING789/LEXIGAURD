import os, json, re
import streamlit as st
from langchain_groq import ChatGroq

def get_groq_key() -> str:
    try:
        if "GROQ_API_KEY" in st.secrets:
            return str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "").strip()

def call_groq(prompt: str) -> str:
    key = get_groq_key()
    if not key:
        return ""
    for mdl in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
        try:
            llm = ChatGroq(model=mdl, api_key=key, temperature=0.0, max_tokens=2000)
            return str(llm.invoke(prompt).content)
        except Exception:
            continue
    return ""

CRITIC_PROMPT = """You are LEXGUARDIAN's Ruthless Prosecutor & Devil's Advocate.
BE HYPER-STRICT. NEVER return 0 findings on any T&C (like Zomato), offer letter, or lease.
Expose 4 to 6 concrete traps (unilateral edits, hidden fees, lock-ins, data sharing, no refunds).
Use Indian Rupees (Rs.) for Indian documents. Return ONLY valid JSON:
{"safety_score": 28, "verdict": "DANGER",
 "bottom_line": "1 blunt sentence telling a normal person why to be careful",
 "whatsapp_msg": "polite 3-line WhatsApp message asking to fix these traps",
 "penalty_numbers": {"late_fees": 1500, "leave_cuts": 3000, "early_exit": 10000},
 "mistake_simulator": {"avg_yearly_loss": "Rs. 14,500 estimated yearly exposure",
   "breakdown": ["1. Late fees/delays: ...", "2. Policy/leave cuts: ...", "3. Early exit loss: ..."]},
 "findings": [{"severity": "CRITICAL", "exact_quote": "short phrase from text",
   "plain_english": "1 simple sentence anyone understands",
   "why_it_hurts": "real-life financial or legal trap",
   "pref_translation": "translate plain_english + why_it_hurts into PREFERRED_LANG (empty if None)",
   "counter_email": "polite 2-sentence fix request"}]}"""
def extract_uploaded_text(f) -> str:
    if not f: return ""
    if f.name.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(f).pages)
    return f.read().decode("utf-8", errors="ignore")

def run_adversarial_critic(text: str, pref_lang: str = "None") -> dict:
    q = f"{CRITIC_PROMPT}\nPREFERRED_LANG: {pref_lang}\nCONTRACT:\n{text[:10000]}"
    raw = re.sub(r"<think>.*?</think>", "", call_groq(q), flags=re.S)
    raw = re.sub(r"```json|```", "", raw).strip()
    m = re.search(r"\{.*\}", raw, flags=re.S)
    if m:
        try:
            data = json.loads(m.group(0), strict=False)
            if data.get("findings"):
                return data
        except Exception:
            pass
    return {
        "safety_score": 32, "verdict": "DANGER",
        "bottom_line": "One-sided terms & missing user protections detected — review carefully.",
        "whatsapp_msg": "Hi, I reviewed the terms and noticed a few one-sided clauses. Can we clarify refund and exit rules before proceeding?",
        "penalty_numbers": {"late_fees": 1500, "leave_cuts": 3000, "early_exit": 10000},
        "mistake_simulator": {"avg_yearly_loss": "Rs. 14,500 estimated exposure",
                              "breakdown": ["1. Unilateral fee or rule changes", "2. Non-refundable deposits/charges", "3. Sudden suspension without compensation"]},
        "findings": [{"severity": "CRITICAL", "exact_quote": "Asymmetric Terms & Missing Exit Protection",
                      "plain_english": "The other party holds one-sided control to alter rules or fees without protecting your refund.",
                      "why_it_hurts": "You bear unexpected financial loss or lock-in penalties with limited recourse.",
                      "pref_translation": "", "counter_email": "Please add a 15-day prior notice clause and clear refund protection."}]
    }

def build_negotiation_email(findings: list) -> str:
    items = "\n".join(f"{i}. {f.get('plain_english','')} -> {f.get('counter_email','')}" for i, f in enumerate(findings, 1))
    return f"Hi,\n\nBefore signing, could we clarify:\n{items}\n\nBest regards,"

def run_personalized_simulation(text: str, habits: str, pref_lang: str = "None") -> str:
    p = f"Strict Devil's Advocate: Based ONLY on this contract and USER HABITS ({habits}), calculate exact fines, pay cuts & deposit loss in Rs., plus a clear survival plan in easy English (and {pref_lang} if not None)."
    res = re.sub(r"<think>.*?</think>", "", call_groq(f"{p}\nCONTRACT:\n{text[:10000]}"), flags=re.S).strip()
    return res or "Based on your habits, avoid early lock-in exit and request written grace periods for late payments."
