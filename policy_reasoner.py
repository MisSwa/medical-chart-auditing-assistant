"""
Policy reasoning via Claude Opus.

Combines Phase 1 extraction, structured rule results, and retrieved policy chunks
to produce a traceable APPROVED / FLAGGED / ESCALATE_TO_HUMAN determination.
"""
import json
import os

from anthropic import Anthropic
from langsmith import traceable

VALID_DETERMINATIONS = {"APPROVED", "FLAGGED", "ESCALATE_TO_HUMAN"}

_REASONING_PROMPT = """\
You are a medical chart auditing assistant. Review the clinical case below against \
insurance policy coverage criteria and produce an audit determination.

You are given:
1. Extracted clinical data from the patient chart
2. Relevant policy excerpts retrieved from the insurance policy document
3. Structured rule evaluation results

## Extracted Clinical Data
{extraction_json}

## Retrieved Policy Excerpts
{policy_chunks}

## Rule Evaluation Results
{rule_results_json}

## Instructions
- Review the clinical data against the policy excerpts and rule results.
- Produce one of these determinations:
  - APPROVED: All rules pass and the policy excerpts clearly support coverage.
  - FLAGGED: One or more rules fail or policy excerpts raise concerns, but the case \
may still be resolvable with additional documentation.
  - ESCALATE_TO_HUMAN: Ambiguous evidence, incomplete data, contradictory findings, \
or any uncertainty. When in doubt, always escalate — never fabricate a determination.
- Cite the specific policy excerpt text that informed your reasoning.
- Be conservative: a missed escalation is worse than an unnecessary one.

Return ONLY valid JSON with no explanation or markdown fences:
{{
  "determination": "APPROVED" | "FLAGGED" | "ESCALATE_TO_HUMAN",
  "reasoning": "Your detailed reasoning here, referencing specific rule results and policy text.",
  "cited_chunks": ["Exact or near-exact quote from a policy excerpt", ...]
}}"""


def build_reasoning_prompt(
    extraction: dict, rule_results: list[dict], policy_chunks: list[str]
) -> str:
    """Assemble the full context prompt for Claude Opus."""
    chunks_formatted = "\n\n".join(
        f"[Excerpt {i + 1}]\n{chunk}" for i, chunk in enumerate(policy_chunks)
    )
    return _REASONING_PROMPT.format(
        extraction_json=json.dumps(extraction, indent=2),
        policy_chunks=chunks_formatted,
        rule_results_json=json.dumps(rule_results, indent=2),
    )


@traceable(name="reason_against_policy", run_type="llm")
def reason_against_policy(
    extraction: dict, rule_results: list[dict], policy_chunks: list[str]
) -> dict:
    """
    Call Claude Opus to reason over extracted data, rule results, and policy chunks.

    Returns:
        {"determination": str, "reasoning": str, "cited_chunks": [str]}

    Always defaults to ESCALATE_TO_HUMAN if the response cannot be cleanly parsed
    or if the determination value is not in the valid set.
    """
    client = _get_client()
    prompt = build_reasoning_prompt(extraction, rule_results, policy_chunks)

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()

    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.splitlines()
        response_text = "\n".join(lines[1:-1]).strip()

    try:
        result = json.loads(response_text)
        determination = result.get("determination", "")
        if determination not in VALID_DETERMINATIONS:
            return _escalate_default(f"Unexpected determination value: '{determination}'")
        return {
            "determination": determination,
            "reasoning": result.get("reasoning", ""),
            "cited_chunks": result.get("cited_chunks", []),
        }
    except (json.JSONDecodeError, AttributeError):
        return _escalate_default("Failed to parse Claude response as valid JSON")


def _escalate_default(reason: str) -> dict:
    return {
        "determination": "ESCALATE_TO_HUMAN",
        "reasoning": f"Determination defaulted to ESCALATE_TO_HUMAN: {reason}.",
        "cited_chunks": [],
    }


def _get_client() -> Anthropic:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file or set it as an environment variable."
        )
    return Anthropic(api_key=api_key)
