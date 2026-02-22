"""
Risk Assessment Tool - Commercial Risk Scoring

Calculates risk scores (1-10) based on RFP commercial constraints.
Used by Sales Agent for lead qualification and prioritization.
"""

from typing import Dict, Any
from datetime import datetime

from backend.config import settings
from backend.state import QualifiedRFP


def assess_rfp_risk(
    due_date: str,
    bid_bond_required: bool = False,
    liquidated_damages_clause: bool = False,
    performance_bond_percent: float = 0.0,
) -> Dict[str, Any]:
    """
    Calculate commercial risk score for an RFP (1-10 scale).

    Scoring Logic:
    - Deadline urgency: < 30 days = +4 points, < 60 days = +2 points
    - Bid bond required: + 2 points
    - Liquidated damages clause: + 3 points
    - Performance bond >= 10%: + 1 point

    Args:
        due_date: Due date (ISO format string, e.g., "2025-04-15")
        bid_bond_required: Whether bid bond is required
        liquidated_damages_clause: Whether LD clause is present
        performance_bond_percent: Performance guarantee percentage

    Returns:
        Dictionary with:
        - risk_score: Overall risk (1-10 scale)
        - risk_level: Qualitative level (LOW, MEDIUM, HIGH, CRITICAL)
        - risk_factors: List of factors contributing to score
        - recommendation: Go/No-Go recommendation
        - days_to_deadline: Days remaining until due date

    Example:
        >>> risk_dict = assess_rfp_risk(
        ...     due_date="2025-04-15",
        ...     bid_bond_required=True,
        ...     liquidated_damages_clause=False,
        ...     performance_bond_percent=10.0
        ... )
        >>> print(f"Risk Score: {risk_dict['risk_score']}/10")
        >>> print(f"Recommendation: {risk_dict['recommendation']}")
    """
    try:
        # Calculate days remaining
        due_datetime = datetime.fromisoformat(due_date)
        today = datetime.now()
        days_remaining = (due_datetime - today).days

        risk_score = 0
        risk_factors = []

        # Deadline urgency scoring
        config = settings.RISK_CONFIG
        if days_remaining < config["urgent_deadline_days"]:
            risk_score += config["urgent_deadline_days_penalty"] if "urgent_deadline_days_penalty" in config else 4
            risk_factors.append(f"URGENT: Deadline in {days_remaining} days (< 30)")
        elif days_remaining < config["moderate_deadline_days"]:
            risk_score += config["moderate_deadline_days_penalty"] if "moderate_deadline_days_penalty" in config else 2
            risk_factors.append(f"ACCELERATED: Deadline in {days_remaining} days (< 60)")

        # Commercial obligations
        if bid_bond_required:
            risk_score += config["bid_bond_penalty"]
            risk_factors.append("Bid bond required")

        if liquidated_damages_clause:
            risk_score += config["ld_clause_penalty"]
            risk_factors.append("Liquidated damages clause present")

        if performance_bond_percent >= 10:
            risk_score += config["high_margin_penalty"]
            risk_factors.append(f"High performance bond: {performance_bond_percent}%")

        # Cap at 10
        risk_score = min(risk_score, 10)

        # Determine risk level
        if risk_score <= 2:
            risk_level = "LOW"
            recommendation = "ACCEPT - Clear pathway to bid"
        elif risk_score <= 5:
            risk_level = "MEDIUM"
            recommendation = "ACCEPT - Evaluate commercial terms"
        elif risk_score <= 7:
            risk_level = "HIGH"
            recommendation = "ESCALATE - Requires management review"
        else:
            risk_level = "CRITICAL"
            recommendation = "DECLINE - Commercial risks exceed threshold"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "days_to_deadline": days_remaining,
            "risk_factors": risk_factors,
            "recommendation": recommendation,
            "bid_bond_required": bid_bond_required,
            "liquidated_damages_clause": liquidated_damages_clause,
            "performance_bond_percent": performance_bond_percent,
        }

    except ValueError as e:
        return {"error": f"Invalid due date format: {str(e)}"}
    except Exception as e:
        return {"error": f"Risk assessment failed: {str(e)}"}


def get_risk_thresholds() -> Dict[str, Any]:
    """
    Return the risk scoring configuration.

    Useful for understanding what triggers high/low risk scores.
    """
    return {
        "thresholds": {
            "urgent_deadline_days": settings.RISK_CONFIG["urgent_deadline_days"],
            "moderate_deadline_days": settings.RISK_CONFIG["moderate_deadline_days"],
            "bid_bond_penalty": settings.RISK_CONFIG["bid_bond_penalty"],
            "ld_clause_penalty": settings.RISK_CONFIG["ld_clause_penalty"],
            "high_margin_penalty": settings.RISK_CONFIG["high_margin_penalty"],
        },
        "qualification_window_days": settings.RFP_QUALIFICATION_WINDOW_DAYS,
        "risk_level_mapping": {
            "0-2": "LOW (Accept)",
            "3-5": "MEDIUM (Accept with review)",
            "6-7": "HIGH (Escalate)",
            "8-10": "CRITICAL (Decline/Manual)",
        },
    }


# ==================== EXPORT ====================
__all__ = [
    "assess_rfp_risk",
    "get_risk_thresholds",
]
