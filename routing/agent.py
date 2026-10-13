import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
    
    if len(sys.argv) > 1:
        arg_val = sys.argv[1]
        if os.path.exists(arg_val):
            with open(arg_val, "r", encoding="utf-8") as file_handle:
                prompt = file_handle.read()
        else:
            prompt = arg_val
    else:
        # Default Test Prompt
        prompt = " refactor this  code"
        
    preview = prompt[:120] + "..." if len(prompt) > 120 else prompt
    print(f"\nUser: {preview}\n")
    agent.run(prompt)
