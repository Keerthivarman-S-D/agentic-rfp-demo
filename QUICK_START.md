# Quick Start Guide: Agentic RFP Pro

## 🚀 Getting Started in 3 Steps

### Step 1: Install and Run
```bash
# Install dependencies
pip install streamlit pandas

# Launch the application
streamlit run app.py
```

Your browser will open to `http://localhost:8501`

---

### Step 2: Execute Sales Agent Scan
1. Look at the sidebar (left panel)
2. Click the button **"1️⃣ Initiate Sales Agent Scan"**
3. Wait ~2 seconds for the scan to complete

**What happens:**
- System scans the RFP database
- Calculates risk scores for each RFP
- Filters for opportunities due within 90 days
- Displays a detailed intelligence report

**Example Output:**
```
✅ Intelligence Report: 1 high-value opportunity(ies) identified within 90-day window.

ID                  Client                          Days Left   Risk Score   Priority
RFP-GOV-2025-001   State Infrastructure Authority     75         9/10        🟡 IMMEDIATE ACTION
```

---

### Step 3: Execute Chief Bid Officer
1. In the sidebar, click **"2️⃣ Execute Chief Bid Officer"**
2. Watch the 4-phase workflow execute:

#### Phase 1: Technical Compliance Review (⚙️)
- Weighted SMM calculation for each product line
- Top 3 SKU comparison
- Compliance status indicators
- SMM breakdown (Material 30%, Cores 25%, Size 25%, Insulation 20%)

**Example:**
```
Line 1: 4C × 95mm² XLPE Cable
Rank 1: OEM-XLPE-4C-95 | SMM: 100% | Status: ✅ Perfect Match
```

#### Phase 2: Dynamic Pricing & Risk Assessment (💰)
- LME commodity-indexed material costs
- Testing and certification costs
- Risk premium calculation (if bid bond required)
- Current LME rates display

**Example:**
```
Material Cost Breakdown (LME-Indexed)
Line   SKU              Quantity   Base (₹/m)   Copper (₹/m)   Unit Price (₹/m)   Line Total (₹)
1      OEM-XLPE-4C-95   5,000 m    ₹1,000       ₹294          ₹1,488             ₹7,440,000
```

#### Phase 3: Strategic Business Intelligence (📊)
- Operational ROI: Manual (48h) vs Agentic (2 min)
- Commodity sensitivity analysis (-10% to +10%)
- Competitive advantage metrics
- Board-level profitability reporting

**Example:**
```
Operational Savings: $2,398.33 (99.9% reduction)

LME Copper Shift   Metal Cost Impact   New Total Bid   Net Profit Impact
+10%               ₹180,000            ₹9,130,000      -₹180,000
```

#### Phase 4: Executive Summary (✅)
- Technical product summary table
- Final bid value (4-column display)
- Compliance status and submission readiness

**Example:**
```
Material Cost: ₹7,200,000
Services & Testing: ₹1,740,000
Risk Premium: ₹10,000
GRAND TOTAL: ₹8,950,000 | Ready for Submission
```

---

## 📊 Understanding the Output

### Risk Scores (1-10 scale)
- **1-3:** Low risk, standard terms
- **4-6:** Moderate risk, bid bond or tight deadline
- **7-8:** High risk, liquidated damages present
- **9-10:** Very high risk, multiple commercial constraints

### SMM (Spec Match Metric)
- **100%:** Perfect Match - All specs exactly met
- **85-99%:** Qualified - Acceptable with minor variations
- **80-84%:** Marginal - Review recommended
- **<80%:** Custom Manufacturing Required - Engineering intervention

### Priority Classifications
- 🔴 **HIGH PRIORITY:** Due in < 30 days
- 🟡 **IMMEDIATE ACTION:** Due in 30-90 days
- 🟢 **STRATEGIC MONITORING:** Due in > 90 days

---

## 🎯 Key Features to Explore

### 1. SMM Breakdown (Technical Agent)
- Click the expander "📊 SMM Breakdown for [SKU]"
- See how each parameter contributes to the final score
- Understand weighted importance:
  - Material: 30% (most critical)
  - Cores: 25%
  - Size: 25%
  - Insulation: 20%

### 2. LME Commodity Rates (Pricing Agent)
- Click the expander "📈 Current LME Commodity Rates"
- View current metal prices (simulated)
- Understand how commodity volatility affects pricing

### 3. Sensitivity Analysis (Business Advisory)
- Review the sensitivity table automatically
- See how ±10% copper price shifts impact profitability
- Understand margin protection strategies

---

## 💡 Tips for Best Experience

1. **Sequential Execution:** Always run Sales Agent Scan before Chief Bid Officer
2. **Observe Timing:** Notice the ~2 second total processing time (vs 48 hours manual)
3. **Expand Details:** Click expanders to see detailed calculations
4. **Compare SKUs:** Review Top 3 rankings to understand matching logic
5. **Read Alerts:** Pay attention to 🚨 warnings for engineering intervention

---

## 🔧 Configuration (Optional)

Want to experiment? Edit these values in `app.py`:

### Change LME Rates:
```python
LME_RATES = {
    "Copper": 9200,  # Try 10000 to see +8.7% impact
    "Aluminium": 2400,
}
```

### Adjust Profit Margin:
```python
TARGET_MARGIN = 1.15  # Try 1.20 for 20% margin
```

### Modify SMM Weights:
```python
weights = {
    "Material": 0.30,  # Increase to 0.40 to prioritize material match
    "Cores": 0.25,
    "Size_mm2": 0.25,
    "Insulation": 0.20,
}
```

---

## 📚 Next Steps

1. **Review System Prompts:** Read [`SYSTEM_PROMPTS.md`](SYSTEM_PROMPTS.md) to understand agent personalities
2. **Understand Architecture:** Check [`README.md`](README.md) for full technical details
3. **Review Implementation:** See [`IMPLEMENTATION_SUMMARY.md`](IMPLEMENTATION_SUMMARY.md) for enhancement details

---

## ❓ Troubleshooting

**Issue:** Nothing happens when clicking buttons
- **Solution:** Ensure Streamlit is running (check terminal for errors)

**Issue:** Errors about missing modules
- **Solution:** Run `pip install streamlit pandas` again

**Issue:** Page looks broken
- **Solution:** Clear browser cache and refresh (Ctrl+F5)

---

## 🎉 Success!

You've successfully run an enterprise-grade multi-agent RFP processing system. The workflow you just witnessed:
- Would normally take 48 hours manually
- Now completes in < 2 minutes
- Maintains 100% technical accuracy
- Provides Board-ready business intelligence

**Explore the system, modify parameters, and see how professional AI orchestration works!**
