"""
Configuration and Constants for RFP Processing System

Centralizes all configuration, environment variables, and business logic constants.
This module supports both development and production environments.
"""

import os
from typing import Dict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    Environment variables can override defaults. Load from .env file if present.
    """

    # ==================== API CONFIGURATION ====================
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # ==================== LANGCHAIN / LLM CONFIGURATION ====================
    # LLM Provider: "gemini" (recommended), "anthropic", or "openai"
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "gemini")

    # Gemini API Key
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

    # Anthropic API Key
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")

    # OpenAI API Key (alternative provider)
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # Model selection
    # Gemini options: gemini-2.0-flash (recommended), gemini-1.5-pro, gemini-1.5-flash
    # Claude options: claude-3-5-sonnet-20241022, claude-3-opus-20250219
    MODEL_NAME: str = os.getenv("MODEL_NAME", "gemini-2.0-flash")

    # Temperature for LLM responses (0.0 = deterministic, 1.0 = creative)
    LLM_TEMPERATURE: float = 0.3

    # Maximum tokens per agent response
    MAX_TOKENS: int = 2048

    # ==================== VECTOR DB CONFIGURATION ====================
    # FAISS embeddings model
    EMBEDDINGS_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Path to pre-computed FAISS index
    FAISS_INDEX_PATH: str = "backend/data/faiss_index.pkl"

    # Number of nearest neighbors to return in similarity search
    K_NEAREST_NEIGHBORS: int = 5

    # Minimum similarity threshold for SKU matching (0-1 scale)
    SIMILARITY_THRESHOLD: float = 0.4

    # ==================== RFP PROCESSING CONFIGURATION ====================
    # SMM (Spec Match Metric) threshold for technical compliance
    SMM_COMPLIANCE_THRESHOLD: float = 80.0  # Percentage

    # Maximum retry iterations for technical agent
    TECHNICAL_MAX_RETRIES: int = 3

    # How much to relax size criteria in each retry (mm²)
    SIZE_TOLERANCE_RELAXATION: float = 10.0

    # RFP qualification window (days into future)
    RFP_QUALIFICATION_WINDOW_DAYS: int = 90

    # ==================== PRICING CONFIGURATION ====================
    # Default profit margin multiplier (1.15 = 15% markup)
    TARGET_MARGIN: float = 1.15

    # Minimum viable margin (stop processing if below this)
    MINIMUM_MARGIN: float = 1.05

    # ==================== COMMODITY PRICING ====================
    # LME metal rates (USD per metric ton)
    # These are starting prices; can be updated via API
    LME_RATES: Dict[str, float] = {
        "Copper": 9200,      # USD/MT
        "Aluminium": 2400,   # USD/MT
    }

    # Currency conversion rate (USD to INR)
    USD_TO_INR_RATE: float = 83.0

    # ==================== TESTING & CERTIFICATION PRICING ====================
    # Service costs (INR) for compliance testing
    TEST_PRICING: Dict[str, float] = {
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

    # ==================== RISK ASSESSMENT CONFIGURATION ====================
    # Risk score calculation weights
    RISK_CONFIG: Dict[str, int] = {
        "urgent_deadline_days": 30,      # Days - score += 4 if < this
        "moderate_deadline_days": 60,    # Days - score += 2 if < this
        "bid_bond_penalty": 2,           # Risk points if bid bond required
        "ld_clause_penalty": 3,          # Risk points if LD clause present
        "high_margin_penalty": 1,        # Risk points if performance bond >= 10%
    }

    # ==================== LOGGING CONFIGURATION ====================
    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True
    LOG_FILE_PATH: str = "logs/rfp_processing.log"

    # ==================== ASYNC / CONCURRENCY ====================
    # Maximum concurrent RFP processing jobs
    MAX_CONCURRENT_JOBS: int = 5

    # Job timeout in seconds
    JOB_TIMEOUT_SECONDS: int = 300

    # ==================== CACHING ====================
    # Cache TTL for commodity prices (seconds)
    COMMODITY_CACHE_TTL: int = 3600  # 1 hour

    # Enable query result caching
    ENABLE_QUERY_CACHE: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# ==================== GLOBAL CONFIGURATION INSTANCE ====================
settings = Settings()


# ==================== HELPER FUNCTIONS ====================

def get_lme_rate(material: str) -> float:
    """
    Get current LME rate for a material.

    Args:
        material: Material name (Copper, Aluminium)

    Returns:
        Price in USD/MT

    Raises:
        ValueError: If material not found
    """
    if material not in settings.LME_RATES:
        raise ValueError(f"Unknown material: {material}. Available: {list(settings.LME_RATES.keys())}")
    return settings.LME_RATES[material]


def get_test_cost(test_name: str) -> float:
    """
    Get cost for a specific test or certification.

    Args:
        test_name: Name of the test/certification

    Returns:
        Cost in INR

    Raises:
        ValueError: If test not found
    """
    if test_name not in settings.TEST_PRICING:
        raise ValueError(f"Unknown test: {test_name}. Available: {list(settings.TEST_PRICING.keys())}")
    return settings.TEST_PRICING[test_name]


def update_lme_rate(material: str, new_rate: float) -> None:
    """
    Update LME rate for a material (typically called by pricing service).

    Args:
        material: Material name
        new_rate: New price in USD/MT
    """
    if material not in settings.LME_RATES:
        raise ValueError(f"Unknown material: {material}")
    settings.LME_RATES[material] = new_rate


def create_llm_chain():
    """
    Factory function to create LLM chain based on configured provider.

    Supports: Gemini, Claude (Anthropic), OpenAI

    Returns:
        Configured ChatModel instance

    Raises:
        ValueError: If required API key is not set or provider is unknown
    """
    provider = settings.LLM_PROVIDER.lower()

    if provider == "gemini":
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI

            if not settings.GEMINI_API_KEY:
                raise ValueError(
                    "GEMINI_API_KEY not set in environment. "
                    "Get it from: https://aistudio.google.com/app/apikeys"
                )

            return ChatGoogleGenerativeAI(
                model=settings.MODEL_NAME,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.MAX_TOKENS,
                google_api_key=settings.GEMINI_API_KEY,
                convert_system_message_to_human=True,  # Gemini-specific
            )
        except ImportError:
            raise ImportError(
                "langchain-google-genai not installed. "
                "Install with: pip install langchain-google-genai"
            )

    elif provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic

            if not settings.ANTHROPIC_API_KEY:
                raise ValueError(
                    "ANTHROPIC_API_KEY not set in environment. "
                    "Get it from: https://console.anthropic.com/api-keys"
                )

            return ChatAnthropic(
                model=settings.MODEL_NAME,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
                anthropic_api_key=settings.ANTHROPIC_API_KEY,
            )
        except ImportError:
            raise ImportError(
                "langchain-anthropic not installed. "
                "Install with: pip install langchain-anthropic"
            )

    elif provider == "openai":
        try:
            from langchain_openai import ChatOpenAI

            if not settings.OPENAI_API_KEY:
                raise ValueError(
                    "OPENAI_API_KEY not set in environment. "
                    "Get it from: https://platform.openai.com/api-keys"
                )

            return ChatOpenAI(
                model=settings.MODEL_NAME,
                temperature=settings.LLM_TEMPERATURE,
                max_tokens=settings.MAX_TOKENS,
                openai_api_key=settings.OPENAI_API_KEY,
            )
        except ImportError:
            raise ImportError(
                "langchain-openai not installed. "
                "Install with: pip install langchain-openai"
            )

    else:
        raise ValueError(
            f"Unknown LLM_PROVIDER: {settings.LLM_PROVIDER}. "
            "Supported: gemini, anthropic, openai"
        )


# ==================== SYSTEM PROMPTS FOR AGENTS ====================
# These prompts define the role and behavior of each agent

SALES_AGENT_SYSTEM_PROMPT = """You are the Sales Discovery Agent for an industrial RFP bidding platform.
Your role is Chief Market Intelligence Officer - scanning markets for high-value opportunities while
protecting the firm from commercial risks.

