import streamlit as st
import pandas as pd
import random
import time
from typing import List, Dict, Any
import datetime # Import datetime for date handling
import json

# --- 1. Synthetic Data Setup (Data Repository) ---

# Simplified OEM Product Datasheet Repository (with Metal Weight for LME Pricing)
OEM_PRODUCTS = [
    {"SKU": "OEM-XLPE-4C-70", "Material": "Copper", "Insulation": "XLPE", "Cores": 4, "Size_mm2": 70, "Voltage_kV": 1.1, "Test_Cert": ["IS-1554", "IEC-60502"], "Base_Price": 800, "Metal_Weight_kg_km": 280},
    {"SKU": "OEM-PVC-3C-95", "Material": "Aluminium", "Insulation": "PVC", "Cores": 3, "Size_mm2": 95, "Voltage_kV": 3.3, "Test_Cert": ["IS-7098"], "Base_Price": 600, "Metal_Weight_kg_km": 220},
    {"SKU": "OEM-XLPE-4C-95", "Material": "Copper", "Insulation": "XLPE", "Cores": 4, "Size_mm2": 95, "Voltage_kV": 1.1, "Test_Cert": ["IS-1554", "IEC-60502"], "Base_Price": 1000, "Metal_Weight_kg_km": 380},
    {"SKU": "OEM-PVC-4C-50", "Material": "Copper", "Insulation": "PVC", "Cores": 4, "Size_mm2": 50, "Voltage_kV": 0.66, "Test_Cert": ["IS-7098"], "Base_Price": 500, "Metal_Weight_kg_km": 200},
    {"SKU": "OEM-XLPE-3C-70", "Material": "Aluminium", "Insulation": "XLPE", "Cores": 3, "Size_mm2": 70, "Voltage_kV": 3.3, "Test_Cert": ["IS-7098", "IEC-60502"], "Base_Price": 750, "Metal_Weight_kg_km": 180},
    {"SKU": "OEM-BEST-MATCH", "Material": "Copper", "Insulation": "XLPE", "Cores": 4, "Size_mm2": 120, "Voltage_kV": 1.1, "Test_Cert": ["IS-1554", "IEC-60502", "UL"], "Base_Price": 1200, "Metal_Weight_kg_km": 480},
]
OEM_DF = pd.DataFrame(OEM_PRODUCTS)

# LME (London Metal Exchange) Commodity Prices (Simulated Current Rates in USD per Metric Ton)
LME_RATES = {
    "Copper": 9200,  # USD/MT
    "Aluminium": 2400,  # USD/MT
}

# Target Profit Margin (configurable)
TARGET_MARGIN = 1.15  # 15% markup

# Services (Testing) Price Table
TEST_PRICING = {
    "High Voltage Dielectric Test": 50000,
    "Conductor Resistance Check": 10000,
    "Site Acceptance Test (SAT)": 120000,
    "Fire Resistance Test": 80000,
    "UL Certification": 200000,
    "IS-1554": 5000, # Certification Cost per SKU
    "IEC-60502": 4000,
    "IS-7098": 3000,
    "Standard Acceptance": 10000,
}

