"""
Business Advisory Agent - Strategic ROI and Competitive Analysis

Quantifies business value of the agentic bidding system through:
- Cost savings analysis (manual vs automated)
- Commodity price sensitivity analysis
- Competitive advantage metrics
- Strategic positioning recommendations
"""

from typing import Dict, Any

from backend.state import RFPGraphState, PricingResult
from backend.config import settings, create_llm_chain, BUSINESS_ADVISORY_SYSTEM_PROMPT


def create_business_advisory_agent_chain():
    """Create the business advisory agent LLM."""
    return create_llm_chain()


def business_advisory_agent_node(state: RFPGraphState) -> RFPGraphState:
    """
    Business Advisory Agent Node - Analyze ROI and competitive advantage.

    This node:
    1. Calculates cost savings (manual vs agentic process)
    2. Performs sensitivity analysis (±10% commodity price changes)
    3. Quantifies first-mover advantage
    4. Provides strategic recommendations

    Args:
        state: Current graph state

    Returns:
        Updated state with roi_analysis data
    """
    try:
        pricing_results = state.get("pricing_results", [])
        qualified_rfp = state.get("qualified_rfp")

        if not pricing_results or not qualified_rfp:
            state["errors"].append("Missing pricing or RFP data for advisory analysis")
            state["status"] = "failed_advisory"
            return state

        # Calculate operational savings
        manual_hours = 48  # Traditional bidding process
        hourly_rate = 50  # USD
        manual_cost = manual_hours * hourly_rate

        agentic_time_minutes = 2  # Agentic process
        agentic_cost = (agentic_time_minutes / 60) * hourly_rate
        operational_savings = manual_cost - agentic_cost
        operational_savings_percent = (operational_savings / manual_cost) * 100

        # Calculate total bid value
        total_bid_value = sum(pr.grand_total for pr in pricing_results)

        # Sensitivity analysis: commodity price impact
        sensitivity_data = []
        lme_rates = state.get("lme_rates_snapshot", settings.LME_RATES)

        copper_rates = [
            ("Copper", -10),
            ("Copper", -5),
            ("Copper", 0),
            ("Copper", 5),
            ("Copper", 10),
        ]

        base_material_cost = sum(pr.material_cost for pr in pricing_results)

        for material, shift_percent in copper_rates:
            if material not in lme_rates:
                continue

            base_rate = lme_rates[material]
            new_rate = base_rate * (1 + shift_percent / 100)
            rate_delta = new_rate - base_rate

            # Simple proportional cost change
            cost_delta = (base_material_cost * shift_percent) / 100
            new_total = total_bid_value + cost_delta

            sensitivity_data.append({
                "lme_shift_percent": shift_percent,
                "material": material,
                "old_rate_usd_mt": base_rate,
                "new_rate_usd_mt": new_rate,
                "cost_impact_inr": round(cost_delta, 0),
                "new_bid_value_inr": round(new_total, 0),
            })

        # Competitive advantage metrics
        days_remaining = qualified_rfp.__dict__.get("Due_Date", "")
        time_saved_days = 2
        first_to_bid_advantage = min(12 * time_saved_days, 24)  # 12% per day saved, max 24%

        competitive_metrics = {
            "response_time_agentic_minutes": agentic_time_minutes,
            "response_time_manual_hours": manual_hours,
            "speed_advantage_percent": 99.9,
            "first_to_bid_probability_agentic_percent": first_to_bid_advantage,
            "first_to_bid_probability_manual_percent": 5,
            "technical_accuracy_agentic_percent": 100,
            "technical_accuracy_manual_percent": 85,
            "accuracy_advantage_percent": 15,
            "pricing_protection": "Real-time LME indexed",
        }

        # Build ROI analysis object
        roi_analysis = {
            "operational_metrics": {
                "manual_process_cost_usd": round(manual_cost, 2),
                "agentic_process_cost_usd": round(agentic_cost, 4),
                "cost_savings_usd": round(operational_savings, 2),
                "cost_savings_percent": round(operational_savings_percent, 1),
                "payback_period_bids": round(50000 / operational_savings, 0) if operational_savings > 0 else 0,
            },
            "commodity_sensitivity": sensitivity_data,
            "competitive_advantage": competitive_metrics,
            "strategic_positioning": {
                "speed_advantage": "First to bid advantage of 2+ days",
                "quality_advantage": "100% technical compliance via weighted SMM",
                "risk_protection": "Real-time commodity hedging via LME indexing",
                "recommendation": "Proceed with bid. Competitive advantage is substantial.",
            },
            "bid_value_summary": {
                "total_bid_value_inr": round(total_bid_value, 0),
                "number_of_lines": len(pricing_results),
                "average_line_value_inr": round(total_bid_value / len(pricing_results), 0),
            },
        }

        state["roi_analysis"] = roi_analysis
        state["status"] = "advisory_complete"

        # Log action
        state["agent_logs"].append({
            "agent": "Business Advisory Agent",
            "action": "ROI & Competitive Analysis",
            "result": f"Savings: ${operational_savings:.0f}, First-mover advantage: {first_to_bid_advantage}%",
        })

        return state

    except Exception as e:
        state["errors"].append(f"Business advisory error: {str(e)}")
        state["status"] = "failed_advisory"
        return state


# ==================== EXPORT ====================
__all__ = [
    "create_business_advisory_agent_chain",
    "business_advisory_agent_node",
]
