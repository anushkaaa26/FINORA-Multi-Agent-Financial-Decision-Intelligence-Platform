from typing import Annotated, Any, Literal
from operator import add
from pydantic import BaseModel, Field
from typing_extensions import TypedDict


class Signal(BaseModel):
    name: str
    raw_value: float
    mapped_score: float
    weight: float
    direction: str


class Params(BaseModel):
    ticker: str
    horizon_months: int = 12
    amount_inr: float | None = 500000.0
    risk_profile: Literal["conservative", "balanced", "aggressive"] = "balanced"


class AgentResult(BaseModel):
    agent: str
    status: Literal["ok", "partial", "failed"] = "ok"
    metrics: dict[str, float | None] = Field(default_factory=dict)
    score: float | None = None
    signals: list[Signal] = Field(default_factory=list)
    narrative: str | None = None
    tool_call_ids: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class FilingsEvidenceItem(BaseModel):
    doc_id: str
    page: int
    section: str
    excerpt: str
    relevance: float
    source_url: str

class FilingsEvidence(BaseModel):
    items: list[FilingsEvidenceItem] = Field(default_factory=list)




class ScenarioResult(BaseModel):
    amount_inr: float
    horizon_months: int
    p5: float
    p50: float
    p95: float
    label: str = "historical simulation, not a forecast"


class ReviewResult(BaseModel):
    passed: bool
    violations: list[str] = Field(default_factory=list)


class DecisionReport(BaseModel):
    ticker: str
    evidence_balance: float
    confidence: float
    supporting_factors: list[str] = Field(default_factory=list)
    risk_factors: list[str] = Field(default_factory=list)
    scenario_summary: str = ""
    confidence_explanation: str = ""
    limitations: list[str] = Field(default_factory=list)


class Event(BaseModel):
    type: str
    agent: str
    status: str
    label: str
    detail: dict[str, Any] = Field(default_factory=dict)


class InvestigationState(TypedDict):
    session_id: str
    question: str
    params: Params
    market: AgentResult | None
    fundamentals: AgentResult | None
    risk: AgentResult | None
    filings: FilingsEvidence | None
    scenario: ScenarioResult | None
    decision: DecisionReport | None
    review: ReviewResult | None
    events: Annotated[list[Event], add]