import json
from loguru import logger

from deriv.engine.graph import compile_graph


def main():
    logger.info("🚀 Deriv Copy Engine — Phase 2 & 3")
    logger.info("=" * 60)

    app = compile_graph()
    thread_config = {"configurable": {"thread_id": "1"}}

    # Kick off with an empty initial state
    initial_state = {"current_stage": "INIT", "llm_logs": []}
    app.invoke(initial_state, config=thread_config)

    state = app.get_state(thread_config)

    while state.next:
        next_node = state.next[0]
        if next_node == "approve_rubric":
            rubric_draft = state.values.get("rubric_draft", [])
            print("\n" + "=" * 60)
            print("🛑 HUMAN IN THE LOOP: RUBRIC APPROVAL")
            print("=" * 60)
            print(json.dumps(rubric_draft, indent=2))
            print("=" * 60)

            choice = input("Do you (a)pprove, (e)dit, or (r)eject this rubric? [a/e/r]: ").strip().lower()

            if choice == "r":
                logger.warning("Operator rejected the rubric.")
                app.update_state(thread_config, {"operator_feedback": "reject"})
            elif choice == "e":
                print("Please edit 'output/rubric_draft.json' manually, save it, and then press Enter.")
                input("Press Enter to continue...")
                with open("output/rubric_draft.json", "r") as f:
                    edited_rubric = json.load(f)
                app.update_state(thread_config, {"operator_feedback": "approve", "rubric_draft": edited_rubric})
            else:
                logger.success("Operator approved the rubric.")
                app.update_state(thread_config, {"operator_feedback": "approve"})

            # Resume graph
            app.invoke(None, config=thread_config)
        else:
            app.invoke(None, config=thread_config)

        state = app.get_state(thread_config)

    final_state = state.values

    logger.info("=" * 60)
    logger.info(f"✅ Final stage: {final_state.get('current_stage')}")
    logger.info(f"   Variants in state: {len(final_state.get('copy_variants', []))}")
    logger.info(f"   Scores in state:   {len(final_state.get('variant_scores', []))}")
    logger.info(f"   Audit results:     {len(final_state.get('compliance_audit', []))}")

    return final_state


if __name__ == "__main__":
    main()
