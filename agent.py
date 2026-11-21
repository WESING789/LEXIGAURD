import os, json, hashlib, re
from datetime import datetime, timezone
from typing import List, TypedDict
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

class AuditState(TypedDict):
    contract_text: str
    playbook_rules: str
    report: dict
    hallucination_errors: List[str]
    security_metadata: dict
    retries: int

def get_llm():
    key = os.getenv("GOOGLE_API_KEY", "").strip()
    if key:
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=key, temperature=0)
    return ChatOllama(model="qwen2.5:7b", temperature=0)

def sanitize_and_fingerprint(text: str, mask_pii: bool = True):
    h = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
    m, clean = 0, text
    if mask_pii:
        for pat, rep in [(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b","[REDACTED-AADHAAR]"),(r"\b[A-Z]{5}\d{4}[A-Z]\b","[REDACTED-PAN]"),(r"\b[\w\.-]+@[\w\.-]+\.\w+\b","[REDACTED-EMAIL]"),(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b","[REDACTED-PHONE]")]:
            clean, c = re.subn(pat, rep, clean); m += c
    return clean, {"sha256": h, "pii_redacted": m, "date": datetime.now(timezone.utc).strftime("%d/%m/%Y")}

def audit_node(state: AuditState):
    llm = get_llm()
    fix = f"\nFIX THESE QUOTES (must match exact words in DOC): {state['hallucination_errors']}" if state.get("hallucination_errors") else ""
    prompt = f"""You are a forensic legal auditor. Analyze <DOC> against <RULES>. Return ONLY valid JSON (no markdown fences) with this exact structure:
{{"tldr": ["bullet 1", "bullet 2", "bullet 3"], "good": [{{"topic": "...", "exact_quote": "verbatim quote from DOC", "benefit_summary": "..."}}], "findings": [{{"finding_type": "HIDDEN LOOPHOLE", "clause_topic": "...", "exact_quote": "verbatim quote from DOC", "risk_level": "HIGH", "violation_reason": "...", "suggested_redline": "..."}}]}}
<RULES>\n{state['playbook_rules']}\n</RULES>\n<DOC>\n{state['contract_text'][:12000]}\n</DOC>{fix}"""
    raw = llm.invoke(prompt).content.strip()
    raw = re.sub(r"^```json\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()
    data = json.loads(raw)
    return {"report": {"tldr": data.get("tldr", []), "good": data.get("good", []), "findings": data.get("findings", [])}, "retries": state.get("retries", 0) + 1}
