"""Dummy pipeline nodes for Phase 1 — no LLM calls, hardcoded data only.

Each function receives the ``CopyEngineState`` and returns a *partial* dict
that LangGraph merges back into state.  Every node also writes its artifact
to the ``output/`` directory for downstream inspection.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from loguru import logger

from deriv.engine.state import CopyEngineState
from deriv.engine.llm import generate_structured_output
from deriv.engine.schemas import RubricWrapper, VariantsWrapper, ScoresWrapper

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

OUTPUT_DIR = Path("output")


def _ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _write_json(filename: str, data: object) -> None:
    _ensure_output_dir()
    path = OUTPUT_DIR / filename
    path.write_text(json.dumps(data, indent=2))
    logger.info(f"  ✏️  Wrote {path}")


def _write_text(filename: str, text: str) -> None:
    _ensure_output_dir()
    path = OUTPUT_DIR / filename
    path.write_text(text)
    logger.info(f"  ✏️  Wrote {path}")


# ---------------------------------------------------------------------------
# Dummy data factories
# ---------------------------------------------------------------------------

ANGLES = [
    "fear_of_missing_out",
    "social_proof",
    "benefit_led",
    "curiosity",
    "empowerment",
    "loss_aversion",
]


def _dummy_rubric() -> list[dict]:
    """Return 5 hardcoded rubric dimensions."""
    dims = [
        ("clarity", "Message Clarity", "Copy is instantly understandable by a non-technical trader"),
        ("relevance", "Audience Relevance", "Copy speaks directly to persona pain-points and goals"),
        ("persuasion", "Persuasive Impact", "Copy compels the reader to take the next step"),
        ("tone_fit", "Tone Alignment", "Copy matches the brief's approachable, empowering tone"),
        ("compliance", "Compliance Safety", "Copy avoids all prohibited claims and implications"),
    ]
    return [
        {
            "dimension_id": did,
            "name": name,
            "weight": 0.2,
            "scale": "0-10",
            "description_of_10": desc,
        }
        for did, name, desc in dims
    ]


def _dummy_variants() -> list[dict]:
    """Generate 24 dummy variants: 6 headlines, 6 CTAs, 12 sub-headlines."""
    variants: list[dict] = []

    for i, angle in enumerate(ANGLES, start=1):
        hid = f"HL-{i:02d}"
        variants.append(
            {
                "variant_id": hid,
                "variant_type": "headline",
                "angle": angle,
                "text": f"[Dummy headline for {angle}]",
                "linked_headline_id": None,
            }
        )

    for i, angle in enumerate(ANGLES, start=1):
        variants.append(
            {
                "variant_id": f"CTA-{i:02d}",
                "variant_type": "cta",
                "angle": angle,
                "text": f"[Dummy CTA for {angle}]",
                "linked_headline_id": None,
            }
        )

    for i, angle in enumerate(ANGLES, start=1):
        hid = f"HL-{i:02d}"
        for j in range(1, 3):
            variants.append(
                {
                    "variant_id": f"SUB-{i:02d}-{j}",
                    "variant_type": "subheadline",
                    "angle": angle,
                    "text": f"[Dummy sub-headline {j} for {angle}]",
                    "linked_headline_id": hid,
                }
            )

    return variants


def _dummy_scores(variants: list[dict], rubric: list[dict]) -> list[dict]:
    """Score every headline & CTA for both personas using dummy values."""
    personas = [
        "Retail Trader — Automation Curious",
        "Experienced Trader — Time Poor",
    ]
    scores: list[dict] = []
    for v in variants:
        if v["variant_type"] in ("headline", "cta"):
            for persona in personas:
                dim_scores = [
                    {
                        "dimension_id": d["dimension_id"],
                        "score": 7.0,
                        "rationale": f"[Dummy rationale for {d['name']}]",
                    }
                    for d in rubric
                ]
                total = sum(
                    d["score"] * rd["weight"]
                    for d, rd in zip(dim_scores, rubric)
                )
                scores.append(
                    {
                        "variant_id": v["variant_id"],
                        "persona": persona,
                        "dimension_scores": dim_scores,
                        "total_weighted_score": round(total, 2),
                    }
                )
    return scores


def _dummy_compliance(variants: list[dict]) -> list[dict]:
    """Audit every variant — mark one as a blocker to exercise exclusion."""
    results: list[dict] = []
    for v in variants:
        # Mark the loss_aversion headline as a blocker for testing
        if v["variant_id"] == "HL-06":
            results.append(
                {
                    "variant_id": v["variant_id"],
                    "variant_text": v["text"],
                    "status": "blocker",
                    "rule_violated": "Must not imply guaranteed returns or risk-free trading",
                    "severity": "blocker",
                    "suggested_fix": "[Dummy fix: rewrite to remove guarantee implication]",
                }
            )
        else:
            results.append(
                {
                    "variant_id": v["variant_id"],
                    "variant_text": v["text"],
                    "status": "clear",
                    "rule_violated": None,
                    "severity": "clear",
                    "suggested_fix": None,
                }
            )
    return results


def _dummy_recommendation_md() -> str:
    """Build a dummy recommendation markdown document."""
    return """\
