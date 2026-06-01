import copy

from escalation import apply_escalation, should_escalate

# ── Fixtures ──────────────────────────────────────────────────────────────────

ALL_PASS_RULES = [
    {"rule_id": "R001", "description": "Diagnosis rule", "passed": True, "reason": "ICD found"},
    {"rule_id": "R002", "description": "BP rule", "passed": True, "reason": "BP within range"},
]

ONE_FAIL_RULES = [
    {"rule_id": "R001", "description": "Diagnosis rule", "passed": True, "reason": "ICD found"},
    {"rule_id": "R002", "description": "BP rule", "passed": False, "reason": "BP too high"},
]

APPROVED_RESULT = {
    "determination": "APPROVED",
    "reasoning": "All criteria met.",
    "cited_chunks": ["Policy excerpt A"],
}

FLAGGED_RESULT = {
    "determination": "FLAGGED",
    "reasoning": "One concern found.",
    "cited_chunks": [],
}

ESCALATE_RESULT = {
    "determination": "ESCALATE_TO_HUMAN",
    "reasoning": "Ambiguous evidence.",
    "cited_chunks": [],
}


# ── should_escalate ───────────────────────────────────────────────────────────

def test_no_escalation_when_all_rules_pass_and_approved():
    assert should_escalate(ALL_PASS_RULES, APPROVED_RESULT) is False


def test_escalation_when_any_rule_fails():
    assert should_escalate(ONE_FAIL_RULES, APPROVED_RESULT) is True


def test_escalation_when_determination_is_flagged():
    assert should_escalate(ALL_PASS_RULES, FLAGGED_RESULT) is True


def test_escalation_when_determination_is_already_escalate():
    assert should_escalate(ALL_PASS_RULES, ESCALATE_RESULT) is True


# ── apply_escalation ──────────────────────────────────────────────────────────

def test_apply_escalation_adds_escalation_reason():
    result = apply_escalation(ONE_FAIL_RULES, APPROVED_RESULT)
    assert "escalation_reason" in result
    assert isinstance(result["escalation_reason"], str)
    assert len(result["escalation_reason"]) > 0


def test_apply_escalation_does_not_mutate_input():
    original = {
        "determination": "APPROVED",
        "reasoning": "All criteria met.",
        "cited_chunks": ["excerpt"],
    }
    original_copy = copy.deepcopy(original)
    apply_escalation(ONE_FAIL_RULES, original)
    assert original == original_copy
