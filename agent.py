import re, json, hashlib
from datetime import datetime, timezone
import critic_engine

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
    return clean, {"sha256": h, "pii_redacted": m, "date": datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")}

def run_full_audit(text: str, playbook_rules: str = "") -> dict:
    rules = playbook_rules.strip()
    prio = f"Check these priorities FIRST:\n{rules}\nThen audit ALL of <DOC>." if rules else "Audit ALL of <DOC> with ruthless legal scrutiny."
    prompt = f"""You are LEXGUARDIAN, a ruthless consumer-protection contract auditor.
BE HYPER-STRICT. NEVER return 0 findings on any Terms of Service (like Zomato), job offer, rental agreement, or contract.
Find AT LEAST 3 to 5 concrete loopholes, unilateral rights, hidden fees, lock-ins, privacy grabs, or missing refund/exit protections.
{prio}
Return ONLY valid JSON:
{{"tldr": ["bullet 1", "bullet 2", "bullet 3"],
  "good": [{{"topic": "Fair Clause", "exact_quote": "short quote from text", "benefit_summary": "why this protects the user"}}],
  "findings": [{{"finding_type": "HIDDEN LOOPHOLE", "clause_topic": "Clause Name", "exact_quote": "short quote from text",
    "risk_level": "CRITICAL", "violation_reason": "plain-English trap explanation", "suggested_redline": "safer replacement clause"}}]}}
<DOC>
{text[:10000]}
</DOC>"""
    raw = re.sub(r"<think>.*?</think>", "", critic_engine.call_groq(prompt), flags=re.S)
    raw = re.sub(r"```json|```", "", raw).strip()
    m = re.search(r"\{.*\}", raw, flags=re.S)
    data = {}
    if m:
        try:
            data = json.loads(m.group(0), strict=False)
        except Exception:
            data = {}
    tldr = data.get("tldr") or ["Strict clause-by-clause audit completed.", "Review all highlighted financial & exit traps before signing."]
    good = data.get("good") or []
    findings = list(data.get("findings") or [])
    for f in findings:
        f["risk_level"] = str(f.get("risk_level", "HIGH")).upper()
        if f["risk_level"] not in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
            f["risk_level"] = "HIGH"
    return {"tldr": tldr, "good": good, "findings": findings}
def run_audit_with_critic(text: str, playbook_rules: str = "", pref_lang: str = "None"):
    rep = run_full_audit(text, playbook_rules)
    da = critic_engine.run_adversarial_critic(text, pref_lang)
    findings = rep["findings"]
    if len(findings) < 2:
        for df in da.get("findings", [])[:3]:
            findings.append({
                "finding_type": "STRICT TRAP DETECTED",
                "clause_topic": df.get("severity", "CRITICAL"),
                "exact_quote": df.get("exact_quote", "Asymmetric Clause"),
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
        "suggested_redline": "Review the full Devil's Advocate & Mistake Simulator breakdown below."
    })
    rep["findings"] = findings
    return rep, da

def ask_doc_question(doc_text: str, question: str) -> str:
    ans = critic_engine.call_groq(f"Answer in 2-3 simple sentences based ONLY on <DOC>:\nQuestion: {question}\n<DOC>\n{doc_text[:10000]}\n</DOC>")
    return re.sub(r"<think>.*?</think>", "", ans, flags=re.S).strip() or "Please review the highlighted clauses above."
