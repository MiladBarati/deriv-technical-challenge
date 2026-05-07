"""LangGraph definition — wires all pipeline nodes into a sequential graph."""

from __future__ import annotations

from langgraph.graph import END, StateGraph

from deriv.engine.nodes import (
    approve_rubric,
    audit_compliance,
    compile_recommendations,
    design_rubric,
    exclude_blockers,
    finalize_results,
    generate_variants,
    load_brief,
    score_variants,
)
from deriv.engine.state import CopyEngineState
from langgraph.checkpoint.memory import MemorySaver

# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------


def build_graph() -> StateGraph:
    """Construct (but do not compile) the Copy Engine state graph."""
    graph = StateGraph(CopyEngineState)

    # Register nodes
    graph.add_node("load_brief", load_brief)
    graph.add_node("design_rubric", design_rubric)
    graph.add_node("approve_rubric", approve_rubric)
    graph.add_node("generate_variants", generate_variants)
    graph.add_node("score_variants", score_variants)
    graph.add_node("audit_compliance", audit_compliance)
    graph.add_node("exclude_blockers", exclude_blockers)
    graph.add_node("compile_recommendations", compile_recommendations)
    graph.add_node("finalize_results", finalize_results)

    # Sequential and Conditional edges
    graph.set_entry_point("load_brief")
    graph.add_edge("load_brief", "design_rubric")
    graph.add_edge("design_rubric", "approve_rubric")
    
    def route_rubric(state: CopyEngineState) -> str:
        feedback = state.get("operator_feedback", "").lower()
        if feedback == "reject":
            return "design_rubric"
        return "generate_variants"

    graph.add_conditional_edges("approve_rubric", route_rubric)
    graph.add_edge("generate_variants", "score_variants")
    graph.add_edge("score_variants", "audit_compliance")
    graph.add_edge("audit_compliance", "exclude_blockers")
    graph.add_edge("exclude_blockers", "compile_recommendations")
    graph.add_edge("compile_recommendations", "finalize_results")
    graph.add_edge("finalize_results", END)

    return graph


def compile_graph():
    """Build and compile the graph (Phase 2)."""
    checkpointer = MemorySaver()
    return build_graph().compile(checkpointer=checkpointer, interrupt_before=["approve_rubric"])
