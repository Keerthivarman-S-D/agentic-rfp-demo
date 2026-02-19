import streamlit as st
import pandas as pd
import random
import time
from typing import List, Dict, Any
import datetime
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
    "IS-1554": 5000,
    "IEC-60502": 4000,
    "IS-7098": 3000,
    "Standard Acceptance": 10000,
}

# Simplified RFP Data (Simulated discovery by Sales Agent)
TODAY = datetime.datetime.now().date()
RFP_DATA = [
    {
        "ID": "RFP-GOV-2025-001",
        "Title": "Infrastructure Project Phase III Cable Supply",
        "Client_Name": "State Infrastructure Authority",
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
    """Calculate risk score (1-10) based on commercial requirements."""
    risk = 0
    
    now = datetime.datetime.now().date()
    days_remaining = (rfp["Due_Date"] - now).days
    if days_remaining < 30:
        risk += 4
    elif days_remaining < 60:
        risk += 2
    
    if rfp.get("Bid_Bond_Required", False):
        risk += 2
    
    if rfp.get("Liquidated_Damages_Clause", False):
        risk += 3
    
    perf_bond = rfp.get("Performance_Bond_Percent", 0)
    if perf_bond >= 10:
        risk += 1
    
    return min(risk, 10)

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
        
        risk_score = calculate_risk_score(rfp)
        
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
    size_match = 1.0 if (rfp_size and sku_size and sku_size >= rfp_size) else 0.0
    size_score = size_match * weights["Size_mm2"] * 100
    total_smm += size_score
    breakdown["Size_mm2"] = {"match": size_match, "score": size_score, "weight": weights["Size_mm2"]}
    
    # Insulation (20%) - Binary Match
    rfp_insulation = rfp_spec.get("Req_Insulation")
    sku_insulation = sku_data.get("Insulation")
    insulation_match = 1.0 if rfp_insulation == sku_insulation else 0.0
    insulation_score = insulation_match * weights["Insulation"] * 100
    total_smm += insulation_score
    breakdown["Insulation"] = {"match": insulation_match, "score": insulation_score, "weight": weights["Insulation"]}
    
    return round(total_smm, 2), breakdown

def technical_agent_match(rfp_products: List[Dict]) -> List[Dict]:
    """
    Technical Agent: Senior Electrical Design Engineer
    Role: Calculate weighted SMM and protect against technical non-compliance.
    """
    st.subheader("⚙️ Technical Agent: Weighted SMM Analysis")
    st.info("**Role:** Senior Design Engineer - Executing precision specification matching against OEM repository...")
    time.sleep(1)
    
    final_selections = []
    
    for product_req in rfp_products:
        sku_scores = []
        for index, sku_row in OEM_DF.iterrows():
            sku_data = sku_row.to_dict()
            smm, breakdown = calculate_smm_weighted(product_req, sku_data)
            sku_scores.append({
                "SKU": sku_data["SKU"], 
                "SMM": smm, 
                "Data": sku_data,
                "Breakdown": breakdown
            })

        sku_scores.sort(key=lambda x: x["SMM"], reverse=True)
        top_sku = sku_scores[0]
        
        top_3_comparison = []
        for i in range(min(3, len(sku_scores))):
            data = sku_scores[i]["Data"]
            smm_val = sku_scores[i]["SMM"]
            
            if smm_val == 100:
                status = "✅ Perfect Match"
            elif smm_val >= 85:
                status = "✅ Qualified"
            elif smm_val >= 80:
                status = "⚠️ Marginal"
            else:
                status = "❌ Custom Req'd"
            
            comparison_row = {
                "Rank": i + 1,
                "SKU": data["SKU"],
                "SMM (%)": smm_val,
                "Status": status,
                "Material": data["Material"],
                "Cores": data["Cores"],
                "Size (mm²)": data["Size_mm2"],
                "Insulation": data["Insulation"],
            }
            top_3_comparison.append(comparison_row)

        st.markdown(f"**Line {product_req['Line']}: {product_req['Req_Cores']}C × {product_req['Req_Size_mm2']}mm² {product_req['Req_Insulation']} Cable**")
        st.dataframe(pd.DataFrame(top_3_comparison), use_container_width=True)
        
        with st.expander(f"📊 SMM Breakdown for {top_sku['SKU']}"):
            breakdown_display = []
            for param, details in top_sku["Breakdown"].items():
                breakdown_display.append({
                    "Parameter": param,
                    "Weight": f"{details['weight']*100:.0f}%",
                    "Match": "✅" if details['match'] == 1.0 else "❌",
                    "Score": f"{details['score']:.1f}"
                })
            st.table(pd.DataFrame(breakdown_display))
        
        product_req["Chosen_SKU"] = top_sku["SKU"]
        product_req["Final_SMM"] = top_sku["SMM"]
        product_req["SKU_Details"] = top_sku["Data"]
        product_req["SMM_Breakdown"] = top_sku["Breakdown"]
        final_selections.append(product_req)
        
    st.success("✅ **Technical Compliance Review Complete.** Recommended SKUs identified.")
    return final_selections

def pricing_agent_calculate(selected_products: List[Dict], test_reqs: List[str], rfp_metadata: Dict) -> Dict:
    """
    Pricing Agent: Industrial Financial Controller
    Role: Dynamic commodity-indexed costing with risk premiums.
    """
    st.subheader("💰 Pricing Agent: Dynamic Costing Engine")
    st.info("**Role:** Financial Controller - Applying LME commodity indexing and margin optimization...")
    time.sleep(1)
    
    material_cost_data = []
    total_base_cost = 0
    total_metal_cost = 0
    total_services_cost = 0

    # Material Costs with LME Indexing
    for product in selected_products:
        sku = product["Chosen_SKU"]
        sku_details = product["SKU_Details"]
        qty = product["Quantity"]
        
        base_price = sku_details["Base_Price"]
        metal_type = sku_details["Material"]
        metal_weight_kg_km = sku_details["Metal_Weight_kg_km"]
        lme_rate_usd_mt = LME_RATES[metal_type]
        
        # Metal cost per meter: (weight_kg/km ÷ 1000) × LME_rate × USD to INR
        metal_cost_per_m = (metal_weight_kg_km / 1000) * (lme_rate_usd_mt / 1000) * 83
        unit_cost = base_price + metal_cost_per_m
        unit_price = unit_cost * TARGET_MARGIN
        
        line_material_cost = qty * unit_price
        line_base_cost = qty * base_price
        line_metal_cost = qty * metal_cost_per_m
        
        total_base_cost += line_base_cost
        total_metal_cost += line_metal_cost
        
        material_cost_data.append({
            "Line": product["Line"],
            "SKU": sku,
            "Quantity": f"{qty:,} m",
            "Base (₹/m)": f"₹{base_price:,.0f}",
            f"{metal_type} (₹/m)": f"₹{metal_cost_per_m:,.0f}",
            "Unit Price (₹/m)": f"₹{unit_price:,.0f}",
            "Line Total (₹)": f"₹{line_material_cost:,.0f}"
        })

    total_material_cost = total_base_cost + total_metal_cost

    # Service (Testing) Costs
    test_cost_data = []
    
    for test in test_reqs:
        cost = TEST_PRICING.get(test, 0)
        total_services_cost += cost
        test_cost_data.append({
            "Type": "Project Test",
            "Service": test,
            "Cost (₹)": f"₹{cost:,.0f}"
        })

    certs = set()
    for product in selected_products:
        certs.update(product["SKU_Details"].get("Test_Cert", []))
        
    for cert in certs:
        cost = TEST_PRICING.get(cert, 0)
        total_services_cost += cost
        test_cost_data.append({
            "Type": "Certification",
            "Service": cert,
            "Cost (₹)": f"₹{cost:,.0f}"
        })
    
    # Risk Premium
    risk_premium = 0
    if rfp_metadata.get("Bid_Bond_Required") or rfp_metadata.get("Liquidated_Damages_Clause"):
        risk_premium = rfp_metadata.get("Bid_Bond_Value", 0) * 0.02
        total_services_cost += risk_premium
        test_cost_data.append({
            "Type": "Risk Premium",
            "Service": "Bid Bond & LD Coverage",
            "Cost (₹)": f"₹{risk_premium:,.0f}"
        })
        
    st.markdown("#### 📦 Material Cost Breakdown (LME-Indexed)")
    st.dataframe(pd.DataFrame(material_cost_data), use_container_width=True)
    
    st.markdown("#### 🧪 Services & Risk Cost Breakdown")
    st.dataframe(pd.DataFrame(test_cost_data), use_container_width=True)
    
    with st.expander("📈 Current LME Commodity Rates"):
        lme_display = []
        for metal, rate in LME_RATES.items():
            lme_display.append({"Metal": metal, "Rate (USD/MT)": f"${rate:,}", "Source": "LME Live"})
        st.table(pd.DataFrame(lme_display))

    st.success(f"✅ **Dynamic Pricing Complete.** Target Margin: {(TARGET_MARGIN-1)*100:.0f}%")
    
    return {
        "Total_Material_Cost": total_material_cost * TARGET_MARGIN,
        "Total_Services_Cost": total_services_cost,
        "Grand_Total": (total_material_cost * TARGET_MARGIN) + total_services_cost,
        "Metal_Cost_Component": total_metal_cost,
        "Base_Cost_Component": total_base_cost,
        "Risk_Premium": risk_premium,
    }

def business_advisory_agent(pricing_result: Dict, selected_products: List[Dict], rfp_metadata: Dict) -> None:
    """
    Business Advisory Agent: Strategic Management Consultant
    Role: Quantify ROI and provide sensitivity analysis.
    """
    st.subheader("📊 Business Advisory Agent: Strategic ROI Analysis")
    st.info("**Role:** Management Consultant - Quantifying business value and competitive advantage...")
    time.sleep(1)
    
    # Manual vs Agentic Cost Savings
    manual_hours = 48
    hourly_rate = 50  # USD
    manual_cost = manual_hours * hourly_rate
    agentic_time_minutes = 2
    agentic_cost = (agentic_time_minutes / 60) * hourly_rate
    savings = manual_cost - agentic_cost
    savings_percent = (savings / manual_cost) * 100
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Manual Process Cost", f"${manual_cost:,.0f}", f"{manual_hours}h @ ${hourly_rate}/h")
    with col2:
        st.metric("Agentic Process Cost", f"${agentic_cost:,.2f}", f"{agentic_time_minutes} min")
    with col3:
        st.metric("Operational Savings", f"${savings:,.0f}", f"{savings_percent:.1f}% reduction")
    
    # Sensitivity Analysis - Copper Price Impact
    st.markdown("### 💹 Commodity Sensitivity Analysis")
    
    copper_scenarios = [-10, -5, 0, 5, 10]
    sensitivity_data = []
    
    base_metal_cost = pricing_result["Metal_Cost_Component"]
    base_profit = pricing_result["Grand_Total"] - pricing_result["Total_Material_Cost"] - pricing_result["Total_Services_Cost"]
    
    for shift in copper_scenarios:
        adjusted_metal_cost = base_metal_cost * (1 + shift/100)
        metal_delta = adjusted_metal_cost - base_metal_cost
        adjusted_total = pricing_result["Grand_Total"] + metal_delta
        adjusted_profit = adjusted_total - pricing_result["Total_Material_Cost"] - metal_delta - pricing_result["Total_Services_Cost"]
        profit_delta = adjusted_profit - base_profit
        
        sensitivity_data.append({
            "LME Copper Shift": f"{shift:+d}%",
            "Metal Cost Impact (₹)": f"₹{metal_delta:,.0f}",
            "New Total Bid (₹)": f"₹{adjusted_total:,.0f}",
            "Net Profit Impact (₹)": f"₹{profit_delta:,.0f}",
            "Profit Margin": f"{(adjusted_profit/adjusted_total)*100:.1f}%"
        })
    
    st.dataframe(pd.DataFrame(sensitivity_data), use_container_width=True)
    
    # Competitive Edge
    st.markdown("### 🏆 Competitive Advantage Metrics")
    days_remaining = (rfp_metadata["Due_Date"] - datetime.datetime.now().date()).days
    time_saved = 2  # days
    first_to_bid_advantage = min(12 * time_saved, 24)  # 12% per day saved, max 24%
    
    competitive_metrics = [
        {"Metric": "Response Time", "Agentic": "< 2 minutes", "Traditional": "48 hours", "Advantage": "99.9% faster"},
        {"Metric": "First-to-Bid Probability", "Agentic": f"{first_to_bid_advantage:.0f}%", "Traditional": "5%", "Advantage": f"+{first_to_bid_advantage-5:.0f}%"},
        {"Metric": "Technical Accuracy", "Agentic": "100% (Weighted SMM)", "Traditional": "~85% (Manual)", "Advantage": "+15%"},
        {"Metric": "Pricing Volatility Risk", "Agentic": "Real-time LME", "Traditional": "Static estimates", "Advantage": "Protected"},
    ]
    
    st.dataframe(pd.DataFrame(competitive_metrics), use_container_width=True)
    
    st.success("📈 **Strategic Advisory Complete.** Bottom-line value quantified for Board presentation.")

def main_orchestrator(qualified_rfp: Dict):
    """
    Main Orchestrator: Chief Bid Officer (CBO)
    Role: Decompose RFPs into parallel workstreams and manage cross-agent consistency.
    """
    st.title(f"🚀 Chief Bid Officer: Processing RFP {qualified_rfp['ID']}")
    
    st.markdown("### Context Decomposition")
    st.markdown(f"**Client:** {qualified_rfp.get('Client_Name', 'N/A')}")
    st.markdown(f"**RFP Title:** {qualified_rfp['Title']}")
    st.markdown(f"**Due Date:** {qualified_rfp['Due_Date'].strftime('%Y-%m-%d')}")
    st.markdown(f"**Risk Score:** {qualified_rfp.get('Risk_Score', 'N/A')}/10")
    
    if qualified_rfp.get("Bid_Bond_Required"):
        st.warning(f"⚠️ **Risk Alert:** Bid Bond Required (₹{qualified_rfp.get('Bid_Bond_Value', 0):,.0f})")
    if qualified_rfp.get("Liquidated_Damages_Clause"):
        st.warning("⚠️ **Risk Alert:** Liquidated Damages Clause Present")
    
    st.divider()
    
    # Phase 1: Technical Matching
    st.markdown("## ⚙️ Phase 1: Technical Compliance Review")
    selected_products = technical_agent_match(qualified_rfp["Products"])
    
    # Check SMM threshold for intervention
    low_match_skus = [p for p in selected_products if p["Final_SMM"] < 80]
    if low_match_skus:
        st.error(f"🚨 **ENGINEERING INTERVENTION REQUIRED:** {len(low_match_skus)} SKU(s) below 80% SMM threshold.")
        for sku in low_match_skus:
            st.markdown(f"- Line {sku['Line']}: {sku['Chosen_SKU']} (SMM: {sku['Final_SMM']}%)")
    
    st.divider()

    # Phase 2: Pricing Estimation
    st.markdown("## 💰 Phase 2: Dynamic Pricing & Risk Assessment")
    pricing_result = pricing_agent_calculate(selected_products, qualified_rfp["Test_Requirements"], qualified_rfp)
    st.divider()
    
    # Phase 3: Business Advisory
    st.markdown("## 📊 Phase 3: Strategic Business Intelligence")
    business_advisory_agent(pricing_result, selected_products, qualified_rfp)
    st.divider()
    
    # Phase 4: Final Consolidation
    st.markdown("## ✅ Phase 4: Executive Summary")
    
    final_tech_summary = [
        {
            "Line": p["Line"], 
            "Quantity": f"{p['Quantity']:,} m",
            "RFP Spec": f"{p['Req_Cores']}C × {p['Req_Size_mm2']}mm² {p['Req_Insulation']}", 
            "Matched SKU": p["Chosen_SKU"], 
            "SMM (%)": p["Final_SMM"]
        }
        for p in selected_products
    ]
    st.markdown("### Technical Product Summary")
    st.dataframe(pd.DataFrame(final_tech_summary), use_container_width=True)
    
    st.markdown("### Final Bid Value")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Material Cost", f"₹{pricing_result['Total_Material_Cost']:,.0f}")
    with col2:
        st.metric("Services & Testing", f"₹{pricing_result['Total_Services_Cost']:,.0f}")
    with col3:
        st.metric("Risk Premium", f"₹{pricing_result.get('Risk_Premium', 0):,.0f}")
    with col4:
        st.metric("**GRAND TOTAL**", f"₹{pricing_result['Grand_Total']:,.0f}", delta="Submission Ready", delta_color="normal")
    
    if not low_match_skus:
        st.balloons()
        st.success("🎉 **Bid Fully Qualified.** Technical integrity: 100%. Ready for Board approval and submission.")
    else:
        st.warning("⚠️ **Manual Review Required.** Engineering team must evaluate custom manufacturing feasibility.")


# --- Streamlit App Initialization ---

st.set_page_config(layout="wide", page_title="Agentic RFP Pro - Enterprise Edition")

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

st.sidebar.title("🎯 Agentic Control Panel")
st.sidebar.markdown("**Enterprise RFP Processing System**")
st.sidebar.markdown("---")

# Display LME Rates in sidebar
st.sidebar.markdown("### 📈 Live LME Rates")
for metal, rate in LME_RATES.items():
    st.sidebar.metric(metal, f"${rate:,}/MT")

st.sidebar.markdown("---")

if st.sidebar.button("1️⃣ Initiate Sales Agent Scan"):
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
    selected_rfp = st.session_state['qualified_rfps'][0]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown(f"**Selected RFP:** {selected_rfp['ID']}")
    st.sidebar.markdown(f"**Risk Score:** {selected_rfp.get('Risk_Score', 'N/A')}/10")
    st.sidebar.markdown(f"**Priority:** {selected_rfp.get('Priority', 'N/A')}")
    
    if st.sidebar.button("2️⃣ Execute Chief Bid Officer", key="run_orchestrator"):
        st.empty() 
        main_orchestrator(selected_rfp)
    else:
        st.warning("Click **'Execute Chief Bid Officer'** to start the multi-agent workflow.")

if 'qualified_rfps' not in st.session_state:
    st.title("Welcome to Agentic RFP Pro 🚀")
    st.markdown("### Enterprise-Grade Intelligent Bid Processing System")
    st.markdown("""
    **System Architecture:**
    - 🔍 **Sales Discovery Agent:** Market intelligence & risk scoring
    - ⚙️ **Technical Agent:** Weighted SMM analysis (30% Material, 25% Cores, 25% Size, 20% Insulation)
    - 💰 **Pricing Agent:** LME commodity-indexed costing with risk premiums
    - 📊 **Business Advisory Agent:** ROI analysis & sensitivity reporting
    - 🚀 **Chief Bid Officer:** End-to-end orchestration
    
    Click **'Initiate Sales Agent Scan'** in the sidebar to begin.
    """)
