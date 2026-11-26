import os, re, json, hashlib
from datetime import datetime, timezone
from typing import TypedDict, List, Dict, Any
import streamlit as st
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

class AuditState(TypedDict):
    contract_text: str
    playbook_rules: str
    report: Dict[str, Any]
    retries: int
    hallucination_errors: List[str]
    security_metadata: Dict[str, Any]

def _groq_key() -> str:
    try:
        if "GROQ_API_KEY" in st.secrets:
            return str(st.secrets["GROQ_API_KEY"]).strip()
    except Exception:
        pass
    return os.getenv("GROQ_API_KEY", "").strip()

def invoke_llm(prompt: str, json_mode: bool = False) -> str:
    key = _groq_key()
    if not key:
        raise RuntimeError("GROQ_API_KEY is missing in Secrets.")
    kwargs = {"model_kwargs": {"response_format": {"type": "json_object"}}} if json_mode else {}
    for m in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]:
        try:
            llm = ChatGroq(model=m, api_key=key, temperature=0.0, max_tokens=2200, **kwargs)
            return llm.invoke(prompt).content
        except Exception as e:
            if "429" in str(e) or "404" in str(e) or "not_found" in str(e):
                continue
            raise e
    raise RuntimeError("All Groq models busy — please retry in 5 seconds.")

def sanitize_and_fingerprint(text: str, mask_pii: bool = True):
    h = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
    m, clean = 0, text
    if mask_pii:
        pats = [(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b", "[REDACTED-AADHAAR]"),
                (r"\b[A-Z]{5}\d{4}[A-Z]\b", "[REDACTED-PAN]"),
                (r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "[REDACTED-EMAIL]"),
                (r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b", "[REDACTED-PHONE]")]
        for pat, rep in pats:
            clean, c = re.subn(pat, rep, clean)
            m += c
    return clean, {"sha256": h, "pii_redacted": m, "date": datetime.now(timezone.utc).strftime("%d/%m/%Y")}
def audit_node(state: AuditState):
    rules = state["playbook_rules"].strip()
    prio = f"Check these user priorities FIRST, then audit ALL of <DOC>:\n{rules}" if rules else "Audit ALL of <DOC> with ruthless legal scrutiny."
    prompt = f"""You are LEXGUARDIAN, a ruthless consumer-protection contract auditor.
BE HYPER-STRICT. NEVER return 0 findings on any Terms of Service (like Zomato), job offer, rental agreement, or contract.
Find AT LEAST 3 to 6 concrete loopholes, unilateral rights, hidden fees, lock-ins, privacy grabs, or missing refund/exit protections.
{prio}
Return ONLY valid JSON with exact keys:
{{"tldr": ["bullet 1", "bullet 2", "bullet 3"],
  "good": [{{"topic": "Fair Clause", "exact_quote": "short verbatim quote", "benefit_summary": "why this protects the user"}}],
  "findings": [{{"finding_type": "HIDDEN LOOPHOLE", "clause_topic": "Topic Name", "exact_quote": "short verbatim quote from <DOC>", "risk_level": "CRITICAL", "violation_reason": "plain-English trap explanation", "suggested_redline": "exact safer replacement clause"}}]}}
<DOC>
{state['contract_text'][:11000]}
</DOC>"""
    raw = invoke_llm(prompt, json_mode=True)
    raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.S).strip()
    data = json.loads(raw, strict=False)
    findings = list(data.get("findings") or [])
    try:
        import critic_engine
        da = critic_engine.run_adversarial_critic(state["contract_text"])
        if len(findings) < 2:
            for df in da.get("findings", [])[:3]:
                findings.append({
                    "finding_type": "DEVIL'S ADVOCATE TRAP",
                    "clause_topic": df.get("severity", "CRITICAL"),
                    "exact_quote": df.get("exact_quote", "Asymmetric Terms"),
                    "risk_level": "HIGH",
                    "violation_reason": df.get("plain_english", ""),
                    "suggested_redline": df.get("counter_email", "Request mutual notice and fair exit terms.")
                })
        findings.append({
            "finding_type": "DEVIL'S ADVOCATE FINAL CHECK",
            "clause_topic": f"Safety Score: {da.get('safety_score', 30)}/100 ({da.get('verdict', 'DANGER')})",
            "exact_quote": "Adversarial Cross-Examination Complete",
            "risk_level": "HIGH",
            "violation_reason": da.get("bottom_line", "One-sided terms and missing protections detected."),
            "suggested_redline": "See full Devil's Advocate & Mistake Simulator breakdown below."
        })
    except Exception:
        pass
    return {"report": {"tldr": data.get("tldr", ["Audit complete."]), "good": data.get("good", []), "findings": findings}, "retries": state.get("retries", 0) + 1}

def verify_node(state: AuditState):
    good = [g for g in state["report"].get("good", []) if len(str(g.get("exact_quote", ""))) >= 3]
    bad = [x for x in state["report"].get("findings", []) if len(str(x.get("exact_quote", ""))) >= 3]
    return {"report": {"tldr": state["report"].get("tldr", []), "good": good, "findings": bad}, "hallucination_errors": []}

def ask_doc_question(doc_text: str, question: str) -> str:
    return invoke_llm(f"Answer in 2-3 simple sentences based ONLY on <DOC>:\nQuestion: {question}\n<DOC>\n{doc_text[:10000]}\n</DOC>")

wf = StateGraph(AuditState)
wf.add_node("audit", audit_node)
wf.add_node("verify", verify_node)
wf.set_entry_point("audit")
wf.add_edge("audit", "verify")
wf.add_edge("verify", END)
auditor_app = wf.compile()
