import sys
import os
import time
import argparse

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
        print("Semantic Router (BGE model) loaded successfully.")
        
    def run(self, user_prompt: str, return_details: bool = False):
        start_time = time.time()
        print(f"Routing task...")
        difficulty = self.router.route_task(user_prompt)
        print(f"Task classified as: {difficulty}")
        
        # 2. Call the respective model pool
        if difficulty == "Easy":
            result = execute_easy_task(user_prompt, return_details=return_details)
        else:
            result = execute_medium_task(user_prompt, return_details=return_details)
            
        duration_ms = int((time.time() - start_time) * 1000)

        if return_details:
            if isinstance(result, dict):
                result["difficulty"] = difficulty
                result["duration_ms"] = duration_ms
                return result
            return {
                "difficulty": difficulty,
                "text": str(result),
                "duration_ms": duration_ms
            }

        print("--- LLM RESPONSE ---")
        print(result)
        return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Coding Agent with Persistent BGE Router")
    parser.add_argument("--server", action="store_true", help="Start the FastAPI web server & dashboard")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on (default: 8080)")
    parser.add_argument("--prompt", type=str, default=None, help="Single prompt or file path to execute once")
    args, unknown = parser.parse_known_args()

    if args.server:
        import uvicorn
        print(f"Starting Gateway Server & Dashboard on http://127.0.0.1:{args.port} ...")
        uvicorn.run("server:app", host="127.0.0.1", port=args.port, reload=False)
    elif args.prompt:
        target = args.prompt
        if os.path.exists(target):
            with open(target, "r", encoding="utf-8") as f:
                prompt_content = f.read()
        else:
            prompt_content = target
        agent = CodingAgent()
        preview = prompt_content[:120] + "..." if len(prompt_content) > 120 else prompt_content
        print(f"\nUser: {preview}\n")
        agent.run(prompt_content)
    elif len(unknown) > 0 and unknown[0] and not unknown[0].startswith("-"):
        target = unknown[0]
        if os.path.exists(target):
            with open(target, "r", encoding="utf-8") as f:
                prompt_content = f.read()
        else:
            prompt_content = target
        agent = CodingAgent()
        preview = prompt_content[:120] + "..." if len(prompt_content) > 120 else prompt_content
        print(f"\nUser: {preview}\n")
        agent.run(prompt_content)
    else:
        # Interactive REPL Session: BGE model stays loaded in memory across all prompts!
        agent = CodingAgent()
        print("\n" + "=" * 60)
        print("🚀 Coding Agent Interactive Session Ready")
        print("BGE Semantic Router is loaded into memory.")
        print("Enter your prompt below. (Type 'exit', 'quit', or 'q' to stop)")
        print("=" * 60 + "\n")

        while True:
            try:
                user_input = input("\n[Enter Prompt] > ").strip()
                if not user_input:
                    continue
                if user_input.lower() in ("exit", "quit", "q"):
                    print("Exiting interactive session.")
                    break
                agent.run(user_input)
            except (KeyboardInterrupt, EOFError):
                print("\nSession ended.")
                break

