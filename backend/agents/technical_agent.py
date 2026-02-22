"""
Technical Agent - SMM Calculation and SKU Matching

Calculates Spec Match Metric (SMM) for product specifications against OEM
catalog using FAISS vector similarity search. Implements retry logic for
non-compliant matches.
"""

from typing import List, Dict, Any

from backend.state import RFPGraphState, ProductSpecification, SelectedSKU
from backend.config import settings, create_llm_chain, TECHNICAL_AGENT_SYSTEM_PROMPT
from backend.tools.vector_db_tool import vector_db_tool
from backend.data.models import get_oem_product_by_sku


def create_technical_agent_chain():
    """Create the technical agent LLM."""
    return create_llm_chain()


def calculate_smm_weighted(
    req_material: str,
    req_insulation: str,
    req_cores: int,
    req_size_mm2: int,
    sku_data: Dict[str, Any],
    size_tolerance: float = 0.0,
) -> tuple:
    """
    Calculate weighted Spec Match Metric (SMM).

    Weights:
    - Material: 30% (exact match only)
    - Cores: 25% (exact match only)
    - Size: 25% (SKU >= requirement, with tolerance relaxation)
    - Insulation: 20% (exact match only)

    Args:
        req_material: Required material
        req_insulation: Required insulation
        req_cores: Required cores
        req_size_mm2: Required size
        sku_data: SKU product data
        size_tolerance: Additional tolerance for size matching (mm²)

    Returns:
        Tuple of (smm_score, breakdown_dict)
    """
    weights = {
        "Material": 0.30,
        "Cores": 0.25,
        "Size_mm2": 0.25,
        "Insulation": 0.20,
    }

    breakdown = {}
    total_smm = 0.0

    # Material match (30%)
    material_match = 1.0 if sku_data.get("Material") == req_material else 0.0
    material_score = material_match * weights["Material"] * 100
    breakdown["Material"] = {
        "match": material_match,
        "score": material_score,
        "weight": weights["Material"],
    }
    total_smm += material_score

    # Cores match (25%)
    cores_match = 1.0 if sku_data.get("Cores") == req_cores else 0.0
    cores_score = cores_match * weights["Cores"] * 100
    breakdown["Cores"] = {
        "match": cores_match,
        "score": cores_score,
        "weight": weights["Cores"],
    }
    total_smm += cores_score

    # Size match - meet or exceed (25%)
    sku_size = sku_data.get("Size_mm2", 0)
    size_match = 1.0 if sku_size >= (req_size_mm2 - size_tolerance) else 0.0
    size_score = size_match * weights["Size_mm2"] * 100
    breakdown["Size_mm2"] = {
        "match": size_match,
        "score": size_score,
        "weight": weights["Size_mm2"],
        "detail": f"{sku_size}mm² vs {req_size_mm2}mm² (tolerance: {size_tolerance}mm²)",
    }
    total_smm += size_score

    # Insulation match (20%)
    insulation_match = 1.0 if sku_data.get("Insulation") == req_insulation else 0.0
    insulation_score = insulation_match * weights["Insulation"] * 100
    breakdown["Insulation"] = {
        "match": insulation_match,
        "score": insulation_score,
        "weight": weights["Insulation"],
    }
    total_smm += insulation_score

    return round(total_smm, 2), breakdown


