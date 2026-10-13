import unittest
import os
import sys

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Set mock env variables for testing configuration modules
os.environ["CLOUDFLARE_API_KEY"] = "mock_cf_token"
os.environ["CLOUDFLARE_ACCOUNT_ID"] = "mock_account_123"
os.environ["GEMINI_API_KEY"] = "mock_gemini_key"
os.environ["NVIDIA_API_KEY"] = "mock_nv_key"
os.environ["OLLAMA_API_KEY"] = "ollama"
os.environ["OLLAMA_BASE_URL"] = "http://localhost:11434/v1"

import configuration.cloudflareapi_configuration as cf_config
import configuration.gemini_configuration as gemini_config
import configuration.nvedia_configuration as nv_config
import configuration.ollama_configuration as ollama_config
from configuration.limits import (
    PROVIDER_LIMITS,
    MODEL_SPECS,
    MODEL_CONTEXT_LIMITS,
    get_provider_limits,
    get_model_specs,
    get_context_limit,
    get_max_output_tokens,
    get_groq_model_limits,
)
from configuration.key_pool import KeyPoolManager
from configuration.usage_store import UsageStoreManager
from configuration.rate_limiter import RateLimiterManager


class TestProviderConfigurations(unittest.TestCase):
    def test_cloudflare_configuration(self):
        models = cf_config.CODING_MODELS
        self.assertEqual(models["qwen_2_5_coder_32b"], "@cf/qwen/qwen2.5-coder-32b-instruct")
        self.assertEqual(models["gpt_oss_120b"], "@cf/openai/gpt-oss-120b")
        self.assertEqual(models["qwen3_30b"], "@cf/qwen/qwen3-30b-a3b-fp8")
        self.assertEqual(models["glm_4_7_flash"], "@cf/zai-org/glm-4.7-flash")
        self.assertIn("mock_account_123", str(cf_config.client.base_url))

    def test_gemini_configuration(self):
        models = gemini_config.CODING_MODELS
        self.assertEqual(models["gemini_3_1_flash_lite"], "gemini-3.1-flash-lite")
        self.assertEqual(models["gemini_3_6_flash"], "gemini-3.6-flash")

    def test_nvidia_configuration(self):
        models = nv_config.CODING_MODELS
        self.assertEqual(models["nemotron_3_super_120b"], "nvidia/nemotron-3-super-120b-a12b")
        self.assertEqual(models["nemotron_3_ultra_550b"], "nvidia/nemotron-3-ultra-550b-a55b")
        self.assertEqual(models["nemotron_3_nano_omni_30b"], "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning")
        self.assertEqual(str(nv_config.client.base_url).rstrip("/"), "https://integrate.api.nvidia.com/v1")

    def test_ollama_configuration(self):
        models = ollama_config.CODING_MODELS
        self.assertEqual(models["gemma4_31b"], "gemma4:31b")
        self.assertEqual(models["gpt_oss_120b"], "gpt-oss:120b")
        self.assertEqual(models["gpt_oss_20b"], "gpt-oss:20b")
        self.assertIn("localhost:11434", str(ollama_config.client.base_url))

    def test_unified_provider_limits(self):
        # All active providers must be present in PROVIDER_LIMITS
        expected_providers = ["groq", "gemini", "cloudflare", "nvidia", "ollama"]
        for provider in expected_providers:
            self.assertIn(provider, PROVIDER_LIMITS)
            limits = get_provider_limits(provider)
            self.assertIn("rpm", limits)
            self.assertIn("rpd", limits)
            self.assertIn("tpd", limits)

        # Together AI should not be present
        self.assertNotIn("together", PROVIDER_LIMITS)

        # Model overrides
        cf_frontier = get_provider_limits("cloudflare", "@cf/openai/gpt-oss-120b")
        self.assertEqual(cf_frontier["rpm"], 50)

        groq_model = get_provider_limits("groq", "openai/gpt-oss-120b")
        self.assertEqual(groq_model["tpd"], 200000)

    def test_rate_limiter_check_limit_status(self):
        key_pool = KeyPoolManager()
        usage_store = UsageStoreManager()
        limiter = RateLimiterManager(key_pool, usage_store)

        # Check status for Cloudflare
        status = limiter.check_limit_status("cloudflare", key_index=0)
        self.assertEqual(status["provider"], "cloudflare")
        self.assertEqual(status["rpm"]["limit"], 300)
        self.assertIn("exceeded", status["rpm"])
        self.assertIn("exceeded", status["rpd"])
        self.assertIn("exceeded", status["tpd"])

        # Check status with model override
        status_model = limiter.check_limit_status("cloudflare", key_index=0, model_name="@cf/openai/gpt-oss-120b")
    def test_model_specs_and_max_output_tokens(self):
        # Cloudflare specs
        self.assertEqual(get_max_output_tokens("cloudflare", "@cf/qwen/qwen2.5-coder-32b-instruct"), 32768)
        self.assertEqual(get_context_limit("cloudflare", "@cf/qwen/qwen2.5-coder-32b-instruct"), 32768)
        self.assertEqual(get_max_output_tokens("cloudflare", "@cf/openai/gpt-oss-120b"), 65536)
        self.assertEqual(get_max_output_tokens("cloudflare", "@cf/qwen/qwen3-30b-a3b-fp8"), 8192)
        self.assertEqual(get_max_output_tokens("cloudflare", "@cf/zai-org/glm-4.7-flash"), 8192)

        # Gemini specs
        self.assertEqual(get_max_output_tokens("gemini", "gemini-3.1-flash-lite"), 65536)
        self.assertEqual(get_context_limit("gemini", "gemini-3.1-flash-lite"), 1048576)

        # NVIDIA specs
        self.assertEqual(get_max_output_tokens("nvidia", "nvidia/nemotron-3-super-120b-a12b"), 65536)
        self.assertEqual(get_max_output_tokens("nvidia", "nvidia/nemotron-3-ultra-550b-a55b"), 65536)
        self.assertEqual(get_max_output_tokens("nvidia", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"), 4096)

        # Ollama specs
        self.assertEqual(get_max_output_tokens("ollama", "gemma4:31b"), 32768)
        self.assertEqual(get_max_output_tokens("ollama", "gpt-oss:120b"), 32768)
        self.assertEqual(get_max_output_tokens("ollama", "gpt-oss:20b"), 32768)

        # Groq specs
        self.assertEqual(get_max_output_tokens("groq", "openai/gpt-oss-20b"), 8000)

        # Fallback for unknown provider/model
        fallback_specs = get_model_specs("unknown_provider", "unknown_model")
        self.assertEqual(fallback_specs["max_output_tokens"], 4096)
        self.assertEqual(fallback_specs["context_window"], 8192)


if __name__ == "__main__":
    unittest.main()

