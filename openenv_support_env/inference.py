from environment import SupportTicketEnv
from models import Action

def run_inference():
    env = SupportTicketEnv()
    obs = env.reset()
    
    done = False
    total_reward = 0
    
    while not done:
        action = Action(
            category="billing",
            priority="high",
            route_to="billing",
            response_type="provide_solution",
            reply_text="We will resolve your issue shortly.",
            close_ticket=False
        )
        
        obs, reward, done, _ = env.step(action)
        total_reward += reward.score

    print("Total Reward:", total_reward)

if __name__ == "__main__":
    run_inference()
