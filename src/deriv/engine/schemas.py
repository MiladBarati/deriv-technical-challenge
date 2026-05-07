"""Pydantic schemas and controlled taxonomy enums for the Copy Engine pipeline."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Controlled Taxonomy Enums
# ---------------------------------------------------------------------------


class CopyAngle(str, Enum):
    """Allowed creative copy angles."""

    FEAR_OF_MISSING_OUT = "fear_of_missing_out"
    SOCIAL_PROOF = "social_proof"
    BENEFIT_LED = "benefit_led"
    CURIOSITY = "curiosity"
    EMPOWERMENT = "empowerment"
    LOSS_AVERSION = "loss_aversion"


class ComplianceSeverity(str, Enum):
    """Allowed compliance severity levels."""

    BLOCKER = "blocker"
    WARNING = "warning"
    CLEAR = "clear"


class RecommendationStatus(str, Enum):
    """Allowed recommendation statuses."""

    ELIGIBLE = "eligible"
    EXCLUDED_COMPLIANCE_BLOCKER = "excluded_compliance_blocker"
    NEEDS_REVIEW = "needs_review"


# ---------------------------------------------------------------------------
# Rubric
# ---------------------------------------------------------------------------


class RubricDimension(BaseModel):
    """A single scoring dimension inside the rubric."""

    dimension_id: str
    name: str
    weight: float = Field(ge=0, le=1)
    scale: str = "0-10"
    description_of_10: str


# ---------------------------------------------------------------------------
# Copy Variants
# ---------------------------------------------------------------------------


class CopyVariant(BaseModel):
    """A single generated copy variant (headline, CTA, or sub-headline)."""

    variant_id: str
    variant_type: str = Field(pattern=r"^(headline|cta|subheadline)$")
    angle: CopyAngle
    text: str
    linked_headline_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Variant Scores
# ---------------------------------------------------------------------------


class DimensionScore(BaseModel):
    """Score for one dimension of the rubric."""

    dimension_id: str
    score: float = Field(ge=0, le=10)
    rationale: str


class VariantScore(BaseModel):
    """Persona-conditional score for a single variant."""

    variant_id: str
    persona: str
    dimension_scores: list[DimensionScore]
    total_weighted_score: float


# ---------------------------------------------------------------------------
# Compliance Audit
# ---------------------------------------------------------------------------


class ComplianceResult(BaseModel):
    """Compliance check result for a single variant."""

    variant_id: str
    variant_text: str
    status: ComplianceSeverity
    rule_violated: Optional[str] = None
    severity: ComplianceSeverity
    suggested_fix: Optional[str] = None


# ---------------------------------------------------------------------------
# LLM Call Logging
# ---------------------------------------------------------------------------


class LLMCallLog(BaseModel):
    """Metadata for a single LLM invocation."""

    stage: str
    timestamp: str
    provider: str
    model: str
    prompt_hash: str
    input_artifacts: list[str]
    output_artifact: str


# ---------------------------------------------------------------------------
# Structured Output Root Wrappers
# ---------------------------------------------------------------------------


class RubricWrapper(BaseModel):
    dimensions: list[RubricDimension]


class VariantsWrapper(BaseModel):
    variants: list[CopyVariant]


class ScoresWrapper(BaseModel):
    scores: list[VariantScore]
