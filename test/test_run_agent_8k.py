import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from routing.agent import CodingAgent

class TeeLogger:
    def __init__(self, log_path: str):
        self.terminal = sys.stdout
        self.log_file = open(log_path, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        self.log_file.write(message)
        self.log_file.flush()

    def flush(self):
        self.terminal.flush()
        self.log_file.flush()

    def close(self):
        self.log_file.close()

def main():
    log_file_path = os.path.join(project_root, "test", "test_8k_output.log")
    tee = TeeLogger(log_file_path)
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = tee
    sys.stderr = tee

    try:
        print("=" * 70)
        print("TEST 1: VERIFYING > 8K TOKEN SKIP LOGIC IN DECISION LAYER VIA AGENT.PY")
        print("=" * 70)

        prompt_file = os.path.join(project_root, "test", "temp_8k_prompt.txt")
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read()

        print(f"Loaded prompt from: {prompt_file}")
        print(f"Prompt character length: {len(prompt)}")

        # Initialize agent
        agent = CodingAgent()

        # Run prompt through agent
        print("\nSending prompt to agent.run()...\n")
        agent.run(prompt)

        print("\n" + "=" * 70)
        print("TEST 1 COMPLETE - LOG SAVED TO:", log_file_path)
        print("=" * 70)

    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        tee.close()

if __name__ == "__main__":
    main()
