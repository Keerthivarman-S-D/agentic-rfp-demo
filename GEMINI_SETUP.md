# 🚀 Gemini API Setup Guide

This document explains how to set up and use Google's Gemini API with the Agentic RFP Bidding Engine.

## ⚡ Quick Setup (2 minutes)

### 1. Get Your Gemini API Key

```bash
# Visit: https://aistudio.google.com/app/apikeys
# Click "Create API Key"
# Copy the key (starts with AIza...)
```

### 2. Update `.env` File

```bash
# Copy the template (if not already done)
cp .env.example .env

# Edit .env and set:
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...your-key-here...
MODEL_NAME=gemini-2.0-flash
```

### 3. Install Dependencies

```bash
# Install Gemini package (already in requirements.txt)
pip install -r requirements.txt

# Or just Gemini if you only need that:
pip install langchain-google-genai
```

### 4. Start the Server

```bash
uvicorn backend.api.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test It

```bash
# Health check
curl http://localhost:8000/health

# Check configuration
curl http://localhost:8000/api/config | grep -i "model\|provider"

# Expected output should show:
# "provider": "gemini"
# "model": "gemini-2.0-flash"
```

---

## 📊 Gemini Model Comparison

| Model | Speed | Cost | When to Use |
|-------|-------|------|------------|
| **gemini-2.0-flash** | ⚡ Fastest | $ Cheapest | ✅ **Production (Recommended)** |
| **gemini-1.5-pro** | Normal | $$ Mid | Complex reasoning, longer context |
| **gemini-1.5-flash** | Fast | $ Low | Good balance, cost-conscious |

**Recommendation:** Use `gemini-2.0-flash` for this system. It's:
- ✅ Fastest (lowest latency)
- ✅ Cheapest (~40x cheaper than Claude Sonnet)
- ✅ Excellent quality for business logic
- ✅ Supports up to 1M token context

---

## 🔄 How It Works

The system uses a **factory function** that automatically creates the right LLM based on `LLM_PROVIDER`:

```python
# In backend/config.py
def create_llm_chain():
    """Factory function to create LLM chain based on configured provider."""
    if settings.LLM_PROVIDER == "gemini":
        return ChatGoogleGenerativeAI(...)  # Gemini
    elif settings.LLM_PROVIDER == "anthropic":
        return ChatAnthropic(...)  # Claude
    elif settings.LLM_PROVIDER == "openai":
        return ChatOpenAI(...)  # GPT
```

All 5 agents use this factory:

```python
# In each agent file:
from backend.config import create_llm_chain

def create_sales_agent_chain():
    return create_llm_chain()  # Automatically uses Gemini!
```

---

## 🔑 Environment Variable Options

### Minimal Setup (Gemini only)
```bash
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIzaSy...
MODEL_NAME=gemini-2.0-flash
```

### Multi-Provider Setup (Gemini + Claude + GPT)
```bash
# Set all keys, switch with LLM_PROVIDER
LLM_PROVIDER=gemini  # or "anthropic" or "openai"
GEMINI_API_KEY=AIzaSy...
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
MODEL_NAME=gemini-2.0-flash  # Model name varies by provider
```

---

## 💰 Cost Comparison

### Processing One RFP

| Provider | Model | Cost (Estimate) |
|----------|-------|-----------------|
| **Gemini** | 2.0-flash | ~$0.001 |
| **Gemini** | 1.5-pro | ~$0.01 |
| **Claude** | 3.5-Sonnet | ~$0.04 |

Your annual savings with Gemini:
```
1,000 RFPs/year × $0.039 savings per RFP  = $39,000/year saved
5,000 RFPs/year × $0.039 savings per RFP  = $195,000/year saved
```

---

## ✅ Verification Checklist

After setup, verify everything works:

```bash
# 1. Check environment
grep "LLM_PROVIDER\|GEMINI_API_KEY\|MODEL_NAME" .env

# 2. Start server
uvicorn backend.api.main:app --reload

# 3. In new terminal, test endpoints
curl http://localhost:8000/health

# 4. Check LLM configuration
curl http://localhost:8000/api/config

# 5. Process a sample RFP
curl -X POST http://localhost:8000/api/rfp/process \
  -H "Content-Type: application/json" \
  -d '{
    "rfp_id": "RFP-TEST-001",
    "title": "Test Cable RFP",
    "client_name": "Test Client",
    "due_date": "2025-04-15",
    "products": [{
      "line": 1,
      "quantity": 5000,
      "req_material": "Copper",
      "req_insulation": "XLPE",
      "req_cores": 4,
      "req_size_mm2": 95,
      "req_voltage_kv": 1.1
    }],
    "test_requirements": ["High Voltage Dielectric Test"],
    "bid_bond_required": true,
    "bid_bond_value": 500000
  }'