# Copy Deck Recommendation

## Primary Persona: Retail Trader — Automation Curious

| Element       | Selected                                       |
|---------------|------------------------------------------------|
| Headline      | [Dummy headline for empowerment]               |
| Sub-headline  | [Dummy sub-headline 1 for empowerment]         |
| CTA           | [Dummy CTA for empowerment]                    |

### Benefit Bullets
- Build strategies visually — no coding skills needed
- Backtest against real historical data before risking capital
- Your bot runs 24/7, even while you sleep

### Trust Signal
Join thousands of traders already automating with Deriv Bot.

### Compliance Notes
All variants passed compliance audit (clear status).

### Recommendation Rationale
The empowerment angle scored highest across all rubric dimensions for the
primary persona. The copy directly addresses the persona's desire for control
while alleviating fears about automation complexity.

---

## Secondary Persona: Experienced Trader — Time Poor

| Element       | Selected                                       |
|---------------|------------------------------------------------|
| Headline      | [Dummy headline for benefit_led]               |
| Sub-headline  | [Dummy sub-headline 1 for benefit_led]         |
| CTA           | [Dummy CTA for benefit_led]                    |

### Benefit Bullets
- Scale your strategies across Forex, Synthetics, and Crypto
- Fine-tune every parameter — full customisability
- Eliminate screen-watching without sacrificing control

### Trust Signal
Trusted by experienced traders managing multi-market portfolios.

### Compliance Notes
All variants passed compliance audit (clear status).