# Simplified RFP Data (Simulated discovery by Sales Agent)
# Use datetime.datetime.now() to ensure dates are current relative to today
TODAY = datetime.datetime.now().date()
RFP_DATA = [
    {
        "ID": "RFP-GOV-2025-001",
        "Title": "Infrastructure Project Phase III Cable Supply",
        "Client_Name": "State Infrastructure Authority",
        # Due date ~2.5 months from now (Qualified)
        "Due_Date": TODAY + datetime.timedelta(days=75), 
        "Products": [
            {"Line": 1, "Quantity": 5000, "Req_Material": "Copper", "Req_Insulation": "XLPE", "Req_Cores": 4, "Req_Size_mm2": 95, "Req_Voltage_kV": 1.1},
            {"Line": 2, "Quantity": 2000, "Req_Material": "Aluminium", "Req_Insulation": "PVC", "Req_Cores": 3, "Req_Size_mm2": 70, "Req_Voltage_kV": 3.3},
        ],
        "Test_Requirements": ["High Voltage Dielectric Test", "Conductor Resistance Check", "Site Acceptance Test (SAT)"],
        "Bid_Bond_Required": True,
        "Bid_Bond_Value": 500000,
        "Liquidated_Damages_Clause": True,
        "Performance_Bond_Percent": 10,
    },
    {
        "ID": "RFP-PSU-2025-002",
        "Title": "New Substation Power Line Supply",
        "Client_Name": "Power Utility Corporation",
        # Due date ~4 months from now (Ignored by Sales Agent)
        "Due_Date": TODAY + datetime.timedelta(days=120), 
        "Products": [
            {"Line": 1, "Quantity": 8000, "Req_Material": "Copper", "Req_Insulation": "PVC", "Req_Cores": 2, "Req_Size_mm2": 50, "Req_Voltage_kV": 0.66},
        ],
        "Test_Requirements": ["Fire Resistance Test", "UL Certification"],
        "Bid_Bond_Required": False,
        "Bid_Bond_Value": 0,
        "Liquidated_Damages_Clause": False,
        "Performance_Bond_Percent": 5,
    }
]


# --- 2. Agent Logic Implementation ---

def calculate_risk_score(rfp: Dict) -> int:
    """
    Calculate risk score (1-10) based on commercial requirements.
    """
    risk = 0
    
    # Days to deadline
    now = datetime.datetime.now().date()
    days_remaining = (rfp["Due_Date"] - now).days
    if days_remaining < 30:
        risk += 4  # High urgency
    elif days_remaining < 60:
        risk += 2
    
    # Bid Bond requirement
    if rfp.get("Bid_Bond_Required", False):
        risk += 2
    
    # Liquidated Damages
    if rfp.get("Liquidated_Damages_Clause", False):
        risk += 3
    
    # Performance Bond
    perf_bond = rfp.get("Performance_Bond_Percent", 0)
    if perf_bond >= 10:
        risk += 1
    
    return min(risk, 10)  # Cap at 10

def sales_agent_scan(rfp_data: List[Dict]) -> List[Dict]:
    """
    Sales Agent: Market Intelligence & Risk Scout
    Role: Proactively qualify leads and extract commercial risks.
    """
    st.subheader("🔍 Sales Discovery Agent: Market Intelligence Scan")
    st.info("**Role:** First line of defense - Extracting metadata and calculating risk profiles...")
    time.sleep(1)

    now = datetime.datetime.now().date()
    three_months_out = now + datetime.timedelta(days=90)
    
    qualified_rfps = []
    display_data = []
    
    for rfp in rfp_data:
        due_date = rfp["Due_Date"]
        days_remaining = (due_date - now).days
        is_qualified = now <= due_date <= three_months_out
        
        # Calculate risk score
        risk_score = calculate_risk_score(rfp)
        
        # Priority classification
        if days_remaining < 30:
            priority = "🔴 HIGH PRIORITY"
        elif days_remaining <= 90:
            priority = "🟡 IMMEDIATE ACTION"
        else:
            priority = "🟢 STRATEGIC MONITORING"
        
        display_data.append({
            "ID": rfp["ID"], 
            "Client": rfp.get("Client_Name", "N/A"),
            "Title": rfp["Title"], 
            "Due Date": due_date.strftime('%Y-%m-%d'),
            "Days Left": days_remaining,
            "Risk Score": f"{risk_score}/10",
            "Priority": priority,
            "Bid Bond": "✅" if rfp.get("Bid_Bond_Required") else "❌",
            "Qualified": "✅" if is_qualified else "❌"
        })
        
        if is_qualified:
            rfp["Risk_Score"] = risk_score
            rfp["Priority"] = priority
            qualified_rfps.append(rfp)
    
    if qualified_rfps:
        st.success(f"✅ **Intelligence Report:** {len(qualified_rfps)} high-value opportunity(ies) identified within 90-day window.")
    else:
        st.warning("⚠️ No immediate opportunities detected. All RFPs beyond strategic threshold.")
        
    st.dataframe(pd.DataFrame(display_data), use_container_width=True)
    
    return qualified_rfps

