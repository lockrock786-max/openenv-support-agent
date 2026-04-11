from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse

from support_env.environment import SupportTicketEnv, TASKS
from support_env.models import Action

app = FastAPI(title="OpenEnv Support Ticket Environment")

env = None


# ✅ REQUIRED: RESET
@app.post("/reset")
def reset():
    global env
    env = SupportTicketEnv()
    obs = env.reset()
    return {"observation": obs}


# ✅ REQUIRED: STEP
@app.post("/step")
def step(action: dict):
    global env

    if env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")

    action_obj = Action(**action)
    obs, reward, done, info = env.step(action_obj)

    return {
        "observation": obs,
        "reward": reward.score if hasattr(reward, "score") else reward,
        "done": done,
        "info": info
    }


# OPTIONAL (SAFE)
@app.get("/state")
def state():
    if env is None:
        return {"state": None}
    return env.state()


# OPTIONAL UI
@app.get("/", response_class=HTMLResponse)
def home():
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


def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