### Recommendation Rationale
The benefit-led angle resonated most strongly with time-poor experienced traders,
emphasising efficiency gains and customisability — the top priorities for this persona.
"""


# ---------------------------------------------------------------------------
# Pipeline Nodes
# ---------------------------------------------------------------------------


def load_brief(state: CopyEngineState) -> dict:
    """Read product_brief.json from disk into state."""
    logger.info("📄 [load_brief] Loading product brief …")

    brief_path = Path("product_brief.json")
    if not brief_path.exists():
        raise FileNotFoundError(f"Product brief not found at {brief_path.resolve()}")

    brief = json.loads(brief_path.read_text())
    logger.info(f"  ✅ Loaded brief for product: {brief['product_brief']['product']}")

    return {
        "product_brief": brief["product_brief"],
        "current_stage": "PRODUCT_BRIEF_LOADED",
    }


def design_rubric(state: CopyEngineState) -> dict:
    """Generate a scoring rubric using the LLM."""
    logger.info("📐 [design_rubric] Designing scoring rubric via LLM …")

    brief = state["product_brief"]
    system_prompt = (
        "You are an expert copywriter and marketing strategist. "
        "Your task is to design a strict scoring rubric to evaluate marketing copy variants. "
        "The rubric MUST contain exactly 5 dimensions based on clarity, relevance, persuasion, tone fit, and compliance. "
        "Each dimension should have an id, name, weight (summing to 1.0 total), scale (e.g. 0-10), and a description of what a 10 looks like. "
        "The tone, constraints, and audience details from the brief must be considered."
    )
    user_prompt = f"Product Brief:\n{json.dumps(brief, indent=2)}\n\nDesign a 5-dimension scoring rubric."
    
    wrapper = generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=RubricWrapper,
        stage="design_rubric",
        input_artifacts=["product_brief.json"],
        output_artifact="rubric_draft.json",
        state=state,
    )
    
    rubric = [d.model_dump() for d in wrapper.dimensions]
    _write_json("rubric_draft.json", rubric)

    logger.info(f"  ✅ Rubric drafted with {len(rubric)} dimensions")
    return {
        "rubric_draft": rubric,
        "current_stage": "RUBRIC_DRAFTED",
    }


def approve_rubric(state: CopyEngineState) -> dict:
    """Handle operator approval/rejection from the state."""
    feedback = state.get("operator_feedback", "approve")
    if feedback == "reject":
        logger.warning("❌ [approve_rubric] Rubric was rejected, routing back to design ...")
        return {"current_stage": "RUBRIC_REJECTED"}
    else:
        logger.info("✅ [approve_rubric] Rubric approved.")
        approved = state["rubric_draft"]
        _write_json("approved_rubric.json", approved)
        return {
            "approved_rubric": approved,
            "current_stage": "RUBRIC_APPROVED",
        }


def generate_variants(state: CopyEngineState) -> dict:
    """Generate copy variants using the LLM."""
    logger.info("✍️  [generate_variants] Generating copy variants via LLM …")

    brief = state["product_brief"]
    system_prompt = (
        "You are an expert copywriter. Your task is to generate marketing copy based on the product brief. "
        "You MUST generate exactly 6 headlines (one for each angle), 6 CTAs (one for each angle), "
        "and 12 subheadlines (2 for each headline, linked_headline_id must match the corresponding headline's variant_id). "
        "The 6 angles are: fear_of_missing_out, social_proof, benefit_led, curiosity, empowerment, loss_aversion. "
        "Ensure you adhere strictly to tone guidance and compliance constraints."
    )
    user_prompt = f"Product Brief:\n{json.dumps(brief, indent=2)}\n\nGenerate the copy variants."
    
    wrapper = generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=VariantsWrapper,
        stage="generate_variants",
        input_artifacts=["product_brief.json", "approved_rubric.json"],
        output_artifact="copy_variants.json",
        state=state,
    )
    
    variants = [v.model_dump() for v in wrapper.variants]
    _write_json("copy_variants.json", variants)

    n_hl = sum(1 for v in variants if v["variant_type"] == "headline")
    n_cta = sum(1 for v in variants if v["variant_type"] == "cta")
    n_sub = sum(1 for v in variants if v["variant_type"] == "subheadline")
    logger.info(f"  ✅ Generated {n_hl} headlines, {n_cta} CTAs, {n_sub} sub-headlines")

    return {
        "copy_variants": variants,
        "current_stage": "VARIANTS_GENERATED",
    }


def score_variants(state: CopyEngineState) -> dict:
    """Score variants against the approved rubric using the LLM."""
    logger.info("📊 [score_variants] Scoring variants by persona via LLM …")

    brief = state["product_brief"]
    rubric = state["approved_rubric"]
    variants = state["copy_variants"]
    
    system_prompt = (
        "You are a critical marketing copy evaluator. "
        "Score each provided headline and CTA variant for BOTH the primary persona and the secondary persona. "
        "Use the exact dimensions, scales, and weights provided in the rubric. "
        "You must output a list of scores, one per variant-persona pair."
    )
    user_prompt = (
        f"Product Brief:\n{json.dumps(brief, indent=2)}\n\n"
        f"Rubric:\n{json.dumps(rubric, indent=2)}\n\n"
        f"Variants:\n{json.dumps(variants, indent=2)}\n\n"
        "Score the headline and CTA variants."
    )
    
    wrapper = generate_structured_output(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        response_model=ScoresWrapper,
        stage="score_variants",
        input_artifacts=["product_brief.json", "approved_rubric.json", "copy_variants.json"],
        output_artifact="variant_scores.json",
        state=state,
    )
    
    scores = [s.model_dump() for s in wrapper.scores]
    _write_json("variant_scores.json", scores)

    logger.info(f"  ✅ Produced {len(scores)} score records")
    return {
        "variant_scores": scores,
        "current_stage": "VARIANTS_SCORED",
    }


def audit_compliance(state: CopyEngineState) -> dict:
    """Run compliance audit on all variants (LLM call placeholder)."""
    logger.info("🛡️  [audit_compliance] Auditing compliance …")

    audit = _dummy_compliance(state["copy_variants"])
    _write_json("compliance_audit.json", audit)

    blockers = sum(1 for r in audit if r["status"] == "blocker")
    logger.info(f"  ✅ Audit complete — {blockers} blocker(s) found")

    return {
        "compliance_audit": audit,
        "current_stage": "COMPLIANCE_AUDITED",
    }


def exclude_blockers(state: CopyEngineState) -> dict:
    """Remove blocker-flagged variants from the pool."""
    logger.info("🚫 [exclude_blockers] Excluding blocker variants …")

    blocker_ids = {
        r["variant_id"]
        for r in state["compliance_audit"]
        if r["status"] == "blocker"
    }

    remaining = [v for v in state["copy_variants"] if v["variant_id"] not in blocker_ids]
    excluded_count = len(state["copy_variants"]) - len(remaining)
    logger.info(f"  ✅ Excluded {excluded_count} variant(s), {len(remaining)} remaining")

    return {
        "copy_variants": remaining,
        "current_stage": "BLOCKERS_EXCLUDED",
    }


def compile_recommendations(state: CopyEngineState) -> dict:
    """Assemble the final recommendation deck."""
    logger.info("📋 [compile_recommendations] Compiling recommendations …")

    rec_md = _dummy_recommendation_md()
    _write_text("recommendation.md", rec_md)

    recommendations = {
        "primary_persona": {
            "headline": "HL-05",
            "subheadline": "SUB-05-1",
            "cta": "CTA-05",
            "status": "eligible",
        },
        "secondary_persona": {
            "headline": "HL-03",
            "subheadline": "SUB-03-1",
            "cta": "CTA-03",
            "status": "eligible",
        },
    }

    logger.info("  ✅ Recommendation deck written")
    return {
        "recommendations": recommendations,
        "current_stage": "RECOMMENDATIONS_SELECTED",
    }


def finalize_results(state: CopyEngineState) -> dict:
    """Write LLM call log and mark pipeline complete."""
    logger.info("🏁 [finalize_results] Finalising results …")

    # In Phase 1 there are no real LLM calls, so the log is empty.
    llm_logs: list[dict] = state.get("llm_logs", [])

    _ensure_output_dir()
    log_path = OUTPUT_DIR / "llm_calls.jsonl"
    with log_path.open("w") as f:
        for entry in llm_logs:
            f.write(json.dumps(entry) + "\n")
    logger.info(f"  ✏️  Wrote {log_path} ({len(llm_logs)} records)")

    logger.info("  ✅ Pipeline complete — all artifacts saved to output/")
    return {
        "llm_logs": llm_logs,
        "current_stage": "RESULTS_FINALISED",
    }
