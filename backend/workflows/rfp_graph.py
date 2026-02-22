"""
RFP Processing Workflow - Main LangGraph StateGraph

Defines the complete multi-agent workflow for RFP processing:
1. Sales discovery & qualification
2. Technical specification extraction
3. Technical agent matching with retry logic
4. Pricing calculation with LME indexing
5. Business advisory analysis
6. Final bid consolidation

The graph implements conditional edges for:
- Retry loops (technical agent retries up to 3 times)
- Compliance validation (technical & pricing checks)
- Decision routing (approve/escalate/decline)
"""

from typing import Literal
from langgraph.graph import StateGraph, END

from backend.state import RFPGraphState
from backend.agents.sales_agent import (
    sales_agent_node,
    extract_specifications_node,
)
from backend.agents.technical_agent import (
    technical_agent_node,
    check_technical_compliance_node,
)
from backend.agents.pricing_agent import (
    pricing_agent_node,
    check_pricing_constraints_node,
)
from backend.agents.business_advisory_agent import (
    business_advisory_agent_node,
)
from backend.agents.orchestrator_agent import (
    consolidate_bid_node,
    make_final_decision_node,
    end_node,
)


def create_rfp_processing_graph() -> StateGraph:
    """
    Create the complete RFP processing workflow graph.

    Node Structure:
    ```
    START
      ↓
    sales_agent_node [Qualify RFP]
      ↓
    extract_specifications_node [Parse product specs]
      ↓
    technical_agent_node [SMM matching]
      ↓
    check_technical_node [Is SMM >= 80%?]
      ├─ NO → technical_agent_node [Retry with relaxation]
      │   ↻ loop up to 3 times
      └─ YES ↓
    pricing_agent_node [Calculate bid]
      ↓
    check_pricing_node [Meets constraints?]
      └─ YES ↓
    business_advisory_node [ROI analysis]
      ↓
    consolidate_bid_node [Assemble final output]
      ↓
    make_final_decision_node [Go/no-go decision]
      ├─ approve → end_node → END
      ├─ escalate → end_node → END
      └─ decline → end_node → END
    ```

    Returns:
        Compiled StateGraph instance
    """

    # Create the graph
    workflow = StateGraph(RFPGraphState)

    # ==================== LAYER 1: SALES DISCOVERY ====================
    workflow.add_node("sales_agent", sales_agent_node)
    workflow.add_node("extract_specifications", extract_specifications_node)

    # ==================== LAYER 2: TECHNICAL MATCHING ====================
    workflow.add_node("technical_agent", technical_agent_node)
    workflow.add_node("check_technical_compliance", check_technical_compliance_node)

    # ==================== LAYER 3: PRICING ====================
    workflow.add_node("pricing_agent", pricing_agent_node)
    workflow.add_node("check_pricing_constraints", check_pricing_constraints_node)

    # ==================== LAYER 4: BUSINESS ADVISORY ====================
    workflow.add_node("business_advisory_agent", business_advisory_agent_node)

    # ==================== LAYER 5: ORCHESTRATION ====================
    workflow.add_node("consolidate_bid", consolidate_bid_node)
    workflow.add_node("make_final_decision", make_final_decision_node)
    workflow.add_node("end", end_node)

    # ==================== EDGES: SEQUENTIAL FLOW ====================

    # Start → Sales Discovery
    workflow.add_edge("__start__", "sales_agent")

    # Sales Agent → Specification Extraction
    workflow.add_edge("sales_agent", "extract_specifications")

    # Specification Extraction → Technical Agent (first attempt)
    workflow.add_edge("extract_specifications", "technical_agent")

    # Technical Agent → Compliance Check
    workflow.add_edge("technical_agent", "check_technical_compliance")

    # ==================== CONDITIONAL EDGES: RETRY LOGIC ====================

    def route_technical_compliance(state: RFPGraphState) -> Literal["pricing_agent", "technical_agent", "end"]:
        """
        Route based on technical compliance check.

        Returns:
        - "pricing_agent" if compliant (SMM >= 80% for all lines)
        - "technical_agent" if retry available
        - "end" if max retries exceeded
        """
        result = state.get("status", "")

        # Note: check_technical_compliance_node returns a string
        # We need to check it via the state
        selected_skus = state.get("selected_skus", [])
        retry_count = state.get("tech_retry_count", 0)

        if not selected_skus:
            return "end"

        # Check if all compliant
        all_compliant = all(sku.smm_score >= 80.0 for sku in selected_skus)

        if all_compliant:
            state["technical_compliance_ok"] = True
            return "pricing_agent"

        # Check retry limit
        if retry_count < 3:
            state["tech_retry_count"] = retry_count + 1
            return "technical_agent"

        # Max retries exceeded
        state["technical_compliance_ok"] = False
        return "end"

    workflow.add_conditional_edges(
        "check_technical_compliance",
        route_technical_compliance,
    )

    # Pricing Agent → Pricing Constraints Check
    workflow.add_edge("pricing_agent", "check_pricing_constraints")

    # ==================== CONDITIONAL EDGES: PRICING VALIDATION ====================

    def route_pricing_constraints(state: RFPGraphState) -> Literal["business_advisory_agent", "end"]:
        """
        Route based on pricing constraints.

        Returns:
        - "business_advisory_agent" if constraints met
        - "end" if constraints violated (escalate)
        """
        pricing_results = state.get("pricing_results", [])

        if not pricing_results:
            state["pricing_constraints_met"] = False
            return "end"

        # Basic validation: all positive values
        all_valid = all(pr.grand_total > 0 for pr in pricing_results)

        if all_valid:
            state["pricing_constraints_met"] = True
            return "business_advisory_agent"

        state["pricing_constraints_met"] = False
        return "end"

    workflow.add_conditional_edges(
        "check_pricing_constraints",
        route_pricing_constraints,
    )

    # Business Advisory → Consolidate Bid
    workflow.add_edge("business_advisory_agent", "consolidate_bid")

    # Consolidate Bid → Final Decision
    workflow.add_edge("consolidate_bid", "make_final_decision")

    # ==================== CONDITIONAL EDGES: FINAL DECISION ====================

    def route_final_decision(state: RFPGraphState) -> Literal["end"]:
        """
        Route final decision to end node.

        The decision is already made in make_final_decision_node.
        This just ensures all paths go to end node.

        Returns:
            - "end" (always, as the end node handles the final status)
        """
        return "end"

    workflow.add_conditional_edges(
        "make_final_decision",
        route_final_decision,
    )

    # End Node → END
    workflow.add_edge("end", END)

    # Compile the graph
    compiled_graph = workflow.compile()

    return compiled_graph


