import os
import groq
from groq import Groq
from openai import OpenAI
from configuration.key_pool import KeyPoolManager
from configuration.usage_store import UsageStoreManager
from configuration.rate_limiter import RateLimiterManager
from configuration.token_estimation import estimate_token
from configuration.limits import get_max_output_tokens

# Candidate models for the Medium pool (in decision priority order)
MEDIUM_CANDIDATES = [
    {
        "provider": "cloudflare",
        "model": "@cf/openai/gpt-oss-120b"
    },
    {
        "provider": "cloudflare",
        "model": "@cf/qwen/qwen2.5-coder-32b-instruct"
    },
    {
        "provider": "cloudflare",
        "model": "@cf/qwen/qwen3-30b-a3b-fp8"
    },
    {
        "provider": "gemini",
        "model": "gemini-3.6-flash"
    },
    {
        "provider": "nvidia",
        "model": "nvidia/nemotron-3-super-120b-a12b"
    },
    {
        "provider": "nvidia",
        "model": "nvidia/nemotron-3-ultra-550b-a55b"
    },
    {
        "provider": "ollama",
        "model": "gpt-oss:120b"
    },
    {
        "provider": "groq",
        "model": "openai/gpt-oss-120b"
    }
]

DEFAULT_TEMPERATURE = 0.2

# Instantiate managers
key_pool = KeyPoolManager()
usage_store = UsageStoreManager()
rate_limiter = RateLimiterManager(key_pool, usage_store)


def create_client_for_provider(provider: str, api_key: str):
    """
    Creates the appropriate client instance for the given provider.
    Written with explicit if-else blocks.
    """
    if provider == "groq":
        client_instance = Groq(api_key=api_key, max_retries=0)
        return client_instance
    elif provider == "cloudflare":
        account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "")
        base_url = "https://api.cloudflare.com/client/v4/accounts/" + account_id + "/ai/v1"
        client_instance = OpenAI(api_key=api_key, base_url=base_url)
        return client_instance
    elif provider == "gemini":
        base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
        client_instance = OpenAI(api_key=api_key, base_url=base_url)
        return client_instance
    elif provider == "nvidia":
        base_url = "https://integrate.api.nvidia.com/v1"
        client_instance = OpenAI(api_key=api_key, base_url=base_url)
        return client_instance
    elif provider == "ollama":
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
        client_instance = OpenAI(api_key=api_key, base_url=base_url)
        return client_instance
    else:
        client_instance = OpenAI(api_key=api_key)
        return client_instance


def execute_medium_task(user_prompt: str) -> str:
    """
    Decision-making engine for Medium tasks:
    1. Estimates user prompt token count.
    2. Iterates through candidate models (Cloudflare, Gemini, NVIDIA, Ollama, Groq).
    3. Checks: if estimated_tokens > max_output_tokens, skips model.
    4. Checks: if no valid key is available from RateLimiter, skips model.
    5. Executes via the first suitable model & available key.
    """
    # 0. Validate message and estimate token usage
    try:
        estimated_tokens = estimate_token(user_prompt)
    except ValueError as error:
        return "Error: " + str(error)

    print(f"[Medium Decision Engine] Prompt Estimated Tokens: {estimated_tokens}\n")

    # 1. Iterate through candidate models in priority order
    for candidate in MEDIUM_CANDIDATES:
        provider = candidate["provider"]
        model_name = candidate["model"]

        max_output_tokens = get_max_output_tokens(provider, model_name)

        # Condition Check: Skip if input tokens exceed max output token capacity
        if estimated_tokens > max_output_tokens:
            print(f"Skipping {provider} ({model_name}): input tokens ({estimated_tokens}) > max output tokens ({max_output_tokens})")
            continue
        else:
            # Check if rate limiter has an available key for this provider and model
            pick_result = rate_limiter.get_valid_key(provider, model_name=model_name)
            if pick_result is None:
                print(f"Skipping {provider} ({model_name}): No valid key available or cooling down.")
                continue
            else:
                api_key = pick_result[0]
                key_index = pick_result[1]

                print(f"Selected Medium Candidate: {provider} -> {model_name} (Key Index: {key_index})")
                print(f"Output Capacity: {max_output_tokens}\n")

                client = create_client_for_provider(provider, api_key)

                try:
                    response = client.chat.completions.create(
                        model=model_name,
                        messages=[{"role": "user", "content": user_prompt}],
                        temperature=DEFAULT_TEMPERATURE,
                        max_tokens=max_output_tokens
                    )

                    prompt_tokens = 0
                    completion_tokens = 0
                    if response.usage is not None:
                        prompt_tokens = response.usage.prompt_tokens
                        completion_tokens = response.usage.completion_tokens

                    usage_store.record_call(
                        provider=provider,
                        key_index=key_index,
                        model_name=model_name,
                        endpoint="chat.completions",
                        status="ok",
                        http_status=200,
                        prompt_tokens=prompt_tokens,
                        completion_tokens=completion_tokens
                    )

                    return response.choices[0].message.content

                except groq.RateLimitError:
                    print(f"WARNING: Rate limit hit on Groq Key index {key_index}. Putting it in cooldown.")
                    key_pool.report_rate_limited(provider="groq", index=key_index, seconds=60)
                    usage_store.record_call(
                        provider="groq",
                        key_index=key_index,
                        model_name=model_name,
                        endpoint="chat.completions",
                        status="error",
                        http_status=429
                    )
                    print("Retrying with next available key or model candidate...\n")
                    return execute_medium_task(user_prompt)

                except Exception as exc:
                    error_message = str(exc)
                    lower_error = error_message.lower()

                    if "rate" in lower_error or "429" in lower_error:
                        print(f"WARNING: Rate limit hit on {provider} Key index {key_index}. Putting it in cooldown.")
                        key_pool.report_rate_limited(provider=provider, index=key_index, seconds=60)
                        usage_store.record_call(
                            provider=provider,
                            key_index=key_index,
                            model_name=model_name,
                            endpoint="chat.completions",
                            status="error",
                            http_status=429
                        )
                        print("Retrying with next available key or model candidate...\n")
                        return execute_medium_task(user_prompt)
                    else:
                        usage_store.record_call(
                            provider=provider,
                            key_index=key_index,
                            model_name=model_name,
                            endpoint="chat.completions",
                            status="error",
                            http_status=500
                        )
                        return "Error: " + error_message

    return "Error: All candidate models and API keys are currently exhausted, cooling down, or token limits exceeded."
