"""
Data Models - OEM Products, RFP Samples, and Data Structures

Contains the synthetic data repository (OEM products, pricing, certifications, RFPs)
for the MVP. In production, this would be replaced with database queries.
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import json

# ==================== OEM PRODUCT CATALOG ====================
# Real-world cable specifications with pricing and certifications

OEM_PRODUCTS: List[Dict[str, Any]] = [
    {
        "SKU": "OEM-XLPE-4C-70",
        "Description": "4-Core Copper XLPE Insulated Cable 70mm² 1.1kV",
        "Material": "Copper",
        "Insulation": "XLPE",
        "Cores": 4,
        "Size_mm2": 70,
        "Voltage_kV": 1.1,
        "Test_Cert": ["IS-1554", "IEC-60502"],
        "Base_Price": 800,  # INR per meter
        "Metal_Weight_kg_km": 280,  # kg per km
    },
    {
        "SKU": "OEM-PVC-3C-95",
        "Description": "3-Core Aluminium PVC Insulated Cable 95mm² 3.3kV",
        "Material": "Aluminium",
        "Insulation": "PVC",
        "Cores": 3,
        "Size_mm2": 95,
        "Voltage_kV": 3.3,
        "Test_Cert": ["IS-7098"],
        "Base_Price": 600,
        "Metal_Weight_kg_km": 220,
    },
    {
        "SKU": "OEM-XLPE-4C-95",
        "Description": "4-Core Copper XLPE Insulated Cable 95mm² 1.1kV (PREMIUM MATCH)",
        "Material": "Copper",
        "Insulation": "XLPE",
        "Cores": 4,
        "Size_mm2": 95,
        "Voltage_kV": 1.1,
        "Test_Cert": ["IS-1554", "IEC-60502"],
        "Base_Price": 1000,
        "Metal_Weight_kg_km": 380,
    },
    {
        "SKU": "OEM-PVC-4C-50",
        "Description": "4-Core Copper PVC Insulated Cable 50mm² 0.66kV",
        "Material": "Copper",
        "Insulation": "PVC",
        "Cores": 4,
        "Size_mm2": 50,
        "Voltage_kV": 0.66,
        "Test_Cert": ["IS-7098"],
        "Base_Price": 500,
        "Metal_Weight_kg_km": 200,
    },
    {
        "SKU": "OEM-XLPE-3C-70",
        "Description": "3-Core Aluminium XLPE Insulated Cable 70mm² 3.3kV",
        "Material": "Aluminium",
        "Insulation": "XLPE",
        "Cores": 3,
        "Size_mm2": 70,
        "Voltage_kV": 3.3,
        "Test_Cert": ["IS-7098", "IEC-60502"],
        "Base_Price": 750,
        "Metal_Weight_kg_km": 180,
    },
    {
        "SKU": "OEM-BEST-MATCH",
        "Description": "4-Core Copper XLPE Insulated Cable 120mm² 1.1kV (PREMIUM UL CERTIFIED)",
        "Material": "Copper",
        "Insulation": "XLPE",
        "Cores": 4,
        "Size_mm2": 120,
        "Voltage_kV": 1.1,
        "Test_Cert": ["IS-1554", "IEC-60502", "UL"],
        "Base_Price": 1200,
        "Metal_Weight_kg_km": 480,
    },
]


# ==================== SAMPLE RFP DATA ====================
# Real-world RFP examples for testing

TODAY = datetime.now().date()

RFP_DATA: List[Dict[str, Any]] = [
    {
        "ID": "RFP-GOV-2025-001",
        "Title": "Infrastructure Project Phase III Cable Supply",
        "Client_Name": "State Infrastructure Authority",
        "Due_Date": (TODAY + timedelta(days=75)).isoformat(),
        "Products": [
            {
                "Line": 1,
                "Quantity": 5000,
                "Req_Material": "Copper",
                "Req_Insulation": "XLPE",
                "Req_Cores": 4,
                "Req_Size_mm2": 95,
                "Req_Voltage_kV": 1.1,
            },
            {
                "Line": 2,
                "Quantity": 2000,
                "Req_Material": "Aluminium",
                "Req_Insulation": "PVC",
                "Req_Cores": 3,
                "Req_Size_mm2": 70,
                "Req_Voltage_kV": 3.3,
            },
        ],
        "Test_Requirements": [
            "High Voltage Dielectric Test",
            "Conductor Resistance Check",
            "Site Acceptance Test (SAT)",
        ],
        "Bid_Bond_Required": True,
        "Bid_Bond_Value": 500000,
        "Liquidated_Damages_Clause": True,
        "Performance_Bond_Percent": 10,
    },
    {
        "ID": "RFP-PSU-2025-002",
        "Title": "New Substation Power Line Supply",
        "Client_Name": "Power Utility Corporation",
        "Due_Date": (TODAY + timedelta(days=120)).isoformat(),
        "Products": [
            {
                "Line": 1,
                "Quantity": 8000,
                "Req_Material": "Copper",
                "Req_Insulation": "PVC",
                "Req_Cores": 4,
                "Req_Size_mm2": 50,
                "Req_Voltage_kV": 0.66,
            },
        ],
        "Test_Requirements": ["Fire Resistance Test", "UL Certification"],
        "Bid_Bond_Required": False,
        "Bid_Bond_Value": 0,
        "Liquidated_Damages_Clause": False,
        "Performance_Bond_Percent": 5,
    },
]


# ==================== HELPER FUNCTIONS ====================

def get_oem_product_by_sku(sku_id: str) -> Dict[str, Any]:
    """
    Retrieve OEM product details by SKU ID.

    Args:
        sku_id: SKU identifier

    Returns:
        Product dictionary

    Raises:
        ValueError: If SKU not found
    """
    for product in OEM_PRODUCTS:
        if product["SKU"] == sku_id:
            return product
    raise ValueError(f"SKU not found: {sku_id}")


def get_all_skus() -> List[str]:
    """Get all available SKU IDs."""
    return [p["SKU"] for p in OEM_PRODUCTS]


def get_skus_by_material(material: str) -> List[Dict[str, Any]]:
    """Get all SKUs made with a specific material."""
    return [p for p in OEM_PRODUCTS if p["Material"] == material]


def get_skus_by_insulation(insulation: str) -> List[Dict[str, Any]]:
    """Get all SKUs with a specific insulation type."""
    return [p for p in OEM_PRODUCTS if p["Insulation"] == insulation]


def get_skus_by_cores_and_voltage(cores: int, voltage_kv: float) -> List[Dict[str, Any]]:
    """Get all SKUs matching core count and voltage."""
    return [p for p in OEM_PRODUCTS if p["Cores"] == cores and p["Voltage_kV"] == voltage_kv]


def get_rfp_by_id(rfp_id: str) -> Dict[str, Any]:
    """
    Retrieve RFP details by ID.

    Args:
        rfp_id: RFP identifier

    Returns:
        RFP dictionary

    Raises:
        ValueError: If RFP not found
    """
    for rfp in RFP_DATA:
        if rfp["ID"] == rfp_id:
            return rfp
    raise ValueError(f"RFP not found: {rfp_id}")


def get_all_rfps() -> List[Dict[str, Any]]:
    """Get all sample RFPs."""
    return RFP_DATA


def add_rfp(rfp_data: Dict[str, Any]) -> None:
    """
    Add a new RFP to the data repository.

    Args:
        rfp_data: RFP dictionary
    """
    if any(r["ID"] == rfp_data["ID"] for r in RFP_DATA):
        raise ValueError(f"RFP already exists: {rfp_data['ID']}")
    RFP_DATA.append(rfp_data)


def create_product_embedding_text(product: Dict[str, Any]) -> str:
    """
    Create a text representation of a product for embedding.

    This text is used by the sentence-transformer to compute embeddings
    for similarity search. It combines all relevant attributes.

    Args:
        product: Product dictionary

    Returns:
        Embedding text
    """
    return (
        f"Cable SKU {product['SKU']}. "
        f"{product['Cores']} core {product['Material']} cable with {product['Insulation']} insulation. "
        f"{product['Size_mm2']}mm² cross-section rated for {product['Voltage_kV']}kV. "
        f"Materials: {product['Material']} conductor. "
        f"Insulation type: {product['Insulation']}. "
        f"Certifications: {', '.join(product['Test_Cert'])}. "
        f"Description: {product['Description']}"
    )


# ==================== EXPORT ====================
__all__ = [
    "OEM_PRODUCTS",
    "RFP_DATA",
    "TODAY",
    "get_oem_product_by_sku",
    "get_all_skus",
    "get_skus_by_material",
    "get_skus_by_insulation",
    "get_skus_by_cores_and_voltage",
    "get_rfp_by_id",
    "get_all_rfps",
    "add_rfp",
    "create_product_embedding_text",
]
