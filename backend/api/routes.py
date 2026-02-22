"""
API Routes and Pydantic Models

Defines REST endpoints for RFP processing and request/response models.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException
import asyncio
import logging

from backend.api.main import app
from backend.workflows.rfp_graph import create_rfp_processing_graph, initialize_rfp_state
from backend.state import RFPGraphState, ConsolidatedBid, SelectedSKU, PricingResult
from backend.data.models import get_all_rfps, get_rfp_by_id

logger = logging.getLogger(__name__)

# ==================== PYDANTIC REQUEST/RESPONSE MODELS ====================


class ProductLineRequest(BaseModel):
    """Product line specification from RFP."""

    line: int = Field(..., description="Line item number")
    quantity: int = Field(..., description="Quantity in meters")
    req_material: str = Field(..., description="Required material (Copper/Aluminium)")
    req_insulation: str = Field(..., description="Required insulation (PVC/XLPE)")
    req_cores: int = Field(..., description="Required number of cores")
    req_size_mm2: int = Field(..., description="Required size in mm²")
    req_voltage_kv: float = Field(..., description="Required voltage in kV")


class RFPProcessingRequest(BaseModel):
    """Request model for RFP processing."""

    rfp_id: str = Field(..., description="Unique RFP identifier")
    title: str = Field(..., description="RFP title")
    client_name: str = Field(..., description="Client organization name")
    due_date: str = Field(..., description="Due date (ISO format)")
    products: List[ProductLineRequest] = Field(..., description="Product line items")
    test_requirements: List[str] = Field(
        default_factory=list,
        description="Required testing/certifications",
    )
    bid_bond_required: bool = Field(default=False, description="Whether bid bond is required")
    bid_bond_value: float = Field(default=0.0, description="Bid bond amount (INR)")
    liquidated_damages_clause: bool = Field(
        default=False,
        description="Whether LD clause is present",
    )
    performance_bond_percent: float = Field(
        default=0.0,
        description="Performance bond percentage",
    )


class SkuDetailResponse(BaseModel):
    """Selected SKU detail."""

    line: int
    sku_id: str
    smm_score: float
    material: str
    insulation: str
    cores: int
    size_mm2: int
    voltage_kv: float
    retry_count: int


class PricingDetailResponse(BaseModel):
    """Pricing detail for a line item."""

    line: int
    sku_id: str
    quantity: int
    material_cost: float
    services_cost: float
    risk_premium: float
    grand_total: float


class ConsolidatedBidResponse(BaseModel):
    """Final consolidated bid response."""

    rfp_id: str = Field(..., description="RFP identifier")
    selected_skus: List[SkuDetailResponse] = Field(..., description="Selected SKUs")
    total_bid_value: float = Field(..., description="Total bid value (INR)")
    technical_compliance: float = Field(
        ...,
        description="Average SMM across all lines (%)",
    )
    pricing_breakdown: List[PricingDetailResponse] = Field(
        ...,
        description="Pricing per line",
    )
    roi_analysis: Dict[str, Any] = Field(
        ...,
        description="Strategic ROI metrics",
    )
    agent_logs: List[Dict[str, str]] = Field(
        ...,
        description="Agent communication trail",
    )


class RFPProcessingResponse(BaseModel):
    """Response model for RFP processing."""

    status: str = Field(..., description="Processing status")
    rfp_id: str = Field(..., description="RFP identifier")
    consolidated_bid: Optional[ConsolidatedBidResponse] = Field(
        None,
        description="Final bid (if processing succeeded)",
    )
    errors: List[str] = Field(default_factory=list, description="Non-fatal errors")
    completion_timestamp: Optional[str] = Field(None, description="When processing finished")


class JobStatusResponse(BaseModel):
    """Response model for async job status."""

    job_id: str = Field(..., description="Job ID")
    status: str = Field(..., description="Current status")
    progress: int = Field(..., description="Progress percentage (0-100)")
    consolidated_bid: Optional[ConsolidatedBidResponse] = Field(None)
    errors: List[str] = Field(default_factory=list)


class CommodityPricesResponse(BaseModel):
    """Response model for commodity prices."""

    rates: Dict[str, float] = Field(..., description="Material prices (USD/MT)")
    timestamp: str = Field(..., description="Timestamp of rates")
    currency_conversion: str = Field(..., description="USD to INR conversion")


# ==================== ROUTER ====================

router = APIRouter(prefix="/api", tags=["RFP Processing"])


# ==================== ENDPOINTS ====================


@router.post("/rfp/process", response_model=RFPProcessingResponse)
async def process_rfp(request: RFPProcessingRequest) -> RFPProcessingResponse:
    """
    Process an RFP end-to-end and return consolidated bid.

    This endpoint:
    1. Validates RFP data
    2. Runs complete multi-agent workflow
    3. Returns structured bid with audit trail

    Args:
        request: RFPProcessingRequest with RFP details

    Returns:
        RFPProcessingResponse with bid or errors

    Raises:
        HTTPException: If processing fails
    """
    try:
        # Convert request to RFP dict
        rfp_dict = {
            "ID": request.rfp_id,
            "Title": request.title,
            "Client_Name": request.client_name,
            "Due_Date": request.due_date,
            "Products": [
                {
                    "Line": p.line,
                    "Quantity": p.quantity,
                    "Req_Material": p.req_material,
                    "Req_Insulation": p.req_insulation,
                    "Req_Cores": p.req_cores,
                    "Req_Size_mm2": p.req_size_mm2,
                    "Req_Voltage_kV": p.req_voltage_kv,
                }
                for p in request.products
            ],
            "Test_Requirements": request.test_requirements,
            "Bid_Bond_Required": request.bid_bond_required,
            "Bid_Bond_Value": request.bid_bond_value,
            "Liquidated_Damages_Clause": request.liquidated_damages_clause,
            "Performance_Bond_Percent": request.performance_bond_percent,
        }

        # Initialize state
        state = initialize_rfp_state(rfp_dict)

        # Create and run graph
        graph = create_rfp_processing_graph()
        final_state = graph.invoke(state)

        # Extract consolidated bid
        consolidated_bid = final_state.get("consolidated_bid")

        # Format response
        if consolidated_bid:
            bid_response = ConsolidatedBidResponse(
                rfp_id=consolidated_bid.rfp_id,
                selected_skus=[
                    SkuDetailResponse(
                        line=sku.line,
                        sku_id=sku.sku_id,
                        smm_score=sku.smm_score,
                        material=sku.matched_specs.get("material", ""),
                        insulation=sku.matched_specs.get("insulation", ""),
                        cores=sku.matched_specs.get("cores", 0),
                        size_mm2=sku.matched_specs.get("size_mm2", 0),
                        voltage_kv=sku.matched_specs.get("voltage_kv", 0.0),
                        retry_count=sku.retry_count,
                    )
                    for sku in consolidated_bid.selected_skus
                ],
                total_bid_value=consolidated_bid.total_bid_value,
                technical_compliance=consolidated_bid.technical_compliance,
                pricing_breakdown=[
                    PricingDetailResponse(
                        line=pr.line,
                        sku_id=pr.sku_id,
                        quantity=pr.quantity,
                        material_cost=pr.material_cost,
                        services_cost=pr.services_cost,
                        risk_premium=pr.risk_premium,
                        grand_total=pr.grand_total,
                    )
                    for pr in consolidated_bid.pricing_breakdown
                ],
                roi_analysis=consolidated_bid.business_roi,
                agent_logs=consolidated_bid.agent_logs,
            )
        else:
            bid_response = None

        return RFPProcessingResponse(
            status=final_state.get("status", "unknown"),
            rfp_id=request.rfp_id,
            consolidated_bid=bid_response,
            errors=final_state.get("errors", []),
            completion_timestamp=final_state.get("completion_timestamp"),
        )

    except Exception as e:
        logger.error(f"RFP processing error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"RFP processing failed: {str(e)}",
        )


@router.get("/rfp/samples", response_model=List[Dict[str, Any]])
async def get_sample_rfps():
    """
    Get list of sample RFPs for testing.

    Returns:
        List of sample RFP objects
    """
    try:
        return get_all_rfps()
    except Exception as e:
        logger.error(f"Error retrieving sample RFPs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve sample RFPs",
        )


@router.get("/commodities/prices", response_model=CommodityPricesResponse)
async def get_commodity_prices():
    """
    Get current LME commodity prices.

    Returns:
        Current metal rates in USD/MT
    """
    from backend.config import settings
    from datetime import datetime

    return CommodityPricesResponse(
        rates=settings.LME_RATES,
        timestamp=datetime.now().isoformat(),
        currency_conversion=f"1 USD = {settings.USD_TO_INR_RATE} INR",
    )


@router.post("/commodities/prices")
async def update_commodity_price(material: str, new_rate_usd_mt: float):
    """
    Update a commodity price (admin function).

    Args:
        material: Material name
        new_rate_usd_mt: New price in USD/MT

    Returns:
        Confirmation
    """
    from backend.config import settings

    try:
        if material not in settings.LME_RATES:
            raise ValueError(f"Unknown material: {material}")

        old_rate = settings.LME_RATES[material]
        settings.LME_RATES[material] = new_rate_usd_mt

        return {
            "status": "updated",
            "material": material,
            "old_rate": old_rate,
            "new_rate": new_rate_usd_mt,
            "change_percent": round(((new_rate_usd_mt - old_rate) / old_rate) * 100, 2),
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/vector-db/search")
async def search_vector_db(
    material: str,
    insulation: str,
    cores: int,
    size_mm2: int,
    voltage_kv: float,
    k: int = 5,
):
    """
    Search OEM catalog via vector DB.

    Args:
        material: Material requirement
        insulation: Insulation requirement
        cores: Cores requirement
        size_mm2: Size requirement
        voltage_kv: Voltage requirement
        k: Number of results

    Returns:
        List of matching SKUs
    """
    try:
        from backend.tools.vector_db_tool import vector_db_tool

        results = vector_db_tool(
            material=material,
            insulation=insulation,
            cores=cores,
            size_mm2=size_mm2,
            voltage_kv=voltage_kv,
            k=k,
        )
        return {"matches": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== REGISTER ROUTER ====================

app.include_router(router)

__all__ = [
    "router",
    "RFPProcessingRequest",
    "RFPProcessingResponse",
    "ConsolidatedBidResponse",
]
