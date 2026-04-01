from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import List, Optional

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from support_env import Action, SupportTicketEnv, TASKS, grade_task


RULES = {
    "billing": {
        "route_to": "billing",
        "response_type": "provide_solution",
        "priority": "high",
    },
    "account_access": {
        "route_to": "support",
        "response_type": "ask_clarify",
        "priority": "urgent",
    },
    "bug_report": {
        "route_to": "engineering",
        "response_type": "escalate",
        "priority": "high",
    },
    "feature_request": {
        "route_to": "engineering",
        "response_type": "acknowledge",
        "priority": "low",
    },
    "cancellation": {
        "route_to": "retention",
        "response_type": "offer_retention",
        "priority": "high",
    },
    "security": {
        "route_to": "security",
        "response_type": "escalate",
        "priority": "urgent",
    },
    "spam": {
        "route_to": "archive",
        "response_type": "no_reply",
        "priority": "low",
    },
    "other": {
        "route_to": "support",
        "response_type": "acknowledge",
        "priority": "normal",
    },
}


def heuristic_action(obs) -> Action:
    text = f"{obs.subject} {obs.body}".lower()
    # Order matters: specific patterns first, then broader routing signals.
    if any(k in text for k in ["security", "suspicious", "whitelist", "unauthorized"]):
        category = "security"
    elif any(k in text for k in ["refund denied", "charged twice", "duplicate charge", "invoice", "receipt"]):
        category = "billing"
    elif any(k in text for k in ["mfa", "authenticator", "login", "sign in", "password", "access"]):
        category = "account_access"
    elif any(k in text for k in ["feature", "suggestion", "wish", "shortcut", "idea"]):
        category = "feature_request"
    elif any(k in text for k in ["crash", "error", "bug", "fails", "failed", "upload", "deliverability", "newsletter", "landing in spam", "product updates", "remediation plan"]):
        category = "bug_report"
    elif any(k in text for k in ["cancel", "cancellation", "renewal", "downgrade", "leave"]):
        category = "cancellation"
    elif any(k in text for k in ["spam", "lottery", "win", "click here"]):
        category = "spam"
    else:
        category = "other"

    base = RULES[category]
    reply = None
    if base["response_type"] == "provide_solution":
        reply = (
            "Thanks for reaching out. I will review the billing record, confirm the charge history, "
            "and help resolve the issue as quickly as possible."
        )
    elif base["response_type"] == "ask_clarify":
        reply = (
            "Thanks for the update. Please share one more detail so I can route the fastest fix path."
        )
    elif base["response_type"] == "escalate":
        reply = (
            "Thank you for the report. I am escalating this to the relevant team for review and next steps."
        )
    elif base["response_type"] == "offer_retention":
        reply = (
            "I understand. I can help review the renewal options and keep the plan aligned with your needs."
        )
    elif base["response_type"] == "acknowledge":
        reply = (
            "Thanks for the suggestion. I have logged it for review by the product team."
        )
    elif base["response_type"] == "deny_request":
        reply = (
            "I understand the request. Based on policy, I cannot approve that refund, but I can explain the timeline."
        )

    close_ticket = category == "spam"
    if category == "feature_request":
        close_ticket = True

    # Small deterministic improvement: urgent if text signals immediate issue.
    priority = base["priority"]
    if any(k in text for k in ["immediate", "urgent", "today", "right away", "asap"]):
        priority = "urgent"
    elif category in {"billing", "bug_report", "cancellation", "security", "account_access"}:
        priority = base["priority"]

    return Action(
        category=category,
        priority=priority,
        route_to=base["route_to"],
        response_type=base["response_type"],
        reply_text=reply,
        close_ticket=close_ticket,
    )


def openai_action(client, obs) -> Action:
    prompt = {
        "task_id": obs.task_id,
        "ticket_index": obs.ticket_index,
        "total_tickets": obs.total_tickets,
        "subject": obs.subject,
        "body": obs.body,
        "customer_tier": obs.customer_tier,
        "customer_sentiment": obs.customer_sentiment,
        "allowed_categories": obs.allowed_categories,
        "allowed_priorities": obs.allowed_priorities,
        "allowed_routes": obs.allowed_routes,
        "allowed_response_types": obs.allowed_response_types,
        "output_schema": {
            "category": "one of allowed_categories",
            "priority": "one of allowed_priorities",
            "route_to": "one of allowed_routes",
            "response_type": "one of allowed_response_types",
            "reply_text": "optional text or null",
            "close_ticket": "boolean",
        },
    }

    response = client.responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5.4-mini"),
        instructions=(
            "You are a customer support triage agent. Return only JSON with keys category, priority, "
            "route_to, response_type, reply_text, close_ticket. Keep reply_text concise and professional. "
            "Never invent categories outside the allowed lists."
        ),
        input=json.dumps(prompt, ensure_ascii=False),
    )

    text = getattr(response, "output_text", "") or ""
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    payload = json.loads(match.group(0) if match else text)
    return Action(**payload)


def run_episode(task_id: str, mode: str) -> dict:
    env = SupportTicketEnv(task_id=task_id)
    obs = env.reset()
    actions: List[Action] = []

    client = None
    if mode == "openai":
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is required for mode=openai")
        client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    while True:
        if mode == "openai":
            assert client is not None
            action = openai_action(client, obs)
        else:
            action = heuristic_action(obs)

        actions.append(action)
        obs, reward, done, info = env.step(action)
        if done:
            break

    grade = grade_task(task_id, actions)
    return {
        "task_id": task_id,
        "mode": mode,
        "env_score": round(env.state().cumulative_score, 6),
        "grader_score": grade.score,
        "details": grade.details,
        "actions": [a.model_dump() for a in actions],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a baseline agent in the support-ticket OpenEnv.")
    parser.add_argument("--mode", choices=["heuristic", "openai"], default="heuristic")
    parser.add_argument("--task", choices=list(TASKS.keys()) + ["all"], default="all")
    parser.add_argument("--out", default="baseline_scores.json")
    args = parser.parse_args()

    task_ids = list(TASKS.keys()) if args.task == "all" else [args.task]
    results = [run_episode(task_id, args.mode) for task_id in task_ids]

    summary = {
        "results": results,
        "average_grader_score": round(sum(r["grader_score"] for r in results) / len(results), 6),
        "average_env_score": round(sum(r["env_score"] for r in results) / len(results), 6),
    }

    print(json.dumps(summary, indent=2))
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
