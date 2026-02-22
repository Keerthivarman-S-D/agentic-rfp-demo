"""
Test Suite for RFP Processing System

Tests for:
- Individual agents
- LangGraph workflow
- API endpoints
- State management
"""

import pytest
from datetime import datetime, timedelta
from backend.state import RFPGraphState, QualifiedRFP, ProductSpecification, SelectedSKU
from backend.config import settings
from backend.agents.sales_agent import sales_agent_node, extract_specifications_node
from backend.agents.technical_agent import calculate_smm_weighted
from backend.workflows.rfp_graph import create_rfp_processing_graph, initialize_rfp_state
from backend.tools.risk_assessment_tool import assess_rfp_risk
from backend.tools.vector_db_tool import vector_db_tool
from backend.data.models import OEM_PRODUCTS, RFP_DATA


class TestRiskAssessment:
    """Test commercial risk scoring."""

    def test_low_risk_rfp(self):
        """Test RFP with low commercial risk."""
        future_date = (datetime.now() + timedelta(days=60)).isoformat()
        result = assess_rfp_risk(
            due_date=future_date,
            bid_bond_required=False,
            liquidated_damages_clause=False,
            performance_bond_percent=0.0,
        )

        assert "risk_score" in result
        assert result["risk_score"] <= 2
        assert result["risk_level"] == "LOW"

    def test_high_risk_rfp(self):
        """Test RFP with high commercial risk."""
        future_date = (datetime.now() + timedelta(days=14)).isoformat()
        result = assess_rfp_risk(
            due_date=future_date,
            bid_bond_required=True,
            liquidated_damages_clause=True,
            performance_bond_percent=15.0,
        )

        assert result["risk_score"] >= 6
        assert result["risk_level"] in ["HIGH", "CRITICAL"]


class TestTechnicalAgent:
    """Test SMM calculation and technical matching."""

    def test_smm_perfect_match(self):
        """Test SMM for perfect product match."""
        sku_data = OEM_PRODUCTS[2]  # OEM-XLPE-4C-95

        smm, breakdown = calculate_smm_weighted(
            req_material="Copper",
            req_insulation="XLPE",
            req_cores=4,
            req_size_mm2=95,
            sku_data=sku_data,
        )

        assert smm == 100.0
        assert breakdown["Material"]["match"] == 1.0
        assert breakdown["Cores"]["match"] == 1.0
        assert breakdown["Size_mm2"]["match"] == 1.0
        assert breakdown["Insulation"]["match"] == 1.0

    def test_smm_size_mismatch(self):
        """Test SMM when size requirement not met."""
        sku_data = OEM_PRODUCTS[0]  # OEM-XLPE-4C-70

        smm, breakdown = calculate_smm_weighted(
            req_material="Copper",
            req_insulation="XLPE",
            req_cores=4,
            req_size_mm2=95,  # Requires 95, but SKU only 70
            sku_data=sku_data,
        )

        assert smm < 100.0
        assert breakdown["Size_mm2"]["match"] == 0.0
        assert smm == 75.0  # Material + Cores + Insulation only

    def test_vector_db_search(self):
        """Test FAISS vector DB search (or fuzzy fallback)."""
        results = vector_db_tool(
            material="Copper",
            insulation="XLPE",
            cores=4,
            size_mm2=95,
            voltage_kv=1.1,
            k=5,
        )

        assert isinstance(results, list)
        assert len(results) > 0
        # Best match should include OEM-XLPE-4C-95
        skus = [r.get("sku") for r in results]
        assert "OEM-XLPE-4C-95" in skus or "OEM-BEST-MATCH" in skus


class TestStateManagement:
    """Test RFPGraphState initialization and transitions."""

    def test_state_initialization(self):
        """Test RFPGraphState initialization."""
        rfp_dict = RFP_DATA[0]
        state = initialize_rfp_state(rfp_dict)

        assert state["status"] == "initialized"
        assert state["rfp_data"] == [rfp_dict]
        assert state["tech_retry_count"] == 0
        assert state["selected_skus"] is None
        assert state["errors"] == []

    def test_product_specification_creation(self):
        """Test ProductSpecification dataclass."""
        spec = ProductSpecification(
            line=1,
            quantity=5000,
            req_material="Copper",
            req_insulation="XLPE",
            req_cores=4,
            req_size_mm2=95,
            req_voltage_kv=1.1,
        )

        assert spec.line == 1
        assert spec.quantity == 5000
        assert spec.req_material == "Copper"