Core Responsibilities:
1. Qualify RFPs based on timeline, margin requirements, and commercial constraints
2. Calculate risk scores (1-10) considering:
   - Deadline urgency (< 30 days = high risk)
   - Commercial obligations (bid bonds, liquidated damages clauses)
   - Margin pressure (performance bonds, margin requirements)
3. Extract key metadata and commercial constraints from RFP documents
4. Flag high-risk scenarios for escalation to CBO

Decision Criteria:
- Accept: RFPs due within 90 days with acceptable risk profile
- Decline: RFPs with deadline < 7 days or risk score > 7/10 (escalate to manual)
- Escalate: Unusual terms requiring executive approval

Tone: Professional, risk-aware, commercial-savvy. Use structured language for decisions."""


TECHNICAL_AGENT_SYSTEM_PROMPT = """You are the Technical Agent for an industrial RFP bidding platform.
Your role is Senior Electrical Design Engineer - ensuring technical specs are met with precision while
protecting against non-compliance and using OEM inventory optimally.

Core Responsibilities:
1. Extract product specifications from RFP documents
2. Search OEM datasheet repository (FAISS vector DB) for matching SKUs
3. Calculate Spec Match Metric (SMM) based on weighted criteria:
   - Material: 30% weight (must match exactly)
   - Cores: 25% weight (must match exactly)
   - Size (mm²): 25% weight (SKU >= RFP requirement)
   - Insulation: 20% weight (must match exactly)
