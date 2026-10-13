import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import groq
from groq import Groq

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from configuration.key_pool import KeyPoolManager
from configuration.usage_store import UsageStoreManager


def send_single_request(client, key_idx: int, request_num: int, usage_store: UsageStoreManager):
    """
    Sends a lightweight real completion request to Groq and records it in the database.
    """
    start_time = time.time()
    model_name = "openai/gpt-oss-20b"

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1
        )
        elapsed = time.time() - start_time

        prompt_tokens = 0
        completion_tokens = 0
        if response.usage is not None:
            prompt_tokens = response.usage.prompt_tokens
            completion_tokens = response.usage.completion_tokens

        usage_store.record_call(
            provider="groq",
            key_index=key_idx,
            model_name=model_name,
            endpoint="chat.completions",
            status="ok",
            http_status=200,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens
        )

        print(f"[Flooder] Request {request_num:02d}/30 on Key {key_idx} succeeded in {elapsed:.2f}s (Tokens: {prompt_tokens}+{completion_tokens})")
        return {"status": "ok", "key_index": key_idx, "req": request_num, "latency": elapsed}

    except groq.RateLimitError as rle:
        elapsed = time.time() - start_time
        usage_store.record_call(
            provider="groq",
            key_index=key_idx,
            model_name=model_name,
            endpoint="chat.completions",
            status="error",
            http_status=429
        )
        print(f"[Flooder] Request {request_num:02d}/30 on Key {key_idx} hit 429 RateLimitError: {rle}")
        return {"status": "rate_limited", "key_index": key_idx, "req": request_num, "latency": elapsed}

    except Exception as exc:
        elapsed = time.time() - start_time
        usage_store.record_call(
            provider="groq",
            key_index=key_idx,
            model_name=model_name,
            endpoint="chat.completions",
            status="error",
            http_status=500
        )
        print(f"[Flooder] Request {request_num:02d}/30 on Key {key_idx} error: {exc}")
        return {"status": "error", "key_index": key_idx, "req": request_num, "latency": elapsed}


def flood_requests_for_key(key_idx: int = 0, total_requests: int = 30, workers: int = 6):
    """
    Sends total_requests requests concurrently using the real Groq API key at key_idx.
    """
    key_pool = KeyPoolManager()
    usage_store = UsageStoreManager()
    keys = key_pool.get_keys("groq")

    if not keys:
        print("ERROR: No GROQ_API_KEY found in environment or .env!")
        return

    if key_idx >= len(keys):
        print(f"ERROR: Key index {key_idx} requested but only {len(keys)} keys available.")
        return

    api_key = keys[key_idx]
    client = Groq(api_key=api_key, max_retries=0)

    print("=" * 60)
    print(f"STARTING RATE FLOODER: Sending {total_requests} requests for Groq Key Index {key_idx}...")
    print("=" * 60)

    start_batch = time.time()
    results = []

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = []
        for i in range(1, total_requests + 1):
            future = executor.submit(send_single_request, client, key_idx, i, usage_store)
            futures.append(future)

        for future in as_completed(futures):
            res = future.result()
            results.append(res)

    total_time = time.time() - start_batch
    print("=" * 60)
    print(f"FLOOD COMPLETE: Sent {total_requests} requests on Key {key_idx} in {total_time:.2f}s")

    # Verify count in database in the last 60 seconds
    now_ms = int(time.time() * 1000)
    one_min_ago_ms = now_ms - (60 * 1000)
    recent_calls = usage_store.count_calls_since("groq", key_idx, one_min_ago_ms)
    print(f"Verified DB Usage: Groq Key {key_idx} has {recent_calls} recorded calls in the last 60 seconds (Limit is 30 RPM).")
    print("=" * 60 + "\n")
    return recent_calls


if __name__ == "__main__":
    target_key = 0
    if len(sys.argv) > 1:
        target_key = int(sys.argv[1])
    flood_requests_for_key(key_idx=target_key, total_requests=30, workers=6)
