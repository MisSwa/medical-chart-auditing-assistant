"""
Escalation trigger for audit determinations.

Rules (enforced without exception):
  - If any rule result has passed == False → escalate
  - If determination is not "APPROVED" → escalate
  - Only APPROVED + all rules passing → not escalated
"""
import copy


def should_escalate(rule_results: list[dict], determination_result: dict) -> bool:
    """
    Returns True if the case must be escalated to a human reviewer.
    Returns False only when all rules pass AND determination is "APPROVED".
    """
    for rule in rule_results:
        if not rule.get("passed", False):
            return True
    if determination_result.get("determination") != "APPROVED":
        return True
    return False


def apply_escalation(rule_results: list[dict], determination_result: dict) -> dict:
    """
    Applies the escalation rule. Returns a copy of determination_result with:
        - determination overridden to "ESCALATE_TO_HUMAN"
        - escalation_reason added: names the failing rules or ambiguous determination
    If not escalated, returns the original result dict unchanged.
    """
    if not should_escalate(rule_results, determination_result):
        return determination_result

    result = copy.copy(determination_result)

    failed_rules = [
        f"{r['rule_id']}: {r['description']}"
        for r in rule_results
        if not r.get("passed", False)
    ]
    if failed_rules:
        reason = "Escalated due to failing rule(s): " + "; ".join(failed_rules)
    else:
        original_det = determination_result.get("determination", "unknown")
        reason = (
            f"Escalated because determination was '{original_det}' "
            f"(only 'APPROVED' with all rules passing avoids escalation)."
        )

    result["determination"] = "ESCALATE_TO_HUMAN"
    result["escalation_reason"] = reason
    return result
