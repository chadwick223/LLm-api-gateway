import time
from typing import Tuple, Optional
from .key_pool import KeyPoolManager
from .usage_store import UsageStoreManager
from .limits import get_provider_limits


class RateLimiterManager:
    def __init__(self, key_pool: KeyPoolManager, usage_store: UsageStoreManager):
        self.key_pool = key_pool
        self.usage_store = usage_store

    def get_valid_key(self, provider: str, model_name: str = None) -> Optional[Tuple[str, int]]:
        """
        Loops through available keys and returns the first one that has not exceeded its limits.
        Works across all providers (groq, gemini, cloudflare, nvidia, ollama) and optionally
        respects model-specific rate limits if model_name is provided.
        """
        limits = get_provider_limits(provider, model_name)
        if not limits:
            print(f"No limits configured for provider: {provider}")
            return None

        # Get all keys that aren't on a hard cooldown, in round-robin order
        available_indexes = self.key_pool.available_indexes(provider)
        all_keys = self.key_pool.get_keys(provider)

        current_time_ms = int(time.time() * 1000)
        one_minute_ago = current_time_ms - (60 * 1000)
        one_day_ago = current_time_ms - (24 * 60 * 60 * 1000)

        for idx in available_indexes:
            # 1. Check Requests Per Minute (RPM)
            rpm = self.usage_store.count_calls_since(provider, idx, one_minute_ago)
            if rpm >= limits["rpm"]:
                print(f"[{provider}] Key {idx} exceeded RPM limit ({rpm}/{limits['rpm']}). Skipping.")
                continue

            # 2. Check Requests Per Day (RPD)
            rpd = self.usage_store.count_calls_since(provider, idx, one_day_ago)
            if rpd >= limits["rpd"]:
                print(f"[{provider}] Key {idx} exceeded RPD limit ({rpd}/{limits['rpd']}). Skipping.")
                continue

            # 3. Check Tokens Per Day (TPD)
            tpd = self.usage_store.count_tokens_since(provider, idx, one_day_ago)
            if tpd >= limits["tpd"]:
                print(f"[{provider}] Key {idx} exceeded TPD limit ({tpd}/{limits['tpd']}). Skipping.")
                continue

            # If we get here, the key passed all checks!
            # Update the rotation pointer in KeyPool so the next request starts at the next key
            self.key_pool.rotation[provider] = (idx + 1) % len(all_keys)

            return all_keys[idx], idx

        # If the loop finishes and we found no keys that passed the limits
        return None

    def check_limit_status(self, provider: str, key_index: int, model_name: str = None) -> dict:
        """
        Inspects and returns the live usage vs limit for a specific provider, key, and optional model.
        Useful for diagnostics and verifying if RPM, RPD, or TPD caps are reached.
        """
        limits = get_provider_limits(provider, model_name)
        if not limits:
            return {"error": f"No limits configured for {provider}"}

        current_time_ms = int(time.time() * 1000)
        one_minute_ago = current_time_ms - (60 * 1000)
        one_day_ago = current_time_ms - (24 * 60 * 60 * 1000)

        rpm_used = self.usage_store.count_calls_since(provider, key_index, one_minute_ago)
        rpd_used = self.usage_store.count_calls_since(provider, key_index, one_day_ago)
        tpd_used = self.usage_store.count_tokens_since(provider, key_index, one_day_ago)

        return {
            "provider": provider,
            "key_index": key_index,
            "model_name": model_name,
            "rpm": {
                "used": rpm_used,
                "limit": limits["rpm"],
                "exceeded": rpm_used >= limits["rpm"]
            },
            "rpd": {
                "used": rpd_used,
                "limit": limits["rpd"],
                "exceeded": rpd_used >= limits["rpd"]
            },
            "tpd": {
                "used": tpd_used,
                "limit": limits["tpd"],
                "exceeded": tpd_used >= limits["tpd"]
            }
        }
