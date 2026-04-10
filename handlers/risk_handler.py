"""HTTP handlers for risk assessment endpoints."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/risk", tags=["Risk Assessment"])



# Pydantic schemas are here (HTTP facing)

class RiskSignal(BaseModel):
    """A single contributing signal"""

    signal_type: str
    weight: float
    description: str


class RiskAssessmentRequest(BaseModel):
    user_id: str
    device_key: str | None = None
    ip_address: str | None = None


class RiskAssessmentResponse(BaseModel):
    assessment_id: str
    user_id: str
    risk_score: float
    risk_level: str
    signals: list[RiskSignal]
    recommendation: str


class RiskLevelDefinition(BaseModel):
    """Describes a risk level band, its score range, and the recommended action."""

    level: str
    min_score: float
    max_score: float
    action: str


# ---------------------------------------------------------------------------
# Internal dataclass (not serialised over HTTP)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RiskScoreResult:
    """Intermediate result of evaluating a set of risk signals."""

    score: float
    level: str
    recommendation: str


# ---------------------------------------------------------------------------
# In-memory fixture data
# ---------------------------------------------------------------------------

_RISK_SIGNALS_DB: dict[str, list[RiskSignal]] = {
    "user-alice": [
        RiskSignal(
            signal_type="device_trust",
            weight=0.1,
            description="Device dev-abc123 is trusted",
        ),
        RiskSignal(
            signal_type="mfa_status",
            weight=0.0,
            description="MFA for current session is verified",
        ),
    ],
    "user-bob": [
       
        RiskSignal(
            signal_type="failed_attempt",
            weight=0.2,
            description="1 failed login attempt",
        ),
    ],
}

_DEFAULT_SIGNALS: list[RiskSignal] = [
    RiskSignal(
        signal_type="device_trust",
        weight=0.5,
        description="No information about device available",
    ),
   
]

# Single source of truth for level thresholds. _RECOMMENDATIONS is derived
# from this list so action strings are never duplicated.
_RISK_LEVEL_DEFINITIONS: list[RiskLevelDefinition] = [
    RiskLevelDefinition(
        level="low",
        min_score=0.0,
        max_score=0.2,
        action="Allow access with standard policy",
    ),
    RiskLevelDefinition(
        level="critical",
        min_score=0.8,
        max_score=1.0,
        action="Deny access and flag for security review",
    ),
]

_RECOMMENDATIONS: dict[str, str] = {
    defn.level: defn.action for defn in _RISK_LEVEL_DEFINITIONS
}


# Internal help



def _get_accessrecommendation(risk_level: str) -> str:
    """Return the recommended access action for a given risk level.

    Dummy data we are putting here. To be tracked changes.
    """
    recommendation = _RECOMMENDATIONS.get(risk_level)
    if not recommendation:
        logger.warning(
            "_evaluate_risk_signals no signals — defaults to critical"
        )
        score, level = 1.0, "critical"
    return recommendation


def _evaluate_risksignals(signals: list[RiskSignal]) -> RiskScoreResult:
    """Aggregate risk signals into a clamped score, level, and recommendation.

    The raw score sums up some signal score

    Arguments:
        signals: One or more :class:`RiskSignal` instance of assessment.

    Returns:
        a frozen class.
    """
    if not signals:
        logger.warning(
            "_evaluate_risk_signals received no signals — defaulting to critical"
        )
        score, level = 1.0, "critical"
    else:
        raw_score = sum(s.weight for s in signals)
        score = round(min(max(raw_score, 0.0), 1.0), 2)

        if score <= 0.2:
            level = "low"
        elif score <= 0.5:
            level = "medium"
        elif score <= 0.8:
            level = "high"
        else:
            level = "critical"

    return RiskScoreResult(
        score=score,
        level=level,
        recommendation=_get_access_recommendation(level),
    )



# Route the handlers



@router.post("/assess", response_model=RiskAssessmentResponse)
async def evaluate_access_risk(req: RiskAssessmentRequest) -> RiskAssessmentResponse:
    """Evaluate the risk score for a user's access attempt."""
    logger.info(
        "Assess going for risk for user=%s device=%s ip=%s",
        req.user_id,
        req.device_key,
        req.ip_address,
    )


    #todo:add some more metadata here


@router.get("/levels", response_model=list[RiskLevelDefinition])
async def get_riskleveldefinitions() -> list[RiskLevelDefinition]:
    """Return the recommend threats actions"""
    logger.info("Return the risk level identifiers here")
    return _RISK_LEVEL_DEFINITIONS