# ==================== HELPER: INITIALIZE STATE ====================

def initialize_rfp_state(rfp_data: dict) -> RFPGraphState:
    """
    Create initial RFPGraphState for a new RFP.

    Args:
        rfp_data: Raw RFP dictionary or list

    Returns:
        Initialized RFPGraphState
    """
    return {
        # Input layer
        "rfp_data": [rfp_data] if isinstance(rfp_data, dict) else rfp_data,

        # Sales agent layer
        "qualified_rfp": None,
        "sales_notes": "",

        # Technical agent layer
        "product_specs": [],
        "selected_skus": None,
        "tech_retry_count": 0,
        "tech_retry_logs": [],
        "tech_retry_criteria_relaxation": 0,
        "technical_compliance_ok": False,

        # Pricing agent layer
        "pricing_results": None,
        "pricing_constraints_met": False,
        "pricing_notes": "",
        "lme_rates_snapshot": {},

        # Business advisory layer
        "roi_analysis": None,

        # Output layer
        "consolidated_bid": None,
        "final_decision": None,

        # System layer
        "agent_logs": [],
        "errors": [],
        "status": "initialized",
        "completion_timestamp": None,
    }


# ==================== EXPORT ====================
__all__ = [
    "create_rfp_processing_graph",
    "initialize_rfp_state",
]