# 6. Look for "status": "workflow_complete_approved" or similar
```

---

## 🔧 Troubleshooting

### Problem: "GEMINI_API_KEY not set"
```bash
# Solution: Check .env file
cat .env | grep GEMINI_API_KEY

# Should output:
# GEMINI_API_KEY=AIzaSy...

# If missing or empty, update it:
nano .env
# Add: GEMINI_API_KEY=AIzaSy...
```

### Problem: "langchain-google-genai not installed"
```bash
# Solution: Install it
pip install langchain-google-genai
# Then restart the server
```

### Problem: API request timeout
```bash
# Gemini sometimes takes longer on first request
# Solution: Just retry, it should work immediately after

# Or check Gemini API status: https://statuspage.cloud.google.com/
```

### Problem: "conversion_to_human_message is not a valid keyword argument"
```bash
# Your langchain-google-genai version is too old
# Solution: Update it
pip install --upgrade langchain-google-genai
```

---

## 🎯 Switching Between LLMs

To switch from Gemini to Claude (or vice versa):

### Option 1: Change .env
```bash
# Edit .env
LLM_PROVIDER=anthropic  # Changed from "gemini"
# Server will automatically use Claude next restart
```

### Option 2: Environment Variable
```bash
# At runtime (Linux/Mac)
export LLM_PROVIDER=anthropic
uvicorn backend.api.main:app --reload

# Or Windows PowerShell
$env:LLM_PROVIDER="anthropic"
uvicorn backend.api.main:app --reload
```

### Option 3: .env Override
```bash
# Create .env.gemini
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIza...

# Create .env.claude
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...

# Use specific env file
export $(cat .env.gemini | xargs)
uvicorn backend.api.main:app
```

---

## 📚 Documentation

- **Full System Architecture**: See `README.md`
- **Implementation Details**: See `IMPLEMENTATION_GUIDE.md`
- **API Reference**: See Swagger UI at `http://localhost:8000/docs`

---

## 🚀 Advanced: A/B Testing with Multiple LLMs

You can test both Gemini and Claude simultaneously:

### Create test script

```python
# test_gemini_vs_claude.py
from backend.config import Settings
from backend.workflows.rfp_graph import initialize_rfp_state, create_rfp_processing_graph
from backend.data.models import RFP_DATA

# Test with Gemini
import os
os.environ["LLM_PROVIDER"] = "gemini"
os.environ["GEMINI_API_KEY"] = "AIza..."

print("Testing with Gemini...")
state = initialize_rfp_state(RFP_DATA[0])
graph = create_rfp_processing_graph()
result_gemini = graph.invoke(state)
print(f"Gemini result: {result_gemini['consolidated_bid'].total_bid_value if result_gemini.get('consolidated_bid') else 'FAILED'}")

# Test with Claude
os.environ["LLM_PROVIDER"] = "anthropic"
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."

print("\nTesting with Claude...")
state = initialize_rfp_state(RFP_DATA[0])
graph = create_rfp_processing_graph()
result_claude = graph.invoke(state)
print(f"Claude result: {result_claude['consolidated_bid'].total_bid_value if result_claude.get('consolidated_bid') else 'FAILED'}")

# Compare
print(f"\nDifference: ₹{abs(result_gemini['consolidated_bid'].total_bid_value - result_claude['consolidated_bid'].total_bid_value):,}")
```

Run it:
```bash
python test_gemini_vs_claude.py
```

---

## 💡 Pro Tips

1. **Free Tier Access**: Gemini API has a generous free tier (60 requests/minute, 2M tokens/day)
2. **Upgrade When Needed**: If you hit limits, just enable paid API (pay-as-you-go)
3. **Model Comparison**: Try `gemini-1.5-pro` for complex RFPs, `gemini-2.0-flash` for standard ones
4. **Fallback Support**: System has Claude support built-in. If Gemini API is down, just switch to Claude

---

## 📞 Support

If you encounter issues:

1. Check the **Troubleshooting** section above
2. Verify your `.env` file has API key
3. Check API status: https://statuspage.cloud.google.com/
4. Review error logs: `tail -f logs/rfp_processing.log` (if logging enabled)

---

**Status: ✅ Gemini Integration Complete**

Your system now supports Gemini, Claude, and OpenAI LLMs with a single configuration change!

Switch between them anytime by changing `LLM_PROVIDER` in `.env`.
