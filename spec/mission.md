# Mission

## Problem

Medical auditors manually process unstructured clinical notes and patient charts from multiple clinics. They extract key clinical metrics — vitals, diagnoses, treatment details — and cross-reference them against insurance coverage policy rules to determine whether a treatment should be approved or flagged. This process is slow, labor-intensive, and prone to human error.

## Purpose

Build an AI-assisted medical chart auditing tool that automates the extraction and cross-referencing work, producing structured audit reports for human auditors to review and act on. The system accelerates auditor throughput and reduces error — without replacing auditor judgment.

## Primary Users

Internal medical auditors who access the system through a Streamlit web app. They upload clinical documents and policy materials, review AI-generated audit reports, and make final decisions on flagged cases.

## Core Principles

### Human-in-the-Loop — Always
The system makes no final decisions. It surfaces findings, flags inconsistencies, and generates structured reports. Any case that does not fully and clearly meet all approval criteria is escalated to a human auditor. Automation is an aid, not a replacement.

### Compliance First
HIPAA and PHI protection are non-negotiable requirements — not afterthoughts. All design, data handling, and infrastructure decisions must prioritize regulatory compliance from day one.

### Accuracy Over Speed
The highest-priority failure mode to avoid is incorrect extraction or hallucinated clinical data. The system must ground every finding in the source document. Uncertainty must be surfaced explicitly rather than hidden.

### Structured, Auditable Output
Every generated report must be traceable back to the source documents. The reasoning behind any flag or recommendation must be explainable to the auditor reviewing it.

## Scope

**In scope:**
- Ingestion of multi-format clinical documents (PDF, plain text, EHR exports, scanned images)
- Extraction of structured clinical data (vitals, diagnoses, treatments, dates)
- Cross-referencing extracted data against insurance policy rules (structured rules and uploaded policy documents)
- Generation of structured audit reports with clear approval, flag, or escalation status
- Escalation queue and review workflow for human auditors
- Full audit trail of system actions and human decisions

**Out of scope:**
- Making or recording final coverage decisions autonomously
- Direct integration with insurance carrier systems (Phase 1)
- Patient-facing features
- Billing or claims submission

## Success Criteria

- Auditors spend less time on data extraction and more time on decision-making
- Extraction accuracy is measurable and improvable against a ground-truth test set
- Every escalation to a human is traceable with a clear reason
- System passes HIPAA compliance review before handling real patient data
