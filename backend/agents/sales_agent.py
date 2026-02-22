"""
Sales Discovery Agent

Responsible for scanning RFP opportunities, qualifying leads, and calculating
commercial risk scores. Acts as Chief Market Intelligence Officer.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain.tools import ToolException

from backend.state import RFPGraphState, QualifiedRFP, ProductSpecification
from backend.config import settings, create_llm_chain, SALES_AGENT_SYSTEM_PROMPT
from backend.tools.risk_assessment_tool import assess_rfp_risk


def create_sales_agent_chain():
    """
    Create the sales discovery agent using LangChain.

    Returns:
        LLM instance configured for sales responsibilities (Gemini/Claude/OpenAI)
    """
    return create_llm_chain()


def sales_agent_node(state: RFPGraphState) -> RFPGraphState:
    """
    Sales Discovery Agent Node - Qualifies RFPs and calculates risk.

    This node:
    1. Qualifies the RFP based on timeline (within 90-day window)
    2. Calculates commercial risk score (1-10)
    3. Extracts metadata and constraints
    4. Returns QualifiedRFP object or marks for escalation

    Args:
        state: Current graph state

    Returns:
        Updated state with qualified_rfp and sales_notes
    """
    try:
        # Extract RFP from input
        rfp_data = state.get("rfp_data", [])
        if not rfp_data:
            state["errors"].append("No RFP data provided")
            state["status"] = "failed_sales_screening"
            return state

        # For MVP, work with first RFP in list
        rfp = rfp_data[0] if isinstance(rfp_data, list) else rfp_data

        # Validate RFP structure
        required_fields = ["ID", "Title", "Client_Name", "Due_Date", "Products", "Test_Requirements"]
        missing_fields = [f for f in required_fields if f not in rfp]
        if missing_fields:
            state["errors"].append(f"RFP missing fields: {missing_fields}")
            state["status"] = "failed_sales_screening"
            return state

        # Parse due date
        try:
            due_date_str = rfp["Due_Date"]
            if isinstance(due_date_str, str):
                due_datetime = datetime.fromisoformat(due_date_str)
            else:
                due_datetime = due_date_str
            due_date_str = due_datetime.isoformat()
        except Exception as e:
            state["errors"].append(f"Invalid due date: {str(e)}")
            state["status"] = "failed_sales_screening"
            return state

        # Assess risk using tool
        risk_result = assess_rfp_risk(
            due_date=due_date_str,
            bid_bond_required=rfp.get("Bid_Bond_Required", False),
            liquidated_damages_clause=rfp.get("Liquidated_Damages_Clause", False),
            performance_bond_percent=rfp.get("Performance_Bond_Percent", 0.0),
        )

        if "error" in risk_result:
            state["errors"].append(risk_result["error"])
            state["status"] = "failed_sales_screening"
            return state

        risk_score = risk_result["risk_score"]
        days_remaining = risk_result["days_to_deadline"]

        # Qualification decision
        is_qualified = (
            0 <= days_remaining <= settings.RFP_QUALIFICATION_WINDOW_DAYS
            and risk_score <= 7
        )

        # Create QualifiedRFP object
        qualified_rfp = QualifiedRFP(
            id=rfp["ID"],
            title=rfp["Title"],
            client_name=rfp["Client_Name"],
            due_date=due_date_str,
            risk_score=risk_score,
            priority=risk_result.get("risk_level", "MEDIUM"),
            bid_bond_required=rfp.get("Bid_Bond_Required", False),
            bid_bond_value=rfp.get("Bid_Bond_Value", 0.0),
            performance_bond_percent=rfp.get("Performance_Bond_Percent", 0.0),
            test_requirements=rfp.get("Test_Requirements", []),
            liquidated_damages_clause=rfp.get("Liquidated_Damages_Clause", False),
        )

        # Build sales notes
        sales_notes = f"""
        Sales Agent Analysis:
        - RFP ID: {rfp["ID"]}
        - Client: {rfp["Client_Name"]}
        - Due Date: {due_date_str} ({days_remaining} days remaining)
        - Risk Score: {risk_score}/10
        - Risk Level: {risk_result['risk_level']}
        - Qualification Status: {'QUALIFIED' if is_qualified else 'DECLINED'}
        - Risk Factors: {', '.join(risk_result['risk_factors'])}
        - Recommendation: {risk_result['recommendation']}
        """

        # Log action
        state["agent_logs"].append({
            "agent": "Sales Agent",
            "action": f"Qualified RFP {rfp['ID']}",
            "result": f"Risk Score: {risk_score}/10, Status: {'QUALIFIED' if is_qualified else 'DECLINED'}",
        })

        # Update state
        state["qualified_rfp"] = qualified_rfp
        state["sales_notes"] = sales_notes.strip()
        state["status"] = "sales_screening_complete"

        return state

    except Exception as e:
        state["errors"].append(f"Sales agent error: {str(e)}")
        state["status"] = "failed_sales_screening"
        return state


def extract_specifications_node(state: RFPGraphState) -> RFPGraphState:
    """
    Extract ProductSpecifications from the RFP for technical matching.

    This node:
    1. Parses product line items from RFP
    2. Creates ProductSpecification objects
    3. Validates technical requirements

    Args:
        state: Current graph state

    Returns:
        Updated state with product_specs
    """
    try:
        rfp = state.get("qualified_rfp")
        if not rfp:
            state["errors"].append("No qualified RFP found")
            state["status"] = "failed_spec_extraction"
            return state

        # Extract product specs from RFP data
        rfp_data = state.get("rfp_data", [])
        if not rfp_data:
            state["errors"].append("No RFP data available for spec extraction")
            state["status"] = "failed_spec_extraction"
            return state

        rfp_dict = rfp_data[0] if isinstance(rfp_data, list) else rfp_data
        products = rfp_dict.get("Products", [])

        product_specs = []
        for product in products:
            try:
                spec = ProductSpecification(
                    line=product.get("Line", 0),
                    quantity=product.get("Quantity", 0),
                    req_material=product.get("Req_Material", ""),
                    req_insulation=product.get("Req_Insulation", ""),
                    req_cores=product.get("Req_Cores", 0),
                    req_size_mm2=product.get("Req_Size_mm2", 0),
                    req_voltage_kv=product.get("Req_Voltage_kV", 0.0),
                )
                product_specs.append(spec)
            except Exception as e:
                state["errors"].append(f"Error parsing product spec {product.get('Line', '?')}: {str(e)}")

        if not product_specs:
            state["errors"].append("No valid product specifications extracted")
            state["status"] = "failed_spec_extraction"
            return state

        state["product_specs"] = product_specs
        state["status"] = "specifications_extracted"

        # Log
        state["agent_logs"].append({
            "agent": "Sales Agent",
            "action": "Extract Specifications",
            "result": f"Extracted {len(product_specs)} product lines",
        })

        return state

    except Exception as e:
        state["errors"].append(f"Specification extraction error: {str(e)}")
        state["status"] = "failed_spec_extraction"
        return state


# ==================== EXPORT ====================
__all__ = [
    "create_sales_agent_chain",
    "sales_agent_node",
    "extract_specifications_node",
]
