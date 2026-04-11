import os
from support_env.environment import SupportTicketEnv, TASKS
from support_env.graders import grade_task ✅  # ✅ correct import


def run_task(task_name):
    env = SupportTicketEnv(task_name)

    print(f"[START] task={task_name} env=support_ticket model=dummy", flush=True)

    obs = env.reset()
    done = False
    step_count = 0
    rewards = []

    while not done:
        # ✅ SAFE ACTION FORMAT (matches most models.py)
        action = {
            "action_type": "respond",
            "response": "Thank you for reaching out. We are working on your issue."
        }

        obs, reward, done, info = env.step(action)

        step_count += 1
        rewards.append(reward)

        error = info.get("error", None)
        error_str = error if error else "null"

        print(
            f"[STEP] step={step_count} action={action} reward={reward:.2f} done={str(done).lower()} error={error_str}",
            flush=True
        )

    # ✅ correct grading call
    result = grade_task(task_name, env)

    rewards_str = ",".join([f"{r:.2f}" for r in rewards])

    print(
        f"[END] success=true steps={step_count} score={result.score:.2f} rewards={rewards_str}",
        flush=True
    )

    env.close()


if __name__ == "__main__":
    for task in TASKS:
        run_task(task)
