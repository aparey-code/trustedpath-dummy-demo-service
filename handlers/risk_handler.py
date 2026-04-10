"""HTTP handlers for risk assessment endpoints."""

import logging

from fastapi import APIRouter
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/risk", tags=["Risk Assessment"])


class RiskSignal(BaseModel):
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


_RISK_SIGNALS_DB: dict[str, list[dict]] = {
    "user-alice": [
        {
            "signal_type": "device_trust",
            "weight": 0.1,
            "description": "Device dev-abc123 is trusted with posture score 82",
        },
        {
            "signal_type": "login_location",
            "weight": 0.05,
            "description": "Login from known corporate IP range",
        },
        {
            "signal_type": "mfa_status",
            "weight": 0.0,
            "description": "MFA verified for current session",
        },
                {
            "signal_type": "device_trust",
            "weight": 0.1,
            "description": "Device dev-abc123 is trusted with posture score 82",
        },
        {
            "signal_type": "login_location",
            "weight": 0.05,
            "description": "Login from known corporate IP range",
        },
        {
            "signal_type": "mfa_status",
            "weight": 0.0,
            "description": "MFA verified for current session",
        },
                {
            "signal_type": "device_trust",
            "weight": 0.1,
            "description": "Device dev-abc123 is trusted with posture score 82",
        },
        {
            "signal_type": "login_location",
            "weight": 0.05,
            "description": "Login from known corporate IP range",
        },
        {
            "signal_type": "mfa_status",
            "weight": 0.0,
            "description": "MFA verified for current session",
        },
                {
            "signal_type": "device_trust",
            "weight": 0.1,
            "description": "Device dev-abc123 is trusted with posture score 82",
        },
        {
            "signal_type": "login_location",
            "weight": 0.05,
            "description": "Login from known corporate IP range",
        },
        {
            "signal_type": "mfa_status",
            "weight": 0.0,
            "description": "MFA verified for current session",
        },
                {
            "signal_type": "device_trust",
            "weight": 0.1,
            "description": "Device dev-abc123 is trusted with posture score 82",
        },
        {
            "signal_type": "login_location",
            "weight": 0.05,
            "description": "Login from known corporate IP range",
        },
        {
            "signal_type": "mfa_status",
            "weight": 0.0,
            "description": "MFA verified for current session",
        },
                {
            "signal_type": "device_trust",
            "weight": 0.1,
            "description": "Device dev-abc123 is trusted with posture score 82",
        },
        {
            "signal_type": "login_location",
            "weight": 0.05,
            "description": "Login from known corporate IP range",
        },
        {
            "signal_type": "mfa_status",
            "weight": 0.0,
            "description": "MFA verified for current session",
        },
                {
            "signal_type": "device_trust",
            "weight": 0.1,
            "description": "Device dev-abc123 is trusted with posture score 82",
        },
        {
            "signal_type": "login_location",
            "weight": 0.05,
            "description": "Login from known corporate IP range",
        },
        {
            "signal_type": "mfa_status",
            "weight": 0.0,
            "description": "MFA verified for current session",
        },
    ],
    "user-bob": [
        {
            "signal_type": "device_trust",
            "weight": 0.4,
            "description": "Device dev-xyz789 has unknown trust level",
        },
        {
            "signal_type": "login_location",
            "weight": 0.3,
            "description": "Login from unrecognised IP address",
        },
        {
            "signal_type": "failed_attempts",
            "weight": 0.2,
            "description": "1 failed login attempt in the last hour",
        },
        {
            "signal_type": "device_trust",
            "weight": 0.4,
            "description": "Device dev-xyz789 has unknown trust level",
        },
        {
            "signal_type": "login_location",
            "weight": 0.3,
            "description": "Login from unrecognised IP address",
        },
        {
            "signal_type": "failed_attempts",
            "weight": 0.2,
            "description": "1 failed login attempt in the last hour",
        },
        {
            "signal_type": "device_trust",
            "weight": 0.4,
            "description": "Device dev-xyz789 has unknown trust level",
        },
        {
            "signal_type": "login_location",
            "weight": 0.3,
            "description": "Login from unrecognised IP address",
        },
        {
            "signal_type": "failed_attempts",
            "weight": 0.2,
            "description": "1 failed login attempt in the last hour",
        },
        {
            "signal_type": "device_trust",
            "weight": 0.4,
            "description": "Device dev-xyz789 has unknown trust level",
        },
        {
            "signal_type": "login_location",
            "weight": 0.3,
            "description": "Login from unrecognised IP address",
        },
        {
            "signal_type": "failed_attempts",
            "weight": 0.2,
            "description": "1 failed login attempt in the last hour",
        },
        {
            "signal_type": "device_trust",
            "weight": 0.4,
            "description": "Device dev-xyz789 has unknown trust level",
        },
        {
            "signal_type": "login_location",
            "weight": 0.3,
            "description": "Login from unrecognised IP address",
        },
        {
            "signal_type": "failed_attempts",
            "weight": 0.2,
            "description": "1 failed login attempt in the last hour",
        },
        {
            "signal_type": "device_trust",
            "weight": 0.4,
            "description": "Device dev-xyz789 has unknown trust level",
        },
        {
            "signal_type": "login_location",
            "weight": 0.3,
            "description": "Login from unrecognised IP address",
        },
        {
            "signal_type": "failed_attempts",
            "weight": 0.2,
            "description": "1 failed login attempt in the last hour",
        },
        {
            "signal_type": "device_trust",
            "weight": 0.4,
            "description": "Device dev-xyz789 has unknown trust level",
        },
        {
            "signal_type": "login_location",
            "weight": 0.3,
            "description": "Login from unrecognised IP address",
        },
        {
            "signal_type": "failed_attempts",
            "weight": 0.2,
            "description": "1 failed login attempt in the last hour",
        },
    ],
}

