import os, json, re, urllib.request

def _smart_llm(prompt: str) -> str:
    key = os.getenv("GROQ_API_KEY", "")
    if not key and os.path.exists(".streamlit/secrets.toml"):
        m = re.search(r"GROQ_API_KEY\s*=\s*['\"]([^'\"]+)", open(".streamlit/secrets.toml").read())
        if m: key = m.group(1)
    if key:
        for mdl in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
            try:
                body = {"model": mdl, "temperature": 0.0, "max_tokens": 1400, "messages": [{"role": "user", "content": prompt}]}
                req = urllib.request.Request("https://groq.com", data=json.dumps(body).encode(),
                    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=18) as r:
                    return json.loads(r.read())["choices"]["message"]["content"]
            except Exception:
                continue
    return "{}"
CRITIC_PROMPT = """Return ONLY valid JSON for this contract audit:
{"safety_score": 0-100, "verdict": "SAFE|CAUTION|DANGER", "bottom_line": "1 simple sentence on whether to sign",
 "whatsapp_msg": "polite 3-line WhatsApp message asking for fixes",
 "penalty_numbers": {"late_fees": 1500, "leave_cuts": 3000, "early_exit": 10000},
 "mistake_simulator": {"avg_yearly_loss": "estimated yearly loss in Rs/$", "breakdown": ["1. Late payments: ...", "2. Extra leaves: ...", "3. Early exit: ..."]},
 "findings": [{"severity": "CRITICAL|HIGH|MEDIUM", "exact_quote": "verbatim text or MISSING CLAUSE", "plain_english": "1 simple sentence",
   "why_it_hurts": "real-life impact", "pref_translation": "translate into PREFERRED_LANG (or empty if None)", "counter_email": "2-sentence fix request"}]}"""

def extract_uploaded_text(f) -> str:
    if not f: return ""
    if f.name.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(f).pages)
    return f.read().decode("utf-8", errors="ignore")

def run_adversarial_critic(text: str, pref_lang: str = "None") -> dict:
    norm = re.sub(r"\s+", " ", text).lower()
    raw = re.sub(r"<think>.*?</think>", "", _smart_llm(f"{CRITIC_PROMPT}\nPREFERRED_LANG: {pref_lang}\nCONTRACT:\n{text[:10000]}"), flags=re.S)
    m = re.search(r"\{.*\}", raw, flags=re.S)
    data = json.loads(m.group(0)) if m else {"safety_score": 50, "verdict": "CAUTION", "bottom_line": "Review carefully.", "penalty_numbers": {"late_fees": 0, "leave_cuts": 0, "early_exit": 0}, "findings": []}
    data["findings"] = [x for x in data.get("findings", []) if x.get("exact_quote", "").lower().strip() == "missing clause" or re.sub(r"\s+", " ", x.get("exact_quote", "")).lower().strip() in norm]
    return data

def build_negotiation_email(findings: list) -> str:
    items = "\n".join(f"{i}. {f.get('plain_english','')} -> {f.get('counter_email','')}" for i, f in enumerate(findings, 1))
    return f"Hi,\n\nBefore signing, could we clarify:\n{items or 'Looks balanced!'}\n\nBest regards,"

def run_personalized_simulation(text: str, habits: str, pref_lang: str = "None") -> str:
    p = f"Based ONLY on this contract and USER HABITS ({habits}), calculate exact fines, pay cuts & survival plan in easy English (plus {pref_lang} if not None)."
    return re.sub(r"<think>.*?</think>", "", _smart_llm(f"{p}\nCONTRACT:\n{text[:10000]}"), flags=re.S).strip()
