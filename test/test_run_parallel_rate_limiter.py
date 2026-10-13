import os
import sys
import time
import threading

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

test_dir = os.path.join(project_root, "test")
if test_dir not in sys.path:
    sys.path.insert(0, test_dir)

from temp_send_30_requests import flood_requests_for_key
from routing.agent import CodingAgent


class ParallelLogger:
    def __init__(self, log_path: str):
        self.terminal = sys.stdout
        self.log_file = open(log_path, "w", encoding="utf-8")
        self.lock = threading.Lock()

    def write(self, message):
        with self.lock:
            try:
                self.terminal.write(message)
            except (UnicodeEncodeError, Exception):
                safe_msg = message.encode("ascii", errors="replace").decode("ascii")
                self.terminal.write(safe_msg)
            self.terminal.flush()
            try:
                self.log_file.write(message)
            except Exception:
                safe_msg = message.encode("utf-8", errors="replace").decode("utf-8")
                self.log_file.write(safe_msg)
            self.log_file.flush()

    def flush(self):
        with self.lock:
            self.terminal.flush()
            self.log_file.flush()

    def close(self):
        self.log_file.close()


def run_agent_worker(prompt: str, logger: ParallelLogger):
    """
    Runs CodingAgent in a parallel thread.
    """
    print("\n[Thread-Agent] Starting CodingAgent initialization...")
    agent = CodingAgent()
    print(f"\n[Thread-Agent] Calling agent.run() with prompt: {prompt[:80]}...\n")
    agent.run(prompt)
    print("\n[Thread-Agent] CodingAgent execution finished.\n")


def run_flooder_worker(key_index: int, total_requests: int):
    """
    Runs flood_requests_for_key in a parallel thread.
    """
    print(f"\n[Thread-Flooder] Starting flood of {total_requests} requests on Groq Key {key_index}...")
    flood_requests_for_key(key_idx=key_index, total_requests=total_requests, workers=6)
    print(f"\n[Thread-Flooder] Flood of {total_requests} requests finished.\n")


def main():
    log_file_path = os.path.join(project_root, "test", "test_rate_limiter_output.log")
    logger = ParallelLogger(log_file_path)

    original_stdout = sys.stdout
    original_stderr = sys.stderr
    sys.stdout = logger
    sys.stderr = logger

    try:
        print("=" * 75)
        print("TEST 2: RATE LIMITER VERIFICATION (PARALLEL EXECUTION)")
        print("=" * 75)
        print("Plan:")
        print("1. Thread A starts CodingAgent() (loading BGE model takes ~8-12 seconds).")
        print("2. Thread B in parallel fires 30 requests to Groq Key 0 (filling 30 RPM limit).")
        print("3. By the time CodingAgent reaches rate_limiter.get_valid_key(), Key 0 is at >= 30 RPM.")
        print("4. Rate limiter intercepts Key 0: '[groq] Key 0 exceeded RPM limit. Skipping.'")
        print("5. Key rotation activates -> Groq Key 1 is selected to serve the prompt!")
        print("=" * 75 + "\n")

        # Prompt for agent: Short prompt (< 8k tokens) that routes to Easy
        easy_short_prompt = "can you fix the formatting of this python file:\n\ndef add(a, b):\nreturn a+b\n"

        # Start flooder thread for Key 0 (30 requests)
        flooder_thread = threading.Thread(
            target=run_flooder_worker,
            args=(0, 30),
            name="FlooderThread"
        )

        # Start agent thread
        agent_thread = threading.Thread(
            target=run_agent_worker,
            args=(easy_short_prompt, logger),
            name="AgentThread"
        )

        print("[Main] Launching both threads in parallel now...")
        start_time = time.time()

        flooder_thread.start()
        agent_thread.start()

        # Wait for both threads to finish
        flooder_thread.join()
        agent_thread.join()

        elapsed_total = time.time() - start_time
        print("\n" + "=" * 75)
        print(f"TEST 2 COMPLETE in {elapsed_total:.2f} seconds!")
        print(f"Log saved to: {log_file_path}")
        print("=" * 75)

    finally:
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        logger.close()


if __name__ == "__main__":
    main()
