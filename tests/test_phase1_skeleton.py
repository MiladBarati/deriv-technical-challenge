"""Phase 1 integration test — runs the full dummy graph and validates outputs."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from deriv.engine.graph import compile_graph
from deriv.engine.nodes import OUTPUT_DIR
from deriv.engine.schemas import (
    ComplianceResult,
    CopyVariant,
    RubricDimension,
    VariantScore,
)


@pytest.fixture(autouse=True)
def _clean_output_dir():
    """Remove and recreate the output directory for a clean run."""
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)
    yield
    # Intentionally leave artifacts after the test for manual inspection.


@pytest.fixture()
def final_state() -> dict:
    """Run the full graph and return the final state."""
    app = compile_graph()
    return app.invoke({"current_stage": "INIT", "llm_logs": []})


# ------------------------------------------------------------------
# Stage progression
# ------------------------------------------------------------------


class TestStageProgression:
    def test_final_stage_is_results_finalised(self, final_state):
        assert final_state["current_stage"] == "RESULTS_FINALISED"

    def test_product_brief_loaded(self, final_state):
        assert "product" in final_state["product_brief"]
        assert final_state["product_brief"]["product"] == "Deriv Bot"


# ------------------------------------------------------------------
# Artifact files exist on disk
# ------------------------------------------------------------------


class TestArtifactFiles:
    EXPECTED_FILES = [
        "rubric_draft.json",
        "approved_rubric.json",
        "copy_variants.json",
        "variant_scores.json",
        "compliance_audit.json",
        "recommendation.md",
        "llm_calls.jsonl",
    ]

    @pytest.mark.parametrize("filename", EXPECTED_FILES)
    def test_artifact_exists(self, final_state, filename):
        assert (OUTPUT_DIR / filename).exists(), f"{filename} not found in {OUTPUT_DIR}"


# ------------------------------------------------------------------
# Schema validation
# ------------------------------------------------------------------


class TestSchemaValidation:
    def test_rubric_has_5_dimensions(self, final_state):
        rubric = final_state["rubric_draft"]
        assert len(rubric) == 5
        for dim in rubric:
            RubricDimension(**dim)

    def test_approved_rubric_matches_draft(self, final_state):
        assert final_state["approved_rubric"] == final_state["rubric_draft"]

    def test_variants_count_and_schema(self, final_state):
        # After blocker exclusion, HL-06 + its 2 sub-headlines are removed → 24 - 3 = 21
        variants = final_state["copy_variants"]
        assert len(variants) == 21

        # Validate schema on the on-disk version (pre-exclusion, all 24)
        on_disk = json.loads((OUTPUT_DIR / "copy_variants.json").read_text())
        assert len(on_disk) == 24
        for v in on_disk:
            CopyVariant(**v)

    def test_variant_angles_coverage(self, final_state):
        on_disk = json.loads((OUTPUT_DIR / "copy_variants.json").read_text())
        angles = {v["angle"] for v in on_disk}
        expected = {
            "fear_of_missing_out",
            "social_proof",
            "benefit_led",
            "curiosity",
            "empowerment",
            "loss_aversion",
        }
        assert angles == expected

    def test_scores_schema(self, final_state):
        scores = final_state["variant_scores"]
        assert len(scores) > 0
        for s in scores:
            VariantScore(**s)

    def test_both_personas_scored(self, final_state):
        personas = {s["persona"] for s in final_state["variant_scores"]}
        assert "Retail Trader — Automation Curious" in personas
        assert "Experienced Trader — Time Poor" in personas

    def test_compliance_audit_schema(self, final_state):
        audit = final_state["compliance_audit"]
        assert len(audit) > 0
        for r in audit:
            ComplianceResult(**r)

    def test_blocker_present_in_audit(self, final_state):
        blockers = [r for r in final_state["compliance_audit"] if r["status"] == "blocker"]
        assert len(blockers) >= 1

    def test_recommendations_have_both_personas(self, final_state):
        recs = final_state["recommendations"]
        assert "primary_persona" in recs
        assert "secondary_persona" in recs

    def test_blocker_excluded_from_final_variants(self, final_state):
        variant_ids = {v["variant_id"] for v in final_state["copy_variants"]}
        assert "HL-06" not in variant_ids, "Blocker variant HL-06 should be excluded"