def calculate_smm_weighted(rfp_spec: Dict, sku_data: Dict) -> tuple:
    """
    Technical Agent: Calculates the Weighted Spec Match Metric (SMM).
    Weights: Material (30%), Cores (25%), Size (25%), Insulation (20%)
    Returns: (total_smm, breakdown_dict)
    """
    weights = {
        "Material": 0.30,
        "Cores": 0.25,
        "Size_mm2": 0.25,
        "Insulation": 0.20,
    }
    
    breakdown = {}
    total_smm = 0.0
    
    # Material (30%) - Binary Match
    rfp_material = rfp_spec.get("Req_Material")
    sku_material = sku_data.get("Material")
    material_match = 1.0 if rfp_material == sku_material else 0.0
    material_score = material_match * weights["Material"] * 100
    total_smm += material_score
    breakdown["Material"] = {"match": material_match, "score": material_score, "weight": weights["Material"]}
    
    # Cores (25%) - Binary Match
    rfp_cores = rfp_spec.get("Req_Cores")
    sku_cores = sku_data.get("Cores")
    cores_match = 1.0 if rfp_cores == sku_cores else 0.0
    cores_score = cores_match * weights["Cores"] * 100
    total_smm += cores_score
    breakdown["Cores"] = {"match": cores_match, "score": cores_score, "weight": weights["Cores"]}
    
    # Size (25%) - Meet or Exceed
    rfp_size = rfp_spec.get("Req_Size_mm2")
    sku_size = sku_data.get("Size_mm2")
    size_match = 1.0 if sku_size >= rfp_size else 0.0
    size_score = size_match * weights["Size_mm2"] * 100
    total_smm += size_score
    breakdown["Size_mm2"] = {"match": size_match, "score": size_score, "weight": weights["Size_mm2"]}
    
    # Insulation (20%) - Binary Match (simplified)
    rfp_insulation = rfp_spec.get("Req_Insulation")
    sku_insulation = sku_data.get("Insulation")
    insulation_match = 1.0 if rfp_insulation == sku_insulation else 0.0
    insulation_score = insulation_match * weights["Insulation"] * 100
    total_smm += insulation_score
    breakdown["Insulation"] = {"match": insulation_match, "score": insulation_score, "weight": weights["Insulation"]}
    
    return round(total_smm, 2), breakdown
    """
    Technical Agent: Matches RFP requirements to OEM SKUs and selects the Top 1.
    """
    st.subheader("Technical Agent: SKU Matching & SMM Calculation")
    st.info("Parsing specifications and comparing against OEM data repository...")
    time.sleep(1)
    
    final_selections = []
    
    for product_req in rfp_products:
        
        sku_scores = []
        for index, sku_row in OEM_DF.iterrows():
            sku_data = sku_row.to_dict()
            smm = calculate_smm(product_req, sku_data)
            sku_scores.append({"SKU": sku_data["SKU"], "SMM": smm, "Data": sku_data})

        # Sort by SMM (descending)
        sku_scores.sort(key=lambda x: x["SMM"], reverse=True)
        
        top_sku = sku_scores[0]
        
        # Prepare comparison table for top 3
        top_3_comparison = []
        for i in range(min(3, len(sku_scores))):
            data = sku_scores[i]["Data"]
            comparison_row = {
                "Rank": i + 1,
                "SKU": data["SKU"],
                "SMM (%)": sku_scores[i]["SMM"],
                "Material": data["Material"],
                "Insulation": data["Insulation"],
                "Cores": data["Cores"],
                "Size (mm2)": data["Size_mm2"],
                "Voltage (kV)": data["Voltage_kV"]
            }
            top_3_comparison.append(comparison_row)

        st.markdown(f"**--- RFP Line {product_req['Line']}: {product_req['Req_Cores']}C x {product_req['Req_Size_mm2']}mm² ({product_req['Req_Insulation']}) ---**")
        st.dataframe(pd.DataFrame(top_3_comparison))
        
        # Select Top 1
        product_req["Chosen_SKU"] = top_sku["SKU"]
        product_req["Final_SMM"] = top_sku["SMM"]
        product_req["SKU_Details"] = top_sku["Data"]
        final_selections.append(product_req)
        
    st.success("Technical matching complete. Top SKUs selected.")
    return final_selections

