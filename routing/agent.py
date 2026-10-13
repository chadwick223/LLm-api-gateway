from routing.layer import TaskRouter
from models.easy_models import execute_easy_task
from models.medium_models import execute_medium_task

class CodingAgent:
    def __init__(self):
        print("Initializing Semantic Router (Loading BGE model)...")
        self.router = TaskRouter()
        
    def run(self, user_prompt: str):
        # 1. Route the intent
        print(f"Routing task...")
        difficulty = self.router.route_task(user_prompt)
        print(f"Task classified as: {difficulty}")
        
        # 2. Call the respective model pool
        if difficulty == "Easy":
            result = execute_easy_task(user_prompt)
        else:
            result = execute_medium_task(user_prompt)
            
        print("--- LLM RESPONSE ---")
        print(result)

if __name__ == "__main__":
    agent = CodingAgent()
    
    # Test Prompt
    prompt = " refactor this  code"
    print(f"\nUser: {prompt}\n")
    agent.run(prompt)
