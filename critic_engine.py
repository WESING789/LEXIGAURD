import os, json, re, urllib.request

def _smart_llm(prompt: str) -> str:
    try:
        import agent
        return agent.invoke_llm(prompt)
    except Exception:
        key = os.getenv("GROQ_API_KEY", "")
        if key:
            req = urllib.request.Request("https://groq.com",
                data=json.dumps({"model": "openai/gpt-oss-120b", "temperature": 0.0,
                "messages": [{"role": "user", "content": prompt}]}).encode(),
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())["choices"]["message"]["content"]
    return "{}"
CRITIC_PROMPT = """You are LEXGUARDIAN's Devil's Advocate Critic. Catch hidden traps, contradictions, and missing protections. Return ONLY JSON:
{"safety_score": 0-100, "verdict": "SAFE|CAUTION|DANGER", "bottom_line": "1 easy English sentence on whether to sign",
 "whatsapp_msg": "polite 3-line WhatsApp message asking for fixes", "ask_before_signing": ["Question 1", "Question 2", "Question 3"],
 "mistake_simulator": {"avg_yearly_loss": "estimated average yearly loss", "breakdown": ["1. Late payments: ...", "2. Extra leaves: ...", "3. Early exit: ..."]},
 "findings": [{"severity": "CRITICAL|HIGH|MEDIUM", "exact_quote": "verbatim text or MISSING CLAUSE", "plain_english": "1 simple sentence",
   "why_it_hurts": "real-life impact", "pref_translation": "translate plain_english + why_it_hurts into PREFERRED_LANG (or empty if None)",
   "counter_email": "polite 2-sentence fix request"}]}"""

def extract_uploaded_text(f) -> str:
    if not f: return ""
    if f.name.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(p.extract_text() or "" for p in PdfReader(f).pages)
    return f.read().decode("utf-8", errors="ignore")

def run_adversarial_critic(text: str, pref_lang: str = "None") -> dict:
    norm = re.sub(r"\s+", " ", text).lower()
    raw = re.sub(r"<think>.*?</think>", "", _smart_llm(f"{CRITIC_PROMPT}\nPREFERRED_LANG: {pref_lang}\n\nCONTRACT:\n{text[:18000]}"), flags=re.S)
    m = re.search(r"\{.*\}", raw, flags=re.S)
    data = json.loads(m.group(0)) if m else {"safety_score": 50, "verdict": "CAUTION", "bottom_line": "Review carefully.", "findings": []}
    data["findings"] = [x for x in data.get("findings", []) if x.get("exact_quote", "").lower().strip() == "missing clause" or re.sub(r"\s+", " ", x.get("exact_quote", "")).lower().strip() in norm]
    return data

def build_negotiation_email(findings: list) -> str:
    items = "\n".join(f"{i}. {f.get('plain_english','')}\n   Suggested fix: {f.get('counter_email','')}" for i, f in enumerate(findings, 1))
    return f"Hi,\n\nBefore signing, could we clarify a few points?\n\n{items or 'Looks balanced!'}\n\nBest regards,"

def run_personalized_simulation(text: str, habits: str, pref_lang: str = "None") -> str:
    p = f"Devil's Advocate: Based ONLY on this contract and USER HABITS ({habits}), calculate exact personalized fines, pay cuts, deposit loss, and give a clear survival plan in easy English (plus {pref_lang} if not None)."
    return re.sub(r"<think>.*?</think>", "", _smart_llm(f"{p}\n\nCONTRACT:\n{text[:15000]}"), flags=re.S).strip()
