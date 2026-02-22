"""
Orchestrator Agent - Chief Bid Officer (Central Controller)

The main decision-making agent that coordinates all other agents,
manages state transitions, and produces the final ConsolidatedBid.
"""

from typing import Dict, Any
from datetime import datetime

from backend.state import RFPGraphState, ConsolidatedBid
from backend.config import settings, create_llm_chain, ORCHESTRATOR_SYSTEM_PROMPT


def create_orchestrator_agent_chain():
    """Create the orchestrator/CBO agent LLM."""
    return create_llm_chain()


def consolidate_bid_node(state: RFPGraphState) -> RFPGraphState:
    """
    Consolidate all agent outputs into final ConsolidatedBid.

    This node assembles the final bid package with:
    - All selected SKUs and technical specs
    - Complete pricing breakdown
    - Business ROI metrics
    - Agent communication audit trail

    Args:
        state: Current graph state

    Returns:
        Updated state with consolidated_bid
    """
    try:
        rfp = state.get("qualified_rfp")
        selected_skus = state.get("selected_skus")
        pricing_results = state.get("pricing_results")
        roi_analysis = state.get("roi_analysis", {})

        if not rfp or not selected_skus or not pricing_results:
            state["errors"].append("Missing required data for bid consolidation")
            state["status"] = "failed_consolidation"
            return state

        # Calculate technical compliance (average SMM)
        technical_compliance = sum(sku.smm_score for sku in selected_skus) / len(selected_skus)

        # Calculate total bid value
        total_bid_value = sum(pr.grand_total for pr in pricing_results)

        # Create ConsolidatedBid
        consolidated_bid = ConsolidatedBid(
            rfp_id=rfp.id,
            selected_skus=selected_skus,
            pricing_breakdown=pricing_results,
            total_bid_value=total_bid_value,
            technical_compliance=technical_compliance,
            business_roi=roi_analysis,
            agent_logs=state.get("agent_logs", []),
        )

        state["consolidated_bid"] = consolidated_bid
        state["status"] = "bid_consolidated"

        # Final log entry
        state["agent_logs"].append({
            "agent": "Orchestrator (CBO)",
            "action": "Consolidate Bid",
            "result": f"Final Bid: ₹{total_bid_value:,.0f}, Compliance: {technical_compliance:.1f}%",
        })

        return state

    except Exception as e:
        state["errors"].append(f"Bid consolidation error: {str(e)}")
        state["status"] = "failed_consolidation"
        return state


def make_final_decision_node(state: RFPGraphState) -> RFPGraphState:
    """
    Make final go/no-go decision.

    Decision logic:
    - APPROVE: If no critical errors, all compliance OK, risk manageable
    - ESCALATE: If any issues requiring executive review
    - DECLINE: If critical failures or unresolvable constraints

    Args:
        state: Current graph state

    Returns:
        Updated state with final_decision field
    """
    errors = state.get("errors", [])
    rfp = state.get("qualified_rfp")
    technical_ok = state.get("technical_compliance_ok", False)
    pricing_ok = state.get("pricing_constraints_met", False)
    consolidated_bid = state.get("consolidated_bid")

    decision = "approve"

    # Critical failures
    if errors and len(errors) > 3:
        state["status"] = "decision_decline"
        decision = "decline"
    elif not consolidated_bid:
        state["status"] = "decision_decline"
        decision = "decline"
    # Check core compliance
    elif not (technical_ok and pricing_ok):
        state["status"] = "decision_escalate"
        decision = "escalate"
    # Check risk score
    elif rfp and rfp.risk_score > 5:
        state["status"] = "decision_escalate"
        decision = "escalate"
    # Approve
    else:
        state["status"] = "decision_approve"
        decision = "approve"

    # Store decision in state
    state["final_decision"] = decision

    # Add log entry
    state["agent_logs"].append({
        "agent": "Orchestrator (Final Decision)",
        "action": "Make Final Decision",
        "result": f"Decision: {decision.upper()}",
    })

    return state


def end_node(state: RFPGraphState) -> RFPGraphState:
    """
    Final workflow node - set completion timestamp and status.

    Args:
        state: Current graph state

    Returns:
        Final state
    """
    state["completion_timestamp"] = datetime.now().isoformat()

    if not state.get("consolidated_bid"):
        state["status"] = "workflow_failed"
    elif state.get("status") == "decision_approve":
        state["status"] = "workflow_complete_approved"
    elif state.get("status") == "decision_escalate":
        state["status"] = "workflow_complete_escalated"
    else:
        state["status"] = "workflow_complete_declined"

    return state


# ==================== EXPORT ====================
__all__ = [
    "create_orchestrator_agent_chain",
    "consolidate_bid_node",
    "make_final_decision_node",
    "end_node",
]
