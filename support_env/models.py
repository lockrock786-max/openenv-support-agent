from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field


TicketCategory = Literal[
    "billing",
    "account_access",
    "bug_report",
    "feature_request",
    "cancellation",
    "security",
    "spam",
    "other",
]

Priority = Literal["low", "normal", "high", "urgent"]
Route = Literal["billing", "support", "engineering", "retention", "security", "archive"]
ResponseType = Literal[
    "acknowledge",
    "ask_clarify",
    "provide_solution",
    "escalate",
    "offer_retention",
    "deny_request",
    "no_reply",
]


class Observation(BaseModel):
    """Public observation exposed to the agent at each step."""

    task_id: str
    ticket_index: int
    total_tickets: int
    subject: str
    body: str
    customer_tier: Literal["free", "pro", "enterprise"]
    customer_sentiment: Literal["calm", "frustrated", "angry"]
    prior_interactions: List[str] = Field(default_factory=list)
    allowed_categories: List[TicketCategory]
    allowed_priorities: List[Priority]
    allowed_routes: List[Route]
    allowed_response_types: List[ResponseType]


class Action(BaseModel):
    """Agent action for a single support ticket."""

    category: TicketCategory
    priority: Priority
    route_to: Route
    response_type: ResponseType
    reply_text: Optional[str] = None
    close_ticket: bool = False


class Reward(BaseModel):
    """Scalar reward plus an interpretable breakdown."""

    score: float = Field(ge=-1.0, le=1.0)
    breakdown: Dict[str, float] = Field(default_factory=dict)
    feedback: str


class EnvState(BaseModel):
    """Internal state for debugging and reproducibility."""

    task_id: str
    step_index: int
    total_tickets: int
    cumulative_score: float
    done: bool
    current_ticket_id: Optional[str] = None
    routed_tickets: List[str] = Field(default_factory=list)
    closed_tickets: List[str] = Field(default_factory=list)


class TicketScenario(BaseModel):
    """A realistic support ticket with gold labels for grading."""

    ticket_id: str
    subject: str
    body: str
    customer_tier: Literal["free", "pro", "enterprise"]
    customer_sentiment: Literal["calm", "frustrated", "angry"]
    prior_interactions: List[str] = Field(default_factory=list)
    gold_category: TicketCategory
    gold_priority: Priority
    gold_route: Route
    gold_response_type: ResponseType
    reference_reply: str
    allow_close: bool = False
    critical_keywords: List[str] = Field(default_factory=list)


class TaskSpec(BaseModel):
    task_id: str
    name: str
    difficulty: Literal["easy", "medium", "hard"]
    description: str
    tickets: List[TicketScenario]

