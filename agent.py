import os, json, hashlib, re
from datetime import datetime, timezone
from typing import List, TypedDict
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

class AuditState(TypedDict):
    contract_text: str; playbook_rules: str; report: dict; hallucination_errors: List[str]; security_metadata: dict; retries: int

def invoke_llm(prompt: str) -> str:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if key:
        for m in ["llama-3.3-70b-versatile", "llama-3.1-8b-instant",  "openai/gpt-oss-20b", "qwen/qwen3-32b"]:
            try: return ChatGroq(model=m, api_key=key, temperature=0, max_tokens=3000).invoke(prompt).content
            except Exception as e:
                if "model_not_found" in str(e) or "404" in str(e): continue
                raise e
    return ChatOllama(model="qwen2.5:7b", temperature=0).invoke(prompt).content

def sanitize_and_fingerprint(text: str, mask_pii: bool = True):
    h = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
    m, clean = 0, text
    if mask_pii:
        for pat, rep in [(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b","[REDACTED-AADHAAR]"),(r"\b[A-Z]{5}\d{4}[A-Z]\b","[REDACTED-PAN]"),(r"\b[\w\.-]+@[\w\.-]+\.\w+\b","[REDACTED-EMAIL]"),(r"\b(?:\+91[\-\s]?)?[6-9]\d{9}\b","[REDACTED-PHONE]")]:
            clean, c = re.subn(pat, rep, clean); m += c
    return clean, {"sha256": h, "pii_redacted": m, "date": datetime.now(timezone.utc).strftime("%d/%m/%Y")}

def audit_node(state: AuditState):
    fix = f"\nFIX QUOTES: {state['hallucination_errors']}" if state.get("hallucination_errors") else ""
    rules = state['playbook_rules'].strip()
    rule_inst = f"Check these priorities FIRST, then scan all of <DOC>:\n{rules}" if rules else "Scan the ENTIRE <DOC> broadly for fair points, hidden loopholes, contradictions, and traps."
    prompt = f"Analyze <DOC> for someone who hates reading fine print. {rule_inst}\nReturn ONLY valid JSON (no markdown):\n{{\"tldr\": [\"b1\", \"b2\", \"b3\"], \"good\": [{{\"topic\": \"...\", \"exact_quote\": \"verbatim quote\", \"benefit_summary\": \"...\"}}], \"findings\": [{{\"finding_type\": \"HIDDEN LOOPHOLE\", \"clause_topic\": \"...\", \"exact_quote\": \"verbatim quote\", \"risk_level\": \"HIGH\", \"violation_reason\": \"...\", \"suggested_redline\": \"...\"}}]}}\n<DOC>\n{state['contract_text'][:10000]}\n</DOC>{fix}"
    raw = invoke_llm(prompt)
    if "</think>" in raw: raw = raw.split("</think>")[-1]
    raw = re.sub(r"<think>.*", "", raw, flags=re.DOTALL).strip()
    s, e = raw.find("{"), raw.rfind("}") + 1
    try: data = json.loads(raw[s:e]) if s != -1 and e > s else {"tldr": ["Scan complete."], "good": [], "findings": []}
    except Exception: data = {"tldr": ["Scan complete."], "good": [], "findings": []}
    return {"report": {"tldr": data.get("tldr", []), "good": data.get("good", []), "findings": data.get("findings", [])}, "retries": state.get("retries", 0) + 1}

def verify_node(state: AuditState):
    norm = " ".join(state["contract_text"].split()).lower()
    errs, ok_bad, ok_good = [], [], []
    for g in state["report"].get("good", []):
        q = str(g.get("exact_quote", ""))
        if len(q) >= 6 and " ".join(q.split()).lower() in norm: ok_good.append(g)
    for item in state["report"].get("findings", []):
        q = str(item.get("exact_quote", ""))
        if len(q) >= 6 and " ".join(q.split()).lower() in norm: ok_bad.append(item)
        else: errs.append(q)
    return {"report": {"tldr": state["report"].get("tldr", []), "good": ok_good, "findings": ok_bad}, "hallucination_errors": errs}

def ask_doc_question(doc_text: str, question: str) -> str:
    return invoke_llm(f"Answer in 2-3 simple sentences based ONLY on <DOC>:\nQuestion: {question}\n<DOC>\n{doc_text[:10000]}\n</DOC>")

wf = StateGraph(AuditState)
wf.add_node("audit", audit_node); wf.add_node("verify", verify_node)
wf.set_entry_point("audit"); wf.add_edge("audit", "verify")
wf.add_conditional_edges("verify", lambda s: "retry" if (s["hallucination_errors"] and s["retries"] < 3) else "pass", {"retry": "audit", "pass": END})
auditor_app = wf.compile()
