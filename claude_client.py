import json
import os

from anthropic import Anthropic
from langsmith import traceable

EXTRACTION_PROMPT = """\
You are a medical chart auditing assistant. Extract specific clinical data from the clinical note below.

Extract these fields if present:
1. vitals: blood_pressure, heart_rate, temperature, weight
2. diagnoses: list of diagnoses (include ICD-10 code if mentioned)
3. medications: list of medications with dosages

Rules — follow these exactly:
- Every extracted field MUST include "source_text": the exact quote from the document that supports it.
- If a field is not present in the document, return null for that field. Do NOT invent or infer values.
- Assign confidence: "high" (clearly stated), "medium" (implied or partial), "low" (uncertain or ambiguous).
- A null value with low confidence is always correct. A hallucinated value with high confidence is never acceptable.
- For diagnoses and medications with no entries, return an empty list [].

Return ONLY valid JSON — no explanation, no markdown fences:
{{
  "vitals": {{
    "blood_pressure": {{"value": "120/80 mmHg", "source_text": "...", "confidence": "high"}} | null,
    "heart_rate": {{"value": "72 bpm", "source_text": "...", "confidence": "high"}} | null,
    "temperature": {{"value": "98.6°F", "source_text": "...", "confidence": "high"}} | null,
    "weight": {{"value": "185 lbs", "source_text": "...", "confidence": "medium"}} | null
  }},
  "diagnoses": [
    {{"value": "Diagnosis name", "icd_code": "E11.9", "source_text": "...", "confidence": "high"}}
  ],
  "medications": [
    {{"value": "Medication name and dosage", "source_text": "...", "confidence": "high"}}
  ]
}}

<clinical_note>
{document_text}
</clinical_note>"""


def get_client() -> Anthropic:
    """Create and return an Anthropic client. Raises EnvironmentError if API key is missing."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY is not set. "
            "Add it to your .env file or set it as an environment variable."
        )
    return Anthropic(api_key=api_key)


@traceable(name="extract_clinical_data", run_type="llm")
def extract_clinical_data(document_text: str) -> dict:
    """
    Send document text to Claude and return a structured clinical extraction dict.

    Schema per field:
        {"value": str, "source_text": str, "confidence": "high"|"medium"|"low"}

    Raises EnvironmentError if API key is absent.
    Raises json.JSONDecodeError if the response is not valid JSON.
    Raises anthropic.APIError on API failures.
    """
    client = get_client()
    prompt = EXTRACTION_PROMPT.format(document_text=document_text)

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()

    # Strip markdown code fences if present
    if response_text.startswith("```"):
        lines = response_text.splitlines()
        response_text = "\n".join(lines[1:-1]).strip()

    return json.loads(response_text)