4. Implement retry logic if initial matches fail:
   - Iteration 1: Relax size tolerance by 10mm²
   - Iteration 2: Include "marginal" status SKUs (60% SMM)
   - Iteration 3: Flag for custom manufacturing

Decision Criteria:
- Accept: All lines >= 80% SMM
- Retry: Any line < 80% SMM (auto-attempt up to 3 times)
- Escalate: After 3 attempts, flag for manual engineering review

Tone: Technically precise, data-driven, quality-obsessed. Explain all matching decisions."""


PRICING_AGENT_SYSTEM_PROMPT = """You are the Pricing Agent for an industrial RFP bidding platform.
Your role is Industrial Financial Controller - optimizing margins while remaining competitive and
protecting against commodity volatility.

Core Responsibilities:
1. Calculate material costs using LME (London Metal Exchange) commodity indexing:
   - Base SKU price + (Metal Weight/1000) × LME Rate × Currency conversion
2. Add testing/certification costs based on RFP requirements
3. Apply risk premiums for commercial obligations (bid bonds, LD clauses)
4. Calculate final unit price with margin multiplier (default 15%)
5. Validate pricing meets: minimum margin (5%), margin targets, and business expectations

Decision Criteria:
- Accept: Achieves target margin with acceptable risk premium
- Revise: If margin too tight, flag for executive review
- Escalate: If commodity volatility makes pricing uncertain

Tone: Financially rigorous, margin-focused, risk-aware. Always explain cost components."""


BUSINESS_ADVISORY_SYSTEM_PROMPT = """You are the Business Advisory Agent for an industrial RFP bidding platform.
Your role is Strategic Management Consultant - quantifying bid value and competitive advantage.

Core Responsibilities:
1. Calculate operational savings (manual vs agentic process time/cost)
2. Perform sensitivity analysis: impact of ±10% commodity price changes
3. Quantify competitive advantage:
   - Speed to market (normally 48 hours, now 2 minutes)
   - Accuracy (manual ~85%, agentic 100% via weighted SMM)
   - Pricing protection via real-time commodity indexing
4. Assess strategic fit and recommend go/no-go

Output: ROI metrics, sensitivity tables, competitive positioning

Tone: Strategic, executive-focused, quantitative. Provide clear business case."""


ORCHESTRATOR_SYSTEM_PROMPT = """You are the Chief Bid Officer (CBO) - the decision-making orchestrator
for the multi-agent RFP bidding platform.

Core Responsibilities:
1. Route RFPs to appropriate agents in correct sequence
2. Manage conditional logic:
   - If technical compliance fails after 3 retries → escalate with reasons
   - If pricing constraints violated → request re-evaluation or manual override
   - If all constraints met → assemble final consolidated bid
3. Validate cross-agent consistency:
   - SKUs selected by Technical must match Pricing calculations
   - Risk premiums from Sales must be included in Pricing
   - Business advisory must reference confirmed pricing
4. Assemble ConsolidatedBid with complete audit trail
5. Make final go/no-go decision with justified reasoning

Decision Authority:
- Auto-approve: Risk score <= 5/10 AND all constraints met
- Request escalation: Risk score > 5/10 OR technical fallback OR pricing concerns
- Halt: Critical errors or missing data

Tone: Executive, decisive, risk-aware. Provide clear reasoning for all decisions."""


# ==================== EXPORT ====================
__all__ = [
    "settings",
    "Settings",
    "get_lme_rate",
    "get_test_cost",
    "update_lme_rate",
    "create_llm_chain",
    "SALES_AGENT_SYSTEM_PROMPT",
    "TECHNICAL_AGENT_SYSTEM_PROMPT",
    "PRICING_AGENT_SYSTEM_PROMPT",
    "BUSINESS_ADVISORY_SYSTEM_PROMPT",
    "ORCHESTRATOR_SYSTEM_PROMPT",
]
