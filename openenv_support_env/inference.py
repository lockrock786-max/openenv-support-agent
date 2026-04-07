import sys
import os

sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), "openenv_support_env"))

from support_env.environment import SupportTicketEnv, TASKS, grade_task

MODEL_NAME = "baseline"
BENCHMARK = "openenv_support"

def run_task(task_id):
    env = SupportTicketEnv(task_id=task_id)
    obs = env.reset()

    rewards = []
    steps = 0

    print(f"[START] task={task_id} env={BENCHMARK} model={MODEL_NAME}", flush=True)

    done = False

    try:
        while not done:
            action = {
                "type": "classify",
                "priority": "medium"
            }

            obs, reward, done, info = env.step(action)

            steps += 1
            reward = float(reward or 0.0)
            rewards.append(reward)

            print(
                f"[STEP] step={steps} action={action} reward={reward:.2f} done={str(done).lower()} error=null",
                flush=True
            )

    except Exception as e:
        print(
            f"[STEP] step={steps} action=error reward=0.00 done=true error={str(e)}",
            flush=True
        )
        done = True

    score = float(grade_task(task_id, env.state()))
    success = score >= 0.5

    rewards_str = ",".join(f"{r:.2f}" for r in rewards)

    print(
        f"[END] success={str(success).lower()} steps={steps} score={score:.2f} rewards={rewards_str}",
        flush=True
    )


if __name__ == "__main__":
    for task in TASKS:
        run_task(task)
