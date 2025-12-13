import streamlit as st
import pandas as pd
import random
import time
from typing import List, Dict, Any
import datetime # Import datetime for date handling

# --- 1. Synthetic Data Setup (Data Repository) ---

# Simplified OEM Product Datasheet Repository
OEM_PRODUCTS = [
    {"SKU": "OEM-XLPE-4C-70", "Material": "Copper", "Insulation": "XLPE", "Cores": 4, "Size_mm2": 70, "Voltage_kV": 1.1, "Test_Cert": ["IS-1554", "IEC-60502"], "Unit_Price": 1200},
    {"SKU": "OEM-PVC-3C-95", "Material": "Aluminium", "Insulation": "PVC", "Cores": 3, "Size_mm2": 95, "Voltage_kV": 3.3, "Test_Cert": ["IS-7098"], "Unit_Price": 850},
    {"SKU": "OEM-XLPE-4C-95", "Material": "Copper", "Insulation": "XLPE", "Cores": 4, "Size_mm2": 95, "Voltage_kV": 1.1, "Test_Cert": ["IS-1554", "IEC-60502"], "Unit_Price": 1500},
    {"SKU": "OEM-PVC-4C-50", "Material": "Copper", "Insulation": "PVC", "Cores": 4, "Size_mm2": 50, "Voltage_kV": 0.66, "Test_Cert": ["IS-7098"], "Unit_Price": 700},
    {"SKU": "OEM-XLPE-3C-70", "Material": "Aluminium", "Insulation": "XLPE", "Cores": 3, "Size_mm2": 70, "Voltage_kV": 3.3, "Test_Cert": ["IS-7098", "IEC-60502"], "Unit_Price": 1100},
    {"SKU": "OEM-BEST-MATCH", "Material": "Copper", "Insulation": "XLPE", "Cores": 4, "Size_mm2": 120, "Voltage_kV": 1.1, "Test_Cert": ["IS-1554", "IEC-60502", "UL"], "Unit_Price": 1800},
]
OEM_DF = pd.DataFrame(OEM_PRODUCTS)

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
        # Due date ~2.5 months from now (Qualified)
        "Due_Date": TODAY + datetime.timedelta(days=75), 
        "Products": [
            {"Line": 1, "Quantity": 5000, "Req_Material": "Copper", "Req_Insulation": "XLPE", "Req_Cores": 4, "Req_Size_mm2": 95, "Req_Voltage_kV": 1.1},
            {"Line": 2, "Quantity": 2000, "Req_Material": "Aluminium", "Req_Insulation": "PVC", "Req_Cores": 3, "Req_Size_mm2": 70, "Req_Voltage_kV": 3.3},
        ],
        "Test_Requirements": ["High Voltage Dielectric Test", "Conductor Resistance Check", "Site Acceptance Test (SAT)"],
    },
    {
        "ID": "RFP-PSU-2025-002",
        "Title": "New Substation Power Line Supply",
        # Due date ~4 months from now (Ignored by Sales Agent)
        "Due_Date": TODAY + datetime.timedelta(days=120), 
        "Products": [
            {"Line": 1, "Quantity": 8000, "Req_Material": "Copper", "Req_Insulation": "PVC", "Req_Cores": 2, "Req_Size_mm2": 50, "Req_Voltage_kV": 0.66},
        ],
        "Test_Requirements": ["Fire Resistance Test", "UL Certification"],
    }
]


# --- 2. Agent Logic Implementation ---

def sales_agent_scan(rfp_data: List[Dict]) -> List[Dict]:
    """
    Sales Agent: Scans RFPs and filters those due in the next 3 months (90 days).
    """
    st.subheader("Sales Agent: RFP Discovery (Scan)")
    st.info("Scanning pre-defined URLs/data sources...")
    time.sleep(1)

    now = datetime.datetime.now().date()
    three_months_out = now + datetime.timedelta(days=90)
    
    qualified_rfps = []
    
    # Standardize data for display
    display_data = []
    
    for rfp in rfp_data:
        due_date = rfp["Due_Date"]
        is_qualified = now <= due_date <= three_months_out
        
        display_data.append({
            "ID": rfp["ID"], 
            "Title": rfp["Title"], 
            "Due Date": due_date.strftime('%Y-%m-%d'), 
            "Qualified (<= 90 days)": "✅" if is_qualified else "❌"
        })
        
        if is_qualified:
            qualified_rfps.append(rfp)
    
    if qualified_rfps:
        st.success(f"Found {len(qualified_rfps)} RFP(s) due within the next 3 months.")
    else:
        st.warning("No RFPs found due within the next 3 months.")
        
    st.table(pd.DataFrame(display_data))
    
    return qualified_rfps

def calculate_smm(rfp_spec: Dict, sku_data: Dict) -> float:
    """
    Technical Agent: Calculates the Spec Match Metric (SMM).
    SMM = (Matching Specs / Total Specs) * 100%
    """
    match_params = ["Material", "Insulation", "Cores", "Size_mm2", "Voltage_kV"]
    total_specs = len(match_params)
    matching_specs = 0
    
    for param in match_params:
        rfp_key = f"Req_{param}"
        sku_key = param
        
        # Binary/Equality Match
        if rfp_spec.get(rfp_key) == sku_data.get(sku_key):
            matching_specs += 1
        # Meets or Exceeds Match (for numerical values like size/voltage)
        elif isinstance(rfp_spec.get(rfp_key), (int, float)) and isinstance(sku_data.get(sku_key), (int, float)):
             # Must meet or exceed the requirement (e.g., higher voltage or size is acceptable)
             if sku_data.get(sku_key) >= rfp_spec.get(rfp_key):
                 matching_specs += 1
    
    smm = (matching_specs / total_specs) * 100 if total_specs > 0 else 0
    return round(smm, 2)

def technical_agent_match(rfp_products: List[Dict]) -> List[Dict]:
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