class TestAgents:
    """Test individual agent nodes."""

    def test_sales_agent_qualification(self):
        """Test sales agent RFP qualification."""
        rfp = RFP_DATA[0]
        state = initialize_rfp_state(rfp)

        result_state = sales_agent_node(state)

        assert result_state["qualified_rfp"] is not None
        assert "Sales Agent" in str(result_state["agent_logs"])
        assert result_state["status"] != "failed_sales_screening"

    def test_specification_extraction(self):
        """Test product specification extraction."""
        rfp = RFP_DATA[0]
        state = initialize_rfp_state(rfp)
        state = sales_agent_node(state)
        state = extract_specifications_node(state)

        assert len(state["product_specs"]) > 0
        assert all(isinstance(spec, ProductSpecification) for spec in state["product_specs"])


class TestWorkflow:
    """Test complete workflow execution."""

    def test_workflow_creation(self):
        """Test that workflow can be created and compiled."""
        graph = create_rfp_processing_graph()
        assert graph is not None

    def test_workflow_execution_sample_rfp(self):
        """Test complete workflow with sample RFP."""
        rfp = RFP_DATA[0]
        state = initialize_rfp_state(rfp)

        graph = create_rfp_processing_graph()
        result_state = graph.invoke(state)

        # Check final state
        assert result_state["status"] is not None
        assert "completion_timestamp" in result_state

        # If successful, should have consolidated bid
        if "approve" in result_state.get("status", ""):
            assert result_state["consolidated_bid"] is not None


class TestAPIModels:
    """Test Pydantic API models."""

    def test_rfp_processing_request_validation(self):
        """Test RFPProcessingRequest validation."""
        from backend.api.routes import RFPProcessingRequest, ProductLineRequest

        product = ProductLineRequest(
            line=1,
            quantity=5000,
            req_material="Copper",
            req_insulation="XLPE",
            req_cores=4,
            req_size_mm2=95,
            req_voltage_kv=1.1,
        )

        request = RFPProcessingRequest(
            rfp_id="RFP-TEST-001",
            title="Test RFP",
            client_name="Test Client",
            due_date="2025-04-15",
            products=[product],
            test_requirements=["High Voltage Dielectric Test"],
            bid_bond_required=True,
            bid_bond_value=500000,
        )

        assert request.rfp_id == "RFP-TEST-001"
        assert len(request.products) == 1
        assert request.bid_bond_required is True


# ==================== FIXTURES ====================

@pytest.fixture
def sample_rfp_state():
    """Create a sample RFP state for testing."""
    return initialize_rfp_state(RFP_DATA[0])


@pytest.fixture
def sample_sku_data():
    """Get a sample SKU for testing."""
    return OEM_PRODUCTS[2]  # OEM-XLPE-4C-95


# ==================== INTEGRATION TESTS ====================

def test_end_to_end_workflow():
    """
    Complete end-to-end test of RFP processing.

    This test runs the full workflow on a sample RFP and validates
    the entire pipeline from qualification through final bid.
    """
    rfp = RFP_DATA[0]
    state = initialize_rfp_state(rfp)

    graph = create_rfp_processing_graph()
    result_state = graph.invoke(state)

    # Validate final state
    assert result_state is not None
    assert "completion_timestamp" in result_state
    assert result_state["status"] is not None

    # Validate logs were recorded
    assert len(result_state["agent_logs"]) > 0

    # If bid was created, validate structure
    if result_state.get("consolidated_bid"):
        bid = result_state["consolidated_bid"]
        assert bid.rfp_id == rfp["ID"]
        assert bid.total_bid_value > 0
        assert len(bid.selected_skus) > 0
        assert len(bid.pricing_breakdown) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
