from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from support_env.environment import SupportTicketEnv, TASKS, grade_task
from support_env.models import Action
from baseline.run_agent import heuristic_action

app = FastAPI(title="OpenEnv Support Ticket Environment")

env = SupportTicketEnv(task_name=list(TASKS.keys())[0])


@app.post("/reset")
def reset():
    obs = env.reset()
    return {"observation": obs}


@app.post("/step")
def step(action: dict):
    action_obj = Action(**action)
    obs, reward, done, info = env.step(action_obj)

    return {
        "observation": obs,
        "reward": reward.score,
        "done": done,
        "info": info
    }


@app.get("/state")
def state():
    return env.state()


@app.get("/", response_class=HTMLResponse)
def home() -> str:
    tasks_html = "".join(
        f"<li><b>{task_id}</b> — {task.difficulty}: {task.description}</li>"
        for task_id, task in TASKS.items()
    )
    return f"""
    <html>
      <body>
        <h1>OpenEnv Support Ticket Environment</h1>
        <ul>{tasks_html}</ul>
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

    env = SupportTicketEnv(task_name=task_id)
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


def main():
    return app
