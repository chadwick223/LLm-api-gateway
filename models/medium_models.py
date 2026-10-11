from configuration.groq_configuration import CODING_MODELS as groq_models, DEFAULT_TEMPERATURE, DEFAULT_MAX_TOKENS
import groq
from groq import Groq
from configuration.key_pool import KeyPoolManager
from configuration.usage_store import UsageStoreManager
from configuration.rate_limiter import RateLimiterManager

# Instantiate our managers
key_pool = KeyPoolManager()
usage_store = UsageStoreManager()
rate_limiter = RateLimiterManager(key_pool, usage_store)

def execute_medium_task(user_prompt: str) -> str:
    """
    Pulls a heavier model from the Medium Pool and executes the prompt.
    Currently hardcoded to use Groq's gpt_120b for testing.
    """
    model_name = groq_models["gpt_120b"]
    print(f"Generating response using Groq model: {model_name}...\n")
    
    # 1. Ask the RateLimiter for a valid key
    pick_result = rate_limiter.get_valid_key("groq")
    if not pick_result:
        return "Error: All Groq API keys are currently exhausted or cooling down."
        
    api_key, key_index = pick_result
    
    # 2. Create the client dynamically for this request
    client = Groq(api_key=api_key)
    
    try:
        # 3. Execute via the dynamically created Groq client
        response = client.chat.completions.create(
            model=model_name,
            messages=[{"role": "user", "content": user_prompt}],
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=DEFAULT_MAX_TOKENS
        )
        
        # Calculate tokens used
        prompt_tokens = response.usage.prompt_tokens if response.usage else 0
        completion_tokens = response.usage.completion_tokens if response.usage else 0
        
        # 4. Record Success
        usage_store.record_call(
            provider="groq",
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
        # 5. Handle Rate Limit Errors
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
        
        print("Retrying with a different key...\n")
        return execute_medium_task(user_prompt)
        
    except Exception as e:
        usage_store.record_call(
            provider="groq",
            key_index=key_index,
            model_name=model_name,
            endpoint="chat.completions",
            status="error",
            http_status=500
        )
        return f"Error: {str(e)}"
