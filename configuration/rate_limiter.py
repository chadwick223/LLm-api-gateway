import time
from typing import Tuple, Optional
from .key_pool import KeyPoolManager
from .usage_store import UsageStoreManager
from .limits import PROVIDER_LIMITS

class RateLimiterManager:
    def __init__(self, key_pool: KeyPoolManager, usage_store: UsageStoreManager):
        self.key_pool = key_pool
        self.usage_store = usage_store
        
    def get_valid_key(self, provider: str) -> Optional[Tuple[str, int]]:
        """
        Loops through available keys and returns the first one that has not exceeded its limits.
        """
        limits = PROVIDER_LIMITS.get(provider.lower())
        if not limits:
            print(f"No limits configured for {provider}")
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
                print(f"Key {idx} exceeded RPM limit ({rpm}/{limits['rpm']}). Skipping.")
                continue
                
            # 2. Check Requests Per Day (RPD)
            rpd = self.usage_store.count_calls_since(provider, idx, one_day_ago)
            if rpd >= limits["rpd"]:
                print(f"Key {idx} exceeded RPD limit ({rpd}/{limits['rpd']}). Skipping.")
                continue
                
            # 3. Check Tokens Per Day (TPD)
            tpd = self.usage_store.count_tokens_since(provider, idx, one_day_ago)
            if tpd >= limits["tpd"]:
                print(f"Key {idx} exceeded TPD limit ({tpd}/{limits['tpd']}). Skipping.")
                continue
                
            # If we get here, the key passed all checks!
            # Update the rotation pointer in KeyPool so the next request starts at the next key
            self.key_pool.rotation[provider] = (idx + 1) % len(all_keys)
            
            return all_keys[idx], idx
            
        # If the loop finishes and we found no keys that passed the limits
        return None
