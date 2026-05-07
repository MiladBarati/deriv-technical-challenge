"""CopyEngineState — the shared state flowing through every LangGraph node."""

from __future__ import annotations

from typing import Any, TypedDict


class CopyEngineState(TypedDict, total=False):
    """
    Central state object for the Copy Engine pipeline.

    Every node reads from and writes to this dict.  Using ``total=False``
    means fields start as absent and are populated progressively as the
    pipeline advances through its stages.
    """

    # Pipeline progress
    current_stage: str

    # Stage 0 — input
    product_brief: dict[str, Any]

    # Stage 1 — rubric
    rubric_draft: list[dict[str, Any]]
    operator_feedback: str
    approved_rubric: list[dict[str, Any]]

    # Stage 2 — generation
    copy_variants: list[dict[str, Any]]

    # Stage 3 — scoring
    variant_scores: list[dict[str, Any]]

    # Stage 4 — compliance
    compliance_audit: list[dict[str, Any]]

    # Stage 5 — recommendations
    recommendations: dict[str, Any]

    # Logging
    llm_logs: list[dict[str, Any]]