def pricing_agent_calculate(selected_products: List[Dict], test_reqs: List[str]) -> Dict:
    """
    Pricing Agent: Calculates material and testing costs.
    """
    st.subheader("Pricing Agent: Cost Estimation")
    st.info("Calculating material costs and pricing required tests...")
    time.sleep(1)
    
    material_cost_data = []
    total_material_cost = 0
    total_services_cost = 0

    # Material Costs
    for product in selected_products:
        sku = product["Chosen_SKU"]
        qty = product["Quantity"]
        price_per_unit = product["SKU_Details"]["Unit_Price"]
        line_material_cost = qty * price_per_unit
        total_material_cost += line_material_cost
        
        material_cost_data.append({
            "Line": product["Line"],
            "SKU": sku,
            "Quantity": qty,
            "Unit Price (Rs)": f"Rs {price_per_unit:,.2f}",
            "Line Total (Rs)": f"Rs {line_material_cost:,.2f}"
        })

    # Service (Testing) Costs
    test_cost_data = []
    
    # 1. Project-Specific Tests
    for test in test_reqs:
        cost = TEST_PRICING.get(test, 0)
        total_services_cost += cost
        test_cost_data.append({
            "Type": "Project Requirement",
            "Service": test,
            "Cost (Rs)": f"Rs {cost:,.2f}"
        })

    # 2. Certification/Standard Costs (Assumed fixed cost per certification for the bid)
    certs = set()
    for product in selected_products:
        # Include the product's certifications only if they are not already covered
        certs.update(product["SKU_Details"].get("Test_Cert", []))
        
    for cert in certs:
        cost = TEST_PRICING.get(cert, 0)
        total_services_cost += cost
        test_cost_data.append({
            "Type": "Certification Cost",
            "Service": f"Compliance Fee ({cert})",
            "Cost (Rs)": f"Rs {cost:,.2f}"
        })
        
    # Consolidate Output
    st.markdown("#### Material Cost Breakdown")
    st.dataframe(pd.DataFrame(material_cost_data))
    
    st.markdown("#### Services & Testing Cost Breakdown")
    st.dataframe(pd.DataFrame(test_cost_data))

    st.success("Pricing calculation complete.")
    
    return {
        "Total_Material_Cost": total_material_cost,
        "Total_Services_Cost": total_services_cost,
        "Grand_Total": total_material_cost + total_services_cost,
    }


