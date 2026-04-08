from __future__ import annotations

from dataclasses import asdict
from typing import Dict, List, Optional, Tuple

from .models import Action, EnvState, Observation, Reward, TaskSpec, TicketScenario
from .scenarios import TASKS


class SupportTicketEnv:
    """A deterministic support-ticket environment with real-world workflow semantics.

    One episode corresponds to one task spec. The agent processes the task's ticket
    queue sequentially, making one decision per ticket.
    """

    def __init__(self, task_id: str = "ticket_triage_easy", max_steps: Optional[int] = None):
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id: {task_id}")
        self.task: TaskSpec = TASKS[task_id]
        self.max_steps = max_steps or len(self.task.tickets)
        self._step_index = 0
        self._done = False
        self._cumulative_score = 0.0
        self._routed_tickets: List[str] = []
        self._closed_tickets: List[str] = []
        self._history: List[str] = []
        self._last_reward: Optional[Reward] = None

    @property
    def current_ticket(self) -> TicketScenario:
        return self.task.tickets[self._step_index]

    def reset(self) -> Observation:
        self._step_index = 0
        self._done = False
        self._cumulative_score = 0.0
        self._routed_tickets = []
        self._closed_tickets = []
        self._history = []
        self._last_reward = None
        return self._build_observation()

    def state(self) -> EnvState:
        current_ticket_id = None if self._done else self.current_ticket.ticket_id
        return EnvState(
            task_id=self.task.task_id,
            step_index=self._step_index,
            total_tickets=len(self.task.tickets),
            cumulative_score=round(self._cumulative_score, 6),
            done=self._done,
            current_ticket_id=current_ticket_id,
            routed_tickets=list(self._routed_tickets),
            closed_tickets=list(self._closed_tickets),
        )

    def step(self, action: Action) -> Tuple[Optional[Observation], Reward, bool, Dict[str, object]]:
        if self._done:
            raise RuntimeError("Episode already finished. Call reset() to start a new episode.")

        ticket = self.current_ticket
        reward, breakdown, feedback = self._score_action(ticket, action)
        self._cumulative_score += reward
        self._history.append(
            f"{ticket.ticket_id}:{action.category}/{action.priority}/{action.route_to}/{action.response_type}"
        )
        self._routed_tickets.append(action.route_to)
        if action.close_ticket:
            self._closed_tickets.append(ticket.ticket_id)

        self._step_index += 1
        if self._step_index >= min(self.max_steps, len(self.task.tickets)):
            self._done = True
            next_obs = None
        else:
            next_obs = self._build_observation()

        reward_model = Reward(score=round(reward, 6), breakdown=breakdown, feedback=feedback)
        self._last_reward = reward_model
        info = {
            "task_id": self.task.task_id,
            "ticket_id": ticket.ticket_id,
            "gold": {
                "category": ticket.gold_category,
                "priority": ticket.gold_priority,
                "route_to": ticket.gold_route,
                "response_type": ticket.gold_response_type,
            },
            "state": self.state().model_dump(),
        }
        return next_obs, reward_model, self._done, info

    def _build_observation(self) -> Observation:
        ticket = self.current_ticket
        return Observation(
            task_id=self.task.task_id,
            ticket_index=self._step_index,
            total_tickets=len(self.task.tickets),
            subject=ticket.subject,
            body=ticket.body,
            customer_tier=ticket.customer_tier,
            customer_sentiment=ticket.customer_sentiment,
            prior_interactions=list(ticket.prior_interactions),
            allowed_categories=[
                "billing",
                "account_access",
                "bug_report",
                "feature_request",
                "cancellation",
                "security",
                "spam",
                "other",
            ],
            allowed_priorities=["low", "normal", "high", "urgent"],
            allowed_routes=["billing", "support", "engineering", "retention", "security", "archive"],
            allowed_response_types=[
                "acknowledge",
                "ask_clarify",
                "provide_solution",
                "escalate",
                "offer_retention",
                "deny_request",
                "no_reply",
            ],
        )

    def _score_action(self, ticket: TicketScenario, action: Action) -> Tuple[float, Dict[str, float], str]:
        breakdown: Dict[str, float] = {}

        def exact_match(name: str, predicted: str, gold: str, weight: float) -> float:
            score = weight if predicted == gold else 0.0
            breakdown[name] = round(score, 4)
            return score

        score = 0.0
        score += exact_match("category", action.category, ticket.gold_category, 0.26)
        score += exact_match("priority", action.priority, ticket.gold_priority, 0.16)
        score += exact_match("route_to", action.route_to, ticket.gold_route, 0.18)
        score += exact_match("response_type", action.response_type, ticket.gold_response_type, 0.16)

        reply_score = self._reply_quality(action.reply_text, ticket.reference_reply, ticket.critical_keywords)
        breakdown["reply_quality"] = round(reply_score, 4)
        score += reply_score * 0.18

        if action.close_ticket and not ticket.allow_close:
            breakdown["unsafe_close_penalty"] = -0.18
            score -= 0.18
        elif action.close_ticket and ticket.allow_close:
            breakdown["close_bonus"] = 0.06
            score += 0.06

        if action.route_to == "archive" and ticket.gold_category != "spam":
            breakdown["misroute_penalty"] = -0.14
            score -= 0.14

        if action.response_type == "no_reply" and ticket.gold_response_type != "no_reply":
            breakdown["missing_reply_penalty"] = -0.12
            score -= 0.12

        if action.category == "spam" and ticket.gold_category != "spam":
            breakdown["false_spam_penalty"] = -0.1
            score -= 0.1

        score = max(-1.0, min(1.0, score))
        feedback = self._compose_feedback(ticket, action, score)
        return score, breakdown, feedback

    @staticmethod
    def _reply_quality(reply_text: Optional[str], reference_reply: str, keywords: List[str]) -> float:
        if not reply_text:
            return 0.0
        reply = reply_text.lower()
        ref = reference_reply.lower()
        keyword_hits = sum(1 for kw in keywords if kw.lower() in reply)
        keyword_score = keyword_hits / max(len(keywords), 1)
        polite_bonus = 0.2 if any(p in reply for p in ["thanks", "sorry", "appreciate", "please"]) else 0.0
        coverage = 0.0
        for token in ["help", "review", "route", "escalate", "confirm", "refund", "access", "policy"]:
            if token in reply:
                coverage += 0.03
        length_penalty = 0.0 if 20 <= len(reply.split()) <= 80 else 0.12
        reference_overlap = 0.0
        ref_tokens = set(ref.split())
        if ref_tokens:
            common = len(set(reply.split()) & ref_tokens)
            reference_overlap = min(0.25, common / max(len(ref_tokens), 1) * 0.25)
        raw = 0.35 * keyword_score + polite_bonus + coverage + reference_overlap - length_penalty
        return max(0.0, min(1.0, raw))

    @staticmethod
    def _compose_feedback(ticket: TicketScenario, action: Action, score: float) -> str:
        notes = []
        if action.category != ticket.gold_category:
            notes.append(f"category should be {ticket.gold_category}")
        if action.priority != ticket.gold_priority:
            notes.append(f"priority should be {ticket.gold_priority}")
        if action.route_to != ticket.gold_route:
            notes.append(f"route_to should be {ticket.gold_route}")
        if action.response_type != ticket.gold_response_type:
            notes.append(f"response_type should be {ticket.gold_response_type}")
        if action.close_ticket and not ticket.allow_close:
            notes.append("ticket should stay open")
        if not notes:
            notes.append("ticket handled well")
        return f"Score {score:.3f}: " + "; ".join(notes)

