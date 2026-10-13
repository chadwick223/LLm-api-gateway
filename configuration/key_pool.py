import os
import time
from typing import List, Optional, Tuple

class KeyPoolManager:
    def __init__(self):
        # Maps "provider:index" -> timestamp (when the cooldown expires)
        self.cooldowns = {}
        # Maps "provider" -> index (the next key index to start searching from for round-robin)
        self.rotation = {}

    def get_keys(self, provider: str) -> List[str]:
        """
        Reads the environment variable for the provider, splits by comma, 
        and returns a list of keys.
        """
        env_var_map = {
            "groq": "GROQ_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "cloudflare": "CLOUDFLARE_API_KEY",
            "nvidia": "NVIDIA_API_KEY",
            "ollama": "OLLAMA_API_KEY",
        }
        
        env_var = env_var_map.get(provider.lower())
        if not env_var:
            return []
            
        raw_keys = os.getenv(env_var, "")
        
        # Split the string by commas
        split_keys = raw_keys.split(",")
        
        # Create a clean list of keys
        clean_keys = []
        for key in split_keys:
            stripped_key = key.strip()
            # Only add to list if the key is not an empty string
            if stripped_key != "":
                clean_keys.append(stripped_key)
                
        return clean_keys

    def key_count(self, provider: str) -> int:
        keys = self.get_keys(provider)
        return len(keys)

    def is_cooling(self, provider: str, index: int) -> bool:
        """
        Checks if the specific key index for a provider is currently in a cooldown period.
        """
        cooldown_key = f"{provider}:{index}"
        
        # If the key does not exist in the dictionary, it defaults to 0 (no cooldown)
        until = self.cooldowns.get(cooldown_key, 0)
        
        current_time = time.time()
        
        # If the cooldown expiration time is greater than the current time, 
        # it means the key is still cooling down
        if until > current_time:
            return True
        else:
            return False

    def available_indexes(self, provider: str) -> List[int]:
        """
        Returns a list of key indexes that are NOT cooling down, 
        ordered by the current round-robin rotation pointer.
        """
        total = self.key_count(provider)
        if total == 0:
            return []
            
        start = self.rotation.get(provider, 0)
        indexes = []
        
        for i in range(total):
            # Round-robin: calculate index wrapped around total
            idx = (start + i) % total
            
            # Check if this specific index is cooling down
            if not self.is_cooling(provider, idx):
                indexes.append(idx)
                
        return indexes

    def pick(self, provider: str) -> Optional[Tuple[str, int]]:
        """
        Picks the next available key for the provider using round-robin.
        Updates the rotation pointer for the next call.
        Returns a tuple of (api_key_string, index) or None if all keys are cooling.
        """
        keys = self.get_keys(provider)
        available = self.available_indexes(provider)
        
        if not available:
            # All keys are cooling or no keys exist
            return None 
            
        # Pick the first available index (which respects the rotation pointer)
        chosen_idx = available[0]
        
        # Update the rotation pointer to the next index for the NEXT request
        self.rotation[provider] = (chosen_idx + 1) % len(keys)
        
        return keys[chosen_idx], chosen_idx

    def report_rate_limited(self, provider: str, index: int, seconds: int = 60):
        """
        Marks a specific key as cooling down for a certain number of seconds.
        By default, we assume a 60 second cooldown.
        """
        cooldown_key = f"{provider}:{index}"
        current_time = time.time()
        
        # The key will be available again at this future timestamp
        available_again_time = current_time + max(5, seconds)
        
        self.cooldowns[cooldown_key] = available_again_time