def main_orchestrator(qualified_rfp: Dict):
    """
    Main Orchestrator: Drives the end-to-end workflow and consolidation.
    """
    st.title(f"🚀 Main Orchestrator: Processing RFP {qualified_rfp['ID']}")
    
    st.markdown("### Context Decomposition")
    st.markdown(f"**RFP Title:** {qualified_rfp['Title']}")
    st.markdown(f"**Submission Due:** {qualified_rfp['Due_Date'].strftime('%Y-%m-%d')}")
    st.markdown(f"**Tests for Pricing Agent:** {', '.join(qualified_rfp['Test_Requirements'])}")
    st.divider()
    
    # --- 1. Execute Technical Agent ---
    st.markdown("## ⚙️ Phase 1: Technical Matching")
    selected_products = technical_agent_match(qualified_rfp["Products"])
    st.divider()

    # --- 2. Execute Pricing Agent (Parallel Phase) ---
    st.markdown("## 💰 Phase 2: Pricing Estimation")
    pricing_result = pricing_agent_calculate(selected_products, qualified_rfp["Test_Requirements"])
    st.divider()
    
    # --- 3. Final Consolidation ---
    st.markdown("## ✅ Phase 3: Final RFP Consolidation")
    
    # Final Technical Summary Table
    final_tech_summary = [
        {"Line": p["Line"], "RFP Qty": p["Quantity"], "RFP Spec": f"{p['Req_Cores']}C x {p['Req_Size_mm2']}mm² {p['Req_Insulation']}", "Chosen OEM SKU": p["Chosen_SKU"], "Spec Match (%)": p["Final_SMM"]}
        for p in selected_products
    ]
    st.markdown("### Technical Product Summary")
    st.dataframe(pd.DataFrame(final_tech_summary))
    
    # Final Price Summary Card
    st.markdown("### Final Consolidated Price")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Material Cost (Rs)", value=f"Rs {pricing_result['Total_Material_Cost']:,.2f}")
        
    with col2:
        st.metric(label="Total Services/Test Cost (Rs)", value=f"Rs {pricing_result['Total_Services_Cost']:,.2f}")

    with col3:
        st.metric(label="Grand Total Bid Value (Rs)", value=f"Rs {pricing_result['Grand_Total']:,.2f}", delta="Ready for Submission")
        
    
    # Check for SMM threshold
    low_match_skus = [p for p in selected_products if p["Final_SMM"] < 80]
    if low_match_skus:
        st.error(f"🚨 ALERT: {len(low_match_skus)} SKU(s) matched below 80% SMM threshold. MANUAL REVIEW REQUIRED for custom manufacturing.")
    else:
        st.balloons()
        st.success("🎉 Bid fully qualified and ready for submission!")
        

# --- Streamlit App Initialization ---

# Set layout configuration
st.set_page_config(layout="wide", page_title="Agentic RFP Solution Demo")

# Custom CSS for the demo aesthetics (kept simple for robustness)
st.markdown("""
<style>
.stApp {
    background-color: #1e1e1e;
    color: #f0f0f0;
}
h1, h2, h3, h4 {
    color: #deff9a;
}
</style>
""", unsafe_allow_html=True)


st.sidebar.title("Agentic Control Panel")
st.sidebar.markdown("Run the full end-to-end RFP process simulation.")

# --- Demo Start ---

# Use session state to maintain the list of qualified RFPs across button clicks
if st.sidebar.button("1. Initiate Sales Agent Scan"):
    # Convert RFP Due Dates to datetime.date objects for comparison
    rfp_data_with_dates = [
        {**rfp, "Due_Date": rfp["Due_Date"]} 
        for rfp in RFP_DATA
    ]
    
    st.session_state['qualified_rfps'] = sales_agent_scan(rfp_data_with_dates)
    
    if st.session_state['qualified_rfps']:
        st.session_state['show_process'] = True
    else:
        st.session_state['show_process'] = False
        
if 'show_process' in st.session_state and st.session_state['show_process']:
    
    # Select the first qualified RFP for the demo
    selected_rfp = st.session_state['qualified_rfps'][0]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**RFP Selected:** {selected_rfp['ID']}")
    
    # Use a unique key to ensure the button re-renders correctly
    if st.sidebar.button("2. Execute Main Orchestrator (Process Bid)", key="run_orchestrator"):
        # Clear previous output before running the new workflow
        st.empty() 
        main_orchestrator(selected_rfp)
    else:
        st.warning("Click 'Execute Main Orchestrator' to start the parallel matching and pricing process.")

# Initial check for the start state
if 'qualified_rfps' not in st.session_state:
    st.title("Welcome to the Agentic RFP Solution Demo")
    st.markdown("Click **'1. Initiate Sales Agent Scan'** in the sidebar to begin the automated workflow.")