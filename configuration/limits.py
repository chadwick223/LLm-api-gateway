# Provider rate limits and model-specific quotas
# Structure: each provider defines default rpm, rpd, tpd and optional per-model overrides.
PROVIDER_LIMITS = {
    "groq": {
        "rpm": 30,
        "rpd": 1000,
        "tpd": 200000,
        "models": {
            "openai/gpt-oss-20b": {"rpm": 30, "rpd": 1000, "tpm": 8000, "tpd": 200000},
            "openai/gpt-oss-120b": {"rpm": 30, "rpd": 1000, "tpm": 8000, "tpd": 200000},
            "qwen-3.8-27b": {"rpm": 30, "rpd": 1000, "tpm": 8000, "tpd": 200000},
        }
    },
    "gemini": {
        "rpm": 15,
        "rpd": 1500,
        "tpd": 1000000,
        "models": {
            "gemini-3.1-flash-lite": {"rpm": 15, "rpd": 1500, "tpd": 1000000},
            "gemini-3.6-flash": {"rpm": 15, "rpd": 1500, "tpd": 1000000},
        }
    },
    "cloudflare": {
        "rpm": 300,
        "rpd": 10000,
        "tpd": 1000000,
        "models": {
            "@cf/qwen/qwen2.5-coder-32b-instruct": {"rpm": 300, "rpd": 10000, "tpd": 1000000},
            "@cf/openai/gpt-oss-120b": {"rpm": 50, "rpd": 5000, "tpd": 500000},
            "@cf/qwen/qwen3-30b-a3b-fp8": {"rpm": 300, "rpd": 10000, "tpd": 1000000},
            "@cf/zai-org/glm-4.7-flash": {"rpm": 300, "rpd": 10000, "tpd": 1000000},
        }
    },
    "nvidia": {
        "rpm": 40,
        "rpd": 1000,
        "tpd": 500000,
        "models": {
            "nvidia/nemotron-3-super-120b-a12b": {"rpm": 40, "rpd": 1000, "tpd": 500000},
            "nvidia/nemotron-3-ultra-550b-a55b": {"rpm": 40, "rpd": 1000, "tpd": 500000},
            "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning": {"rpm": 40, "rpd": 1000, "tpd": 500000},
        }
    },
    "ollama": {
        "rpm": 60,
        "rpd": 10000,
        "tpd": 1000000,
        "models": {
            "gemma4:31b": {"rpm": 60, "rpd": 10000, "tpd": 1000000},
            "gpt-oss:120b": {"rpm": 60, "rpd": 10000, "tpd": 1000000},
            "gpt-oss:20b": {"rpm": 60, "rpd": 10000, "tpd": 1000000},
        }
    }
}

# Model specifications structured by provider:
# Includes context_window and max_output_tokens per model per provider
MODEL_SPECS = {
    "groq": {
        "openai/gpt-oss-20b": {
            "context_window": 131072,
            "max_output_tokens": 8000,
        },
        "openai/gpt-oss-120b": {
            "context_window": 131072,
            "max_output_tokens": 8000,
        },
        "qwen-3.8-27b": {
            "context_window": 131072,
            "max_output_tokens": 8000,
        },
    },
    "cloudflare": {
        "@cf/qwen/qwen2.5-coder-32b-instruct": {
            "context_window": 32768,
            "max_output_tokens": 32768,
        },
        "@cf/openai/gpt-oss-120b": {
            "context_window": 128000,
            "max_output_tokens": 65536,
        },
        "@cf/qwen/qwen3-30b-a3b-fp8": {
            "context_window": 32768,
            "max_output_tokens": 8192,
        },
        "@cf/zai-org/glm-4.7-flash": {
            "context_window": 131072,
            "max_output_tokens": 8192,
        },
    },
    "gemini": {
        "gemini-3.1-flash-lite": {
            "context_window": 1048576,
            "max_output_tokens": 65536,
        },
        "gemini-3.6-flash": {
            "context_window": 1048576,
            "max_output_tokens": 65536,
        },
    },
    "nvidia": {
        "nvidia/nemotron-3-super-120b-a12b": {
            "context_window": 1048576,
            "max_output_tokens": 65536,
        },
        "nvidia/nemotron-3-ultra-550b-a55b": {
            "context_window": 1048576,
            "max_output_tokens": 65536,
        },
        "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning": {
            "context_window": 262144,
            "max_output_tokens": 4096,
        },
    },
    "ollama": {
        "gemma4:31b": {
            "context_window": 131072,
            "max_output_tokens": 32768,
        },
        "gpt-oss:120b": {
            "context_window": 131072,
            "max_output_tokens": 32768,
        },
        "gpt-oss:20b": {
            "context_window": 131072,
            "max_output_tokens": 32768,
        },
    },
}

# Flat dictionary maintained for backwards compatibility with any direct dict lookups
MODEL_CONTEXT_LIMITS = {}
for _prov, _models in MODEL_SPECS.items():
    for _m_name, _specs in _models.items():
        MODEL_CONTEXT_LIMITS[_m_name] = _specs["context_window"]


def get_provider_limits(provider: str, model_name: str = None) -> dict:
    """
    Returns the rate limits (rpm, rpd, tpd) for a provider.
    If model_name is specified and has overrides in PROVIDER_LIMITS[provider]["models"],
    returns the model-specific limits.
    Otherwise returns the provider-level defaults.
    """
    prov_key = provider.lower()
    prov_data = PROVIDER_LIMITS.get(prov_key)
    
    if not prov_data:
        return {}
        
    if model_name:
        model_overrides = prov_data.get("models", {})
        if model_name in model_overrides:
            return model_overrides[model_name]
            
    return {
        "rpm": prov_data.get("rpm", 30),
        "rpd": prov_data.get("rpd", 1000),
        "tpd": prov_data.get("tpd", 200000),
    }


def get_model_specs(provider: str, model_name: str = None) -> dict:
    """
    Returns full specs (context_window, max_output_tokens) for a provider + model combination.
    If called with a single argument, searches across all providers for matching model_name.
    """
    # Handle single argument call: get_model_specs(model_name)
    if model_name is None:
        target_model = provider
        for prov_key, prov_models in MODEL_SPECS.items():
            if target_model in prov_models:
                return prov_models[target_model]
        return {
            "context_window": 8192,
            "max_output_tokens": 4096,
        }

    prov_key = provider.lower()
    prov_models = MODEL_SPECS.get(prov_key, {})
    if model_name in prov_models:
        return prov_models[model_name]

    # Fallback if model not found under specific provider
    return {
        "context_window": 8192,
        "max_output_tokens": 4096,
    }


def get_context_limit(provider_or_model: str, model_name: str = None) -> int:
    """
    Returns the context window limit for a provider + model combination.
    Supports get_context_limit("groq", "openai/gpt-oss-20b") or get_context_limit("openai/gpt-oss-20b").
    """
    specs = get_model_specs(provider_or_model, model_name)
    return specs["context_window"]


def get_max_output_tokens(provider_or_model: str, model_name: str = None) -> int:
    """
    Returns the maximum generation/output token allowance for a provider + model combination.
    Supports get_max_output_tokens("groq", "openai/gpt-oss-20b") or get_max_output_tokens("openai/gpt-oss-20b").
    """
    specs = get_model_specs(provider_or_model, model_name)
    return specs["max_output_tokens"]


def get_groq_model_limits(model_name: str) -> dict:
    """
    Convenience lookup for Groq model limits.
    """
    return get_provider_limits("groq", model_name)