def technical_agent_node(state: RFPGraphState) -> RFPGraphState:
    """
    Technical Agent Node - Match product specs to SKUs using SMM.

    This node:
    1. Searches OEM catalog for matching SKUs (FAISS similarity search)
    2. Calculates SMM for each candidate
    3. Selects best match
    4. Logs retry info if applicable

    Args:
        state: Current graph state

    Returns:
        Updated state with selected_skus or retry_needed flag
    """
    try:
        product_specs = state.get("product_specs", [])
        if not product_specs:
            state["errors"].append("No product specifications found")
            state["status"] = "failed_technical_matching"
            return state

        # Get retry attempt number and relaxation setting
        retry_count = state.get("tech_retry_count", 0)
        size_tolerance = state.get("tech_retry_criteria_relaxation", 0)

        # Progressive relaxation strategy (retry logic)
        if retry_count == 0:
            # First attempt: exact matching
            size_tolerance = 0
        elif retry_count == 1:
            # Second attempt: relax size by 10mm²
            size_tolerance = settings.SIZE_TOLERANCE_RELAXATION
        elif retry_count >= 2:
            # Third attempt: further relaxation
            size_tolerance = settings.SIZE_TOLERANCE_RELAXATION * 2

        selected_skus = []
        retry_log_entries = []

        for spec in product_specs:
            # Search vector DB for similar products
            search_results = vector_db_tool(
                material=spec.req_material,
                insulation=spec.req_insulation,
                cores=spec.req_cores,
                size_mm2=spec.req_size_mm2,
                voltage_kv=spec.req_voltage_kv,
                k=5,
            )

            if not search_results or "error" in search_results[0]:
                state["errors"].append(f"Vector DB search failed for line {spec.line}")
                continue

            # Evaluate matches with SMM
            best_match = None
            best_smm = 0

            for search_result in search_results:
                sku_id = search_result.get("sku")
                try:
                    sku_data = get_oem_product_by_sku(sku_id)
                    smm_score, breakdown = calculate_smm_weighted(
                        req_material=spec.req_material,
                        req_insulation=spec.req_insulation,
                        req_cores=spec.req_cores,
                        req_size_mm2=spec.req_size_mm2,
                        sku_data=sku_data,
                        size_tolerance=size_tolerance,
                    )

                    if smm_score > best_smm:
                        best_smm = smm_score
                        best_match = {
                            "sku_id": sku_id,
                            "sku_data": sku_data,
                            "smm_score": smm_score,
                            "breakdown": breakdown,
                        }
                except Exception as e:
                    state["errors"].append(f"Error evaluating SKU {sku_id}: {str(e)}")

            if best_match:
                selected_sku = SelectedSKU(
                    line=spec.line,
                    sku_id=best_match["sku_id"],
                    smm_score=best_match["smm_score"],
                    smm_breakdown=best_match["breakdown"],
                    retry_count=retry_count,
                    matched_specs={
                        "material": best_match["sku_data"].get("Material"),
                        "insulation": best_match["sku_data"].get("Insulation"),
                        "cores": best_match["sku_data"].get("Cores"),
                        "size_mm2": best_match["sku_data"].get("Size_mm2"),
                        "voltage_kv": best_match["sku_data"].get("Voltage_kV"),
                    },
                )
                selected_skus.append(selected_sku)

                retry_log_entries.append(
                    f"Line {spec.line}: {best_match['sku_id']} (SMM: {best_match['smm_score']}%, Attempt: {retry_count + 1})"
                )
            else:
                state["errors"].append(f"No matching SKU found for line {spec.line}")

        state["selected_skus"] = selected_skus if selected_skus else None
        state["tech_retry_logs"].extend(retry_log_entries)
        state["status"] = "technical_matching_complete"

        # Log action
        state["agent_logs"].append({
            "agent": "Technical Agent",
            "action": f"SMM Matching (Attempt {retry_count + 1})",
            "result": f"Selected {len(selected_skus)} SKUs with avg SMM: {sum(s.smm_score for s in selected_skus) / len(selected_skus):.1f}%" if selected_skus else "No matches",
        })

        return state

    except Exception as e:
        state["errors"].append(f"Technical agent error: {str(e)}")
        state["status"] = "failed_technical_matching"
        return state


def check_technical_compliance_node(state: RFPGraphState) -> RFPGraphState:
    """
    Check if technical compliance is met (all SKUs >= 80% SMM).

    This node validates compliance and updates state.
    The actual routing is handled by route_technical_compliance router function.

    Args:
        state: Current graph state

    Returns:
        Updated state dict
    """
    selected_skus = state.get("selected_skus", [])

    if not selected_skus:
        state["errors"].append("No SKUs selected")
        state["technical_compliance_ok"] = False
        return state

    # Check if all SKUs meet threshold
    all_compliant = all(sku.smm_score >= settings.SMM_COMPLIANCE_THRESHOLD for sku in selected_skus)

    if all_compliant:
        state["technical_compliance_ok"] = True
    else:
        # Check if retries remaining
        retry_count = state.get("tech_retry_count", 0)
        if retry_count >= settings.TECHNICAL_MAX_RETRIES:
            state["technical_compliance_ok"] = False
            state["errors"].append(f"Technical compliance failed after {retry_count} attempts")
        # else: let router handle retry logic

    return state


# ==================== EXPORT ====================
__all__ = [
    "create_technical_agent_chain",
    "technical_agent_node",
    "check_technical_compliance_node",
    "calculate_smm_weighted",
]
