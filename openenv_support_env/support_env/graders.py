from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

from .models import Action, TaskSpec
from .scenarios import TASKS


@dataclass(frozen=True)
class GraderResult:
    task_id: str
    score: float
    details: Dict[str, float]


def grade_easy(actions: List[Action], task: TaskSpec) -> GraderResult:
    gold = task.tickets
    cat = sum(1 for a, t in zip(actions, gold) if a.category == t.gold_category) / len(gold)
    priority = sum(1 for a, t in zip(actions, gold) if a.priority == t.gold_priority) / len(gold)
    route = sum(1 for a, t in zip(actions, gold) if a.route_to == t.gold_route) / len(gold)
    score = 0.55 * cat + 0.25 * priority + 0.20 * route
    return GraderResult(task.task_id, round(score, 6), {"category": cat, "priority": priority, "route": route})


def grade_medium(actions: List[Action], task: TaskSpec) -> GraderResult:
    gold = task.tickets
    base = []
    for a, t in zip(actions, gold):
        local = 0.0
        local += 0.25 if a.category == t.gold_category else 0.0
        local += 0.15 if a.priority == t.gold_priority else 0.0
        local += 0.20 if a.route_to == t.gold_route else 0.0
        local += 0.15 if a.response_type == t.gold_response_type else 0.0
        local += 0.15 if a.reply_text and len(a.reply_text.split()) >= 8 else 0.0
        local += 0.10 if not a.close_ticket or t.allow_close else 0.0
        base.append(min(1.0, local))
    score = sum(base) / len(base)
    return GraderResult(task.task_id, round(score, 6), {f"ticket_{i}": s for i, s in enumerate(base)})


def grade_hard(actions: List[Action], task: TaskSpec) -> GraderResult:
    gold = task.tickets
    per_ticket = []
    for a, t in zip(actions, gold):
        local = 0.0
        local += 0.20 if a.category == t.gold_category else 0.0
        local += 0.12 if a.priority == t.gold_priority else 0.0
        local += 0.15 if a.route_to == t.gold_route else 0.0
        local += 0.15 if a.response_type == t.gold_response_type else 0.0
        if a.reply_text:
            reply = a.reply_text.lower()
            kw_hits = sum(1 for kw in t.critical_keywords if kw.lower() in reply)
            local += min(0.22, 0.11 * kw_hits)
            local += 0.06 if any(word in reply for word in ["sorry", "thanks", "appreciate", "please"]) else 0.0
        local += 0.10 if not a.close_ticket else (-0.12 if not t.allow_close else 0.04)
        per_ticket.append(max(0.0, min(1.0, local)))
    score = sum(per_ticket) / len(per_ticket)
    return GraderResult(task.task_id, round(score, 6), {f"ticket_{i}": s for i, s in enumerate(per_ticket)})


GRADERS: Dict[str, Callable[[List[Action], TaskSpec], GraderResult]] = {
    "ticket_triage_easy": grade_easy,
    "ticket_triage_medium": grade_medium,
    "ticket_triage_hard": grade_hard,
}


def grade_task(task_id: str, actions: List[Action]) -> GraderResult:
    if task_id not in TASKS:
        raise ValueError(f"Unknown task_id: {task_id}")
    task = TASKS[task_id]
    grader = GRADERS[task_id]
    return grader(actions, task)

