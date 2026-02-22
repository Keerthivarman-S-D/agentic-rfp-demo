"""
Pricing Agent - LME Commodity-Indexed Cost Calculation

Calculates final pricing with:
- LME (London Metal Exchange) commodity indexing
- Testing service and certification costs
- Commercial risk premiums
- Margin optimization
"""

from typing import List, Dict, Any

from backend.state import RFPGraphState, PricingResult, SelectedSKU
from backend.config import settings, create_llm_chain, PRICING_AGENT_SYSTEM_PROMPT
from backend.tools.pricing_lookup_tool import (
    calculate_sku_unit_cost,
    calculate_line_cost,
    get_commodity_prices,
)
from backend.tools.risk_assessment_tool import get_risk_thresholds
from backend.data.models import get_oem_product_by_sku


def create_pricing_agent_chain():
    """Create the pricing agent LLM."""
    return create_llm_chain()


def pricing_agent_node(state: RFPGraphState) -> RFPGraphState:
    """
    Pricing Agent Node - Calculate complete bid pricing with LME indexing.

    This node:
    1. Gets selected SKUs from technical agent
    2. Calculates LME-indexed material costs
    3. Adds testing/certification costs
    4. Applies risk premiums
    5. Returns complete PricingResult per line

    Args:
        state: Current graph state

    Returns:
        Updated state with pricing_results
    """
    try:
        selected_skus = state.get("selected_skus", [])
        rfp_data = state.get("rfp_data", [])
        qualified_rfp = state.get("qualified_rfp")

        if not selected_skus or not rfp_data:
            state["errors"].append("Missing selected SKUs or RFP data for pricing")
            state["status"] = "failed_pricing"
            return state

        # Get RFP details
        rfp = rfp_data[0] if isinstance(rfp_data, list) else rfp_data
        test_requirements = rfp.get("Test_Requirements", [])
        bid_bond_value = rfp.get("Bid_Bond_Value", 0.0)
        include_risk_premium = rfp.get("Bid_Bond_Required", False) or rfp.get("Liquidated_Damages_Clause", False)

        # Calculate pricing for each line
        pricing_results = []
        total_bid_value = 0.0

        for selected_sku in selected_skus:
            try:
                # Get SKU details
                sku_data = get_oem_product_by_sku(selected_sku.sku_id)

                # Find corresponding product spec to get quantity
                matching_spec = None
                for spec in state.get("product_specs", []):
                    if spec.line == selected_sku.line:
                        matching_spec = spec
                        break

                if not matching_spec:
                    state["errors"].append(f"No matching spec for line {selected_sku.line}")
                    continue

                # Calculate line cost
                cost_result = calculate_line_cost(
                    sku_id=selected_sku.sku_id,
                    quantity=matching_spec.quantity,
                    material=sku_data["Material"],
                    metal_weight_kg_km=sku_data["Metal_Weight_kg_km"],
                    test_requirements=test_requirements,
                    include_risk_premium=include_risk_premium,
                    bid_bond_value=bid_bond_value,
                )

                if "error" in cost_result:
                    state["errors"].append(f"Line {selected_sku.line} pricing error: {cost_result['error']}")
                    continue

                # Create PricingResult object
                pricing_result = PricingResult(
                    line=selected_sku.line,
                    sku_id=selected_sku.sku_id,
                    quantity=matching_spec.quantity,
                    material_cost=cost_result["material_cost_total_inr"],
                    labor_cost=0,  # Included in base price
                    services_cost=cost_result["services_cost_inr"],
                    risk_premium=cost_result["risk_premium_inr"],
                    grand_total=cost_result["grand_total_inr"],
                    commodities_used={
                        sku_data["Material"]: cost_result["material_cost_total_inr"]
                    },
                )

                pricing_results.append(pricing_result)
                total_bid_value += pricing_result.grand_total

            except Exception as e:
                state["errors"].append(f"Error pricing line {selected_sku.line}: {str(e)}")

        if not pricing_results:
            state["errors"].append("No valid pricing results calculated")
            state["status"] = "failed_pricing"
            return state

        # Validate margin
        margin_ok = True  # Can add margin validation logic here
        pricing_constraints_met = margin_ok

        state["pricing_results"] = pricing_results
        state["pricing_constraints_met"] = pricing_constraints_met
        state["status"] = "pricing_complete"

        # Store current LME rates for audit trail
        state["lme_rates_snapshot"] = settings.LME_RATES.copy()

        # Log action
        avg_margin = (settings.TARGET_MARGIN - 1) * 100
        state["agent_logs"].append({
            "agent": "Pricing Agent",
            "action": "Calculate LME-Indexed Pricing",
            "result": f"Total bid: ₹{total_bid_value:,.0f}, {len(pricing_results)} lines, Margin: {avg_margin:.0f}%",
        })

        return state

    except Exception as e:
        state["errors"].append(f"Pricing agent error: {str(e)}")
        state["status"] = "failed_pricing"
        return state


def check_pricing_constraints_node(state: RFPGraphState) -> RFPGraphState:
    """
    Check if pricing constraints are met.

    Validates pricing and updates state.
    The actual routing is handled by route_pricing_constraints router function.

    Args:
        state: Current graph state

    Returns:
        Updated state dict
    """
    pricing_results = state.get("pricing_results", [])

    if not pricing_results:
        state["errors"].append("No pricing results available")
        state["pricing_constraints_met"] = False
        return state

    # For MVP, basic validation: all lines have positive totals
    all_valid = all(pr.grand_total > 0 for pr in pricing_results)

    if all_valid:
        state["pricing_constraints_met"] = True
    else:
        state["pricing_constraints_met"] = False
        state["errors"].append("Pricing validation failed: Invalid cost values")

    return state


# ==================== EXPORT ====================
__all__ = [
    "create_pricing_agent_chain",
    "pricing_agent_node",
    "check_pricing_constraints_node",
]
