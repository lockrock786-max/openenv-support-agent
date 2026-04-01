from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from support_env import SupportTicketEnv, TASKS, grade_task
from baseline.run_agent import heuristic_action

app = FastAPI(title="OpenEnv Support Ticket Environment")


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    tasks_html = "".join(
        f"<li><b>{task_id}</b> — {task.difficulty}: {task.description}</li>"
        for task_id, task in TASKS.items()
    )
    return f"""
    <html>
      <head><title>OpenEnv Support Ticket Environment</title></head>
      <body style="font-family: Arial, sans-serif; max-width: 900px; margin: 40px auto; line-height: 1.5;">
        <h1>OpenEnv Support Ticket Environment</h1>
        <p>A deterministic customer-support workflow environment for RL agents.</p>
        <h2>Tasks</h2>
        <ul>{tasks_html}</ul>
        <p>Use <code>/api/tasks</code> for JSON metadata and <code>/api/demo/&lt;task_id&gt;</code> for a live baseline rollout.</p>
      </body>
    </html>
    """


@app.get("/api/tasks")
def tasks() -> dict:
    return {task_id: task.model_dump() for task_id, task in TASKS.items()}


@app.get("/api/demo/{task_id}")
def demo(task_id: str) -> dict:
    if task_id not in TASKS:
        raise HTTPException(status_code=404, detail="Unknown task_id")

    env = SupportTicketEnv(task_id=task_id)
    obs = env.reset()
    actions = []
    while True:
        action = heuristic_action(obs)
        actions.append(action)
        obs, reward, done, info = env.step(action)
        if done:
            break

    grader = grade_task(task_id, actions)
    return {
        "task_id": task_id,
        "env_score": env.state().cumulative_score,
        "grader_score": grader.score,
        "details": grader.details,
        "actions": [a.model_dump() for a in actions],
    }

