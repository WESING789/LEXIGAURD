import os, hashlib, re
from datetime import datetime, timezone
from typing import List, Literal, TypedDict
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

class GoodPoint(BaseModel):
    topic: str
    exact_quote: str
    benefit_summary: str

class ClauseAudit(BaseModel):
    finding_type: Literal["HIDDEN LOOPHOLE", "CLAUSE CONTRADICTION", "SILENT OMISSION", "RULE VIOLATION"]
    clause_topic: str
    exact_quote: str
    risk_level: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]
    violation_reason: str
    suggested_redline: str

class AuditReport(BaseModel):
    plain_english_tldr: List[str]
    good_points: List[GoodPoint]
    findings: List[ClauseAudit]

class AuditState(TypedDict):
    contract_text: str
    playbook_rules: str
    report: dict
    hallucination_errors: List[str]
    security_metadata: dict
    retries: int

def get_llm():
    if os.getenv("GOOGLE_API_KEY"): return ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    return ChatOllama(model="qwen2.5:7b", temperature=0)

def sanitize_and_fingerprint(text: str, mask_pii: bool = True):
    h = hashlib.sha256(text.encode()).hexdigest()
    m, clean = 0, text
    if mask_pii:
        for pat, rep in [(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b","[REDACTED-AADHAAR]"),(r"\b[A-Z]{5}\d{4}[A-Z]\b","[REDACTED-PAN]"),(r"\b[\w\.-]+@[\w\.-]+\.\w+\b","[REDACTED-EMAIL]"),(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b","[REDACTED-PHONE]")]:
            clean, c = re.subn(pat, rep, clean); m += c
    return clean, {"sha256": h, "pii_redacted": m, "date": datetime.now(timezone.utc).strftime("%d/%m/%Y")}

def audit_node(state: AuditState):
    llm = get_llm().with_structured_output(AuditReport)
    fix = f"\nFIX QUOTES: {state['hallucination_errors']}" if state.get("hallucination_errors") else ""
    prompt = f"Audit <DOC> against <RULES> for people who hate reading fine print. Return 3 plain_english_tldr bullets, fair good_points, and risky findings (HIDDEN LOOPHOLE, CLAUSE CONTRADICTION, SILENT OMISSION, RULE VIOLATION) with verbatim exact_quote.\n<RULES>\n{state['playbook_rules']}\n</RULES>\n<DOC>\n{state['contract_text'][:14000]}\n</DOC>{fix}"
    res = llm.invoke(prompt)
    return {"report": {"tldr": res.plain_english_tldr, "good": [g.model_dump() for g in res.good_points], "findings": [f.model_dump() for f in res.findings]}, "retries": state.get("retries", 0) + 1}

def verify_node(state: AuditState):
    norm = " ".join(state["contract_text"].split()).lower()
    errs, ok_bad, ok_good = [], [], []
    for g in state["report"].get("good", []):
        if len(g["exact_quote"]) >= 6 and " ".join(g["exact_quote"].split()).lower() in norm: ok_good.append(g)
    for item in state["report"].get("findings", []):
        if len(item["exact_quote"]) >= 6 and " ".join(item["exact_quote"].split()).lower() in norm: ok_bad.append(item)
        else: errs.append(item["exact_quote"])
    return {"report": {"tldr": state["report"].get("tldr", []), "good": ok_good, "findings": ok_bad}, "hallucination_errors": errs}

wf = StateGraph(AuditState)
wf.add_node("audit", audit_node); wf.add_node("verify", verify_node)
wf.set_entry_point("audit"); wf.add_edge("audit", "verify")
wf.add_conditional_edges("verify", lambda s: "retry" if (s["hallucination_errors"] and s["retries"] < 3) else "pass", {"retry": "audit", "pass": END})
auditor_app = wf.compile()
