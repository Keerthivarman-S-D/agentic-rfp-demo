"""
Pricing Lookup Tool - Cost Calculation and LME Commodity Indexing

Enables the Pricing Agent to calculate product costs based on:
- Base SKU prices
- LME (London Metal Exchange) commodity rates
- Testing/certification requirements
- Commercial risk premiums
"""

from typing import Dict, Any, List

from backend.config import settings, get_lme_rate, get_test_cost
from backend.data.models import get_oem_product_by_sku


def calculate_sku_unit_cost(
    sku_id: str,
    material: str,
    metal_weight_kg_km: float,
) -> Dict[str, float]:
    """
    Calculate unit cost for a SKU with LME commodity indexing.

    Uses London Metal Exchange (LME) rates to price conductor materials.
    Formula: Unit Cost = Base Price + (Metal Weight/1000) × LME Rate × Currency Conversion

    Args:
        sku_id: SKU identifier
        material: Material type (Copper, Aluminium)
        metal_weight_kg_km: Metal weight in kg per km

    Returns:
        Dictionary with cost components:
        - base_price: Fixed manufacturing cost (INR/meter)
        - metal_cost_per_m: Material cost per meter based on LME (INR/meter)
        - unit_cost: Total cost per meter (INR/meter)
        - unit_price: Final price with margin applied (INR/meter)

    Example:
        >>> result = calculate_sku_unit_cost(
        ...     sku_id="OEM-XLPE-4C-95",
        ...     material="Copper",
        ...     metal_weight_kg_km=380
        ... )
        >>> print(f"Unit price: ₹{result['unit_price']}")
    """
    try:
        # Get product base price
        product = get_oem_product_by_sku(sku_id)
        base_price = product["Base_Price"]

        # Get LME rate for material
        lme_rate_usd_mt = get_lme_rate(material)

        # Calculate metal cost per meter
        # Formula: (weight_kg/km ÷ 1000) × LME_rate_usd × USD_to_INR
        metal_cost_per_m = (metal_weight_kg_km / 1000) * (lme_rate_usd_mt / 1000) * settings.USD_TO_INR_RATE

        # Total unit cost before margin
        unit_cost = base_price + metal_cost_per_m

        # Apply target margin
        unit_price = unit_cost * settings.TARGET_MARGIN

        return {
            "sku": sku_id,
            "base_price": base_price,
            "lme_rate_usd_mt": lme_rate_usd_mt,
            "metal_weight_kg_km": metal_weight_kg_km,
            "metal_cost_per_m": round(metal_cost_per_m, 2),
            "unit_cost": round(unit_cost, 2),
            "unit_price": round(unit_price, 2),
            "margin_percent": round((settings.TARGET_MARGIN - 1) * 100, 1),
        }

    except ValueError as e:
        return {"error": f"SKU not found: {str(e)}"}
    except Exception as e:
        return {"error": f"Cost calculation failed: {str(e)}"}


def calculate_line_cost(
    sku_id: str,
    quantity: int,
    material: str,
    metal_weight_kg_km: float,
    test_requirements: List[str] = None,
    include_risk_premium: bool = False,
    bid_bond_value: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculate total cost for an RFP line item.

    Includes:
    - Material cost (LME-indexed) × quantity
    - Testing/certification costs
    - Risk premiums if required

    Args:
        sku_id: SKU identifier
        quantity: Quantity in meters
        material: Material type
        metal_weight_kg_km: Metal weight
        test_requirements: List of required tests/certifications
        include_risk_premium: Add commercial risk premium
        bid_bond_value: Bid bond amount (for risk calculation)

    Returns:
        Dictionary with:
        - unit_price: Price per meter
        - material_cost_total: Material cost × quantity
        - services_cost: Testing + certifications
        - risk_premium: Commercial risk margin
        - grand_total: Complete line cost
    """
    try:
        # Get unit cost
        unit_cost_dict = calculate_sku_unit_cost(sku_id, material, metal_weight_kg_km)
        if "error" in unit_cost_dict:
            return unit_cost_dict

        unit_price = unit_cost_dict["unit_price"]
        material_cost_total = unit_price * quantity

        # Calculate service costs
        services_cost = 0.0
        service_items = []

        if test_requirements:
            for test in test_requirements:
                cost = get_test_cost(test)
                services_cost += cost
                service_items.append(f"{test}: ₹{cost:,.0f}")

        # Add risk premium if applicable
        risk_premium = 0.0
        if include_risk_premium and bid_bond_value > 0:
            # 2% of bid bond as risk premium
            risk_premium = bid_bond_value * 0.02

        grand_total = material_cost_total + services_cost + risk_premium

        return {
            "sku": sku_id,
            "unit_price_inr_m": round(unit_price, 2),
            "quantity_m": quantity,
            "material_cost_total_inr": round(material_cost_total, 2),
            "services_cost_inr": round(services_cost, 2),
            "service_items": service_items,
            "risk_premium_inr": round(risk_premium, 2),
            "grand_total_inr": round(grand_total, 2),
        }

    except Exception as e:
        return {"error": f"Line cost calculation failed: {str(e)}"}


def get_commodity_prices() -> Dict[str, Any]:
    """
    Return current LME commodity rates used for pricing.

    Returns:
        Dictionary mapping materials to prices (USD/MT)
    """
    try:
        return {
            "timestamp": "Current cached rates",
            "rates": settings.LME_RATES,
            "currency_conversion": f"USD to INR: {settings.USD_TO_INR_RATE}",
            "note": "Rates are cached; update via update_commodity_prices endpoint",
        }
    except Exception as e:
        return {"error": f"Failed to retrieve commodity prices: {str(e)}"}


def update_commodity_price(material: str, new_rate_usd_mt: float) -> Dict[str, Any]:
    """
    Update LME commodity rate (admin function).

    Used to refresh commodity pricing when market rates change.

    Args:
        material: Material name (Copper, Aluminium)
        new_rate_usd_mt: New price in USD/MT

    Returns:
        Confirmation of price update
    """
    try:
        old_rate = settings.LME_RATES.get(material)
        if old_rate is None:
            return {"error": f"Unknown material: {material}"}

        settings.LME_RATES[material] = new_rate_usd_mt
        percent_change = ((new_rate_usd_mt - old_rate) / old_rate) * 100

        return {
            "material": material,
            "old_rate_usd_mt": old_rate,
            "new_rate_usd_mt": new_rate_usd_mt,
            "change_percent": round(percent_change, 2),
            "status": "Updated successfully",
        }

    except Exception as e:
        return {"error": f"Failed to update commodity price: {str(e)}"}


# ==================== EXPORT ====================
__all__ = [
    "calculate_sku_unit_cost",
    "calculate_line_cost",
    "get_commodity_prices",
    "update_commodity_price",
]
