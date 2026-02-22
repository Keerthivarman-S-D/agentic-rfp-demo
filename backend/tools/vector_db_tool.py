"""
Vector Database Tool - FAISS-based Similarity Search

Enables the Technical Agent to find matching OEM SKUs based on product specifications
using semantic similarity search (FAISS/sentence-transformers).
"""

from typing import List, Dict, Any, Optional

from backend.data.embeddings_cache import search_vector_db


def vector_db_tool(
    material: Optional[str] = None,
    insulation: Optional[str] = None,
    cores: Optional[int] = None,
    size_mm2: Optional[int] = None,
    voltage_kv: Optional[float] = None,
    k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search OEM datasheet repository for matching cable SKUs using FAISS similarity search.

    This tool enables content-based product matching. It takes product specifications
    and returns the top-k most similar OEM SKUs ranked by match score.

    Args:
        material: Required conductor material (e.g., "Copper", "Aluminium")
        insulation: Required insulation type (e.g., "XLPE", "PVC")
        cores: Number of cores required
        size_mm2: Cross-section area in mm²
        voltage_kv: Rated voltage in kV
        k: Number of results to return (default: 5)

    Returns:
        List of matched SKUs, each with:
        - sku: SKU identifier
        - similarity: Match score (0-100% if fuzzy, 0-1 if FAISS)
        - product: Full product details (material, cores, price, etc.)
        - match_reason: Explanation of why this match was selected

    Example:
        >>> results = vector_db_tool(
        ...     material="Copper",
        ...     insulation="XLPE",
        ...     cores=4,
        ...     size_mm2=95,
        ...     voltage_kv=1.1
        ... )
        >>> for result in results:
        ...     print(f"{result['sku']}: {result['similarity']}% match")

    Notes:
        - If FAISS is available, uses semantic embeddings
        - Falls back to attribute-based fuzzy matching if FAISS unavailable
        - Returns empty list if search fails
    """
    try:
        results = search_vector_db(
            req_material=material,
            req_insulation=insulation,
            req_cores=cores,
            req_size_mm2=size_mm2,
            req_voltage_kv=voltage_kv,
            k=k,
        )

        # Format results for clarity
        formatted_results = []
        for result in results[:k]:
            formatted_results.append(
                {
                    "sku": result["sku"],
                    "similarity": result["similarity"],
                    "material": result["product"]["Material"],
                    "insulation": result["product"]["Insulation"],
                    "cores": result["product"]["Cores"],
                    "size_mm2": result["product"]["Size_mm2"],
                    "voltage_kv": result["product"]["Voltage_kV"],
                    "base_price": result["product"]["Base_Price"],
                    "certifications": result["product"]["Test_Cert"],
                    "match_reason": result["match_reason"],
                }
            )

        return formatted_results

    except Exception as e:
        return [{"error": f"Vector DB search failed: {str(e)}"}]


def get_sku_details(sku_id: str) -> Dict[str, Any]:
    """
    Retrieve full details for a specific SKU.

    Args:
        sku_id: SKU identifier (e.g., "OEM-XLPE-4C-95")

    Returns:
        Dictionary with complete SKU specifications:
        - Material, cores, size, voltage, certifications
        - Pricing, weight, test requirements

    Raises:
        Returns error dict if SKU not found
    """
    try:
        from backend.data.models import get_oem_product_by_sku

        product = get_oem_product_by_sku(sku_id)
        return {
            "sku": product["SKU"],
            "description": product["Description"],
            "material": product["Material"],
            "insulation": product["Insulation"],
            "cores": product["Cores"],
            "size_mm2": product["Size_mm2"],
            "voltage_kv": product["Voltage_kV"],
            "base_price": product["Base_Price"],
            "metal_weight_kg_km": product["Metal_Weight_kg_km"],
            "certifications": product["Test_Cert"],
        }
    except ValueError as e:
        return {"error": str(e)}
    except Exception as e:
        return {"error": f"Failed to retrieve SKU details: {str(e)}"}


# ==================== EXPORT ====================
__all__ = [
    "vector_db_tool",
    "get_sku_details",
]