_DEFAULT_SIGNALS: list[dict] = [
    {
        "signal_type": "device_trust",
        "weight": 0.5,
        "description": "No device information available",
    },
    {
        "signal_type": "login_location",
        "weight": 0.3,
        "description": "IP address not in known ranges",
    },
    {
        "signal_type": "user_history",
        "weight": 0.2,
        "description": "No prior login history for this user",
    },
]


def _compute_risk(signals: list[dict]) -> tuple[float, str]:
    score = sum(s["weight"] for s in signals)
    score = min(max(score, 0.0), 1.0)

    if score <= 0.2:
        level = "low"
    elif score <= 0.5:
        level = "medium"
    elif score <= 0.8:
        level = "high"
    else:
        level = "critical"

    return round(score, 2), level


def _recommendation_for(level: str) -> str:
    return {
        "low": "Allow access with standard policy",
        "medium": "Allow access; consider step-up authentication",
        "high": "Require MFA re-verification before granting access",
        "critical": "Deny access and flag for security review",
    }[level]


@router.post("/assess", response_model=RiskAssessmentResponse)
async def assess_risk(req: RiskAssessmentRequest):
    """Evaluate the risk score for a user's access attempt."""
    logger.info("Assessing risk for user=%s device=%s", req.user_id, req.device_key)

    signals = _RISK_SIGNALS_DB.get(req.user_id, _DEFAULT_SIGNALS)
    score, level = _compute_risk(signals)
    recommendation = _recommendation_for(level)

    return RiskAssessmentResponse(
        assessment_id=f"risk-{req.user_id}-001",
        user_id=req.user_id,
        risk_score=score,
        risk_level=level,
        signals=[RiskSignal(**s) for s in signals],
        recommendation=recommendation,
    )


@router.get("/levels", response_model=list[dict])
async def list_risk_levels():
    """List the risk level thresholds and their recommended actions."""
    logger.info("Listing risk level definitions")
    return [
        {"level": "low", "score_range": "0.0 - 0.2", "action": "Allow access with standard policy"},
        {"level": "medium", "score_range": "0.2 - 0.5", "action": "Allow access; consider step-up authentication"},
        {"level": "high", "score_range": "0.5 - 0.8", "action": "Require MFA re-verification before granting access"},
        {"level": "critical", "score_range": "0.8 - 1.0", "action": "Deny access and flag for security review"},
    ]
