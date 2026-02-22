"""
RFP Processing System - Core State Management

This module defines the GraphState TypedDict and all supporting dataclasses
that track data flow through the multi-agent LangGraph workflow.

The state machine ensures type-safe execution and complete audit trails.
"""

from typing import TypedDict, Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QualifiedRFP:
    """
    RFP metadata after Sales Agent screening and qualification.

    Attributes:
        id: Unique RFP identifier
        title: RFP title/description
        client_name: Client organization name
        due_date: Submission deadline (ISO format string)
        risk_score: Commercial risk assessment (1-10 scale)
        priority: Priority level (HIGH PRIORITY, IMMEDIATE ACTION, STRATEGIC MONITORING)
        bid_bond_required: Whether bid bond is needed
        bid_bond_value: Bond amount if required (INR)
        performance_bond_percent: Performance guarantee percentage
        test_requirements: List of required testing certifications
        liquidated_damages_clause: Whether LD clause is present
    """
    id: str
    title: str
    client_name: str
    due_date: str
    risk_score: int
    priority: str
    bid_bond_required: bool = False
    bid_bond_value: float = 0.0
    performance_bond_percent: float = 0.0
    test_requirements: List[str] = field(default_factory=list)
    liquidated_damages_clause: bool = False


@dataclass
class ProductSpecification:
    """
    Individual product line requirement extracted from RFP.

    Attributes:
        line: Line item number in RFP
        quantity: Quantity required (in meters)
        req_material: Required conductor material (Copper/Aluminium)
        req_insulation: Required insulation type (PVC/XLPE)
        req_cores: Number of cores required
        req_size_mm2: Cross-section size in mm²
        req_voltage_kv: Rated voltage in kV
    """
    line: int
    quantity: int
    req_material: str
    req_insulation: str
    req_cores: int
    req_size_mm2: int
    req_voltage_kv: float


@dataclass
class SelectedSKU:
    """
    Technical agent output: matched SKU for a product specification line.

    Attributes:
        line: Line item reference
        sku_id: Selected SKU identifier
        smm_score: Spec Match Metric score (0-100%)
        smm_breakdown: Individual component match scores
        retry_count: How many retry iterations were needed
        matched_specs: Actual SKU specifications that matched
    """
    line: int
    sku_id: str
    smm_score: float
    smm_breakdown: Dict[str, float]
    retry_count: int
    matched_specs: Dict[str, Any]


@dataclass
class PricingResult:
    """
    Pricing agent output: complete cost breakdown for a line item.

    Attributes:
        line: Line item reference
        sku_id: Associated SKU
        quantity: Ordered quantity (meters)
        material_cost: Cost of material components (LME-indexed)
        labor_cost: Manufacturing/handling cost
        services_cost: Testing and certification costs
        risk_premium: Additional margin for commercial risks
        grand_total: Complete cost for this line
        commodities_used: Dict of commodity type → cost contribution
    """
    line: int
    sku_id: str
    quantity: int
    material_cost: float
    labor_cost: float
    services_cost: float
    risk_premium: float
    grand_total: float
    commodities_used: Dict[str, float] = field(default_factory=dict)


@dataclass
class ConsolidatedBid:
    """
    Final output: complete, submission-ready bid package.

    Attributes:
        rfp_id: Associated RFP identifier
        selected_skus: List of matched SKUs across all line items
        pricing_breakdown: Cost details for each line
        total_bid_value: Grand total for entire bid
        technical_compliance: Overall SMM average (%)
        business_roi: Strategic metrics (cost savings, competitive advantage)
        created_at: Timestamp of bid generation
        agent_logs: Complete communication trail for audit
    """
    rfp_id: str
    selected_skus: List[SelectedSKU]
    pricing_breakdown: List[PricingResult]
    total_bid_value: float
    technical_compliance: float
    business_roi: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    agent_logs: List[Dict[str, str]] = field(default_factory=list)


class RFPGraphState(TypedDict):
    """
    Central state machine for the entire RFP processing workflow.

    This TypedDict is used by LangGraph to manage state transitions across
    multiple agents. Each key represents a piece of information that flows
    through the system.

    Layer Organization:
    - Input Layer: Raw RFP data received from discovery
    - Sales Agent Layer: Qualification and risk assessment
    - Technical Agent Layer: SKU matching with retry control
    - Pricing Agent Layer: Cost calculation
    - Business Advisory Layer: Strategic analysis
    - Output Layer: Final consolidated bid
    - System Layer: Logging and error handling
    """

    # ==================== INPUT LAYER ====================
    # Initial RFP data from discovery process
    rfp_data: List[Dict[str, Any]]


    # ==================== SALES AGENT LAYER ====================
    # Output from sales discovery and risk screening
    qualified_rfp: Optional[QualifiedRFP]
    sales_notes: str


    # ==================== TECHNICAL AGENT LAYER ====================
    # Extracted product specifications from RFP
    product_specs: List[ProductSpecification]

    # SKU matching results
    selected_skus: Optional[List[SelectedSKU]]

    # Retry control and tracking
    tech_retry_count: int                    # Current iteration (0-3)
    tech_retry_logs: List[str]               # What was attempted in each iteration
    tech_retry_criteria_relaxation: int      # How much to relax matching criteria

    # Validation flag for conditional routing
    technical_compliance_ok: bool            # SMM >= 80% for all lines?


    # ==================== PRICING AGENT LAYER ====================
    # Cost calculation results
    pricing_results: Optional[List[PricingResult]]

    # Validation and control
    pricing_constraints_met: bool            # Within margin targets? Budget OK?
    pricing_notes: str                       # Explanation of pricing decisions

    # LME commodity market data
    lme_rates_snapshot: Dict[str, float]     # Metal prices at calculation time


    # ==================== BUSINESS ADVISORY LAYER ====================
    # Strategic analysis output
    roi_analysis: Optional[Dict[str, Any]]   # Sensitivity analysis, competitive metrics


    # ==================== OUTPUT LAYER ====================
    # Final submission-ready bid
    consolidated_bid: Optional[ConsolidatedBid]

    # Final decision on bid
    final_decision: Optional[str]                # "approve", "escalate", or "decline"


    # ==================== SYSTEM LAYER ====================
    # Agent communication and decision trail
    agent_logs: List[Dict[str, str]]         # Audit trail: agent → action → result

    # Error tracking
    errors: List[str]                        # Non-fatal errors during processing

    # Workflow status
    status: str                              # Current phase (e.g., "sales_screening", "technical_matching", "pricing")
    completion_timestamp: Optional[str]      # When processing finished
