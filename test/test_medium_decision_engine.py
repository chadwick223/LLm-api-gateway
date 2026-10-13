import unittest
import os
import sys

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.medium_models import (
    MEDIUM_CANDIDATES,
    create_client_for_provider,
    execute_medium_task,
)
from configuration.limits import get_max_output_tokens
from groq import Groq
from openai import OpenAI


class TestMediumDecisionEngine(unittest.TestCase):
    def test_medium_candidates_list(self):
        # Verify the medium candidates list contains all 8 required models in order
        expected = [
            ("cloudflare", "@cf/openai/gpt-oss-120b"),
            ("cloudflare", "@cf/qwen/qwen2.5-coder-32b-instruct"),
            ("cloudflare", "@cf/qwen/qwen3-30b-a3b-fp8"),
            ("gemini", "gemini-3.6-flash"),
            ("nvidia", "nvidia/nemotron-3-super-120b-a12b"),
            ("nvidia", "nvidia/nemotron-3-ultra-550b-a55b"),
            ("ollama", "gpt-oss:120b"),
            ("groq", "openai/gpt-oss-120b"),
        ]
        self.assertEqual(len(MEDIUM_CANDIDATES), 8)
        for i in range(len(expected)):
            self.assertEqual(MEDIUM_CANDIDATES[i]["provider"], expected[i][0])
            self.assertEqual(MEDIUM_CANDIDATES[i]["model"], expected[i][1])

    def test_create_client_for_provider(self):
        # Groq client
        groq_client = create_client_for_provider("groq", "mock_key")
        self.assertIsInstance(groq_client, Groq)

        # Cloudflare client
        os.environ["CLOUDFLARE_ACCOUNT_ID"] = "test_acc_medium"
        cf_client = create_client_for_provider("cloudflare", "mock_key")
        self.assertIsInstance(cf_client, OpenAI)
        self.assertIn("test_acc_medium", str(cf_client.base_url))

        # Gemini client
        gemini_client = create_client_for_provider("gemini", "mock_key")
        self.assertIsInstance(gemini_client, OpenAI)
        self.assertIn("generativelanguage.googleapis.com", str(gemini_client.base_url))

        # NVIDIA client
        nv_client = create_client_for_provider("nvidia", "mock_key")
        self.assertIsInstance(nv_client, OpenAI)
        self.assertIn("integrate.api.nvidia.com", str(nv_client.base_url))

        # Ollama client
        ollama_client = create_client_for_provider("ollama", "mock_key")
        self.assertIsInstance(ollama_client, OpenAI)

    def test_token_output_capacity_lookup(self):
        # Cloudflare gpt-oss-120b has max_output_tokens = 65536
        cf_max = get_max_output_tokens("cloudflare", "@cf/openai/gpt-oss-120b")
        self.assertEqual(cf_max, 65536)

        # Gemini 3.6 flash has max_output_tokens = 65536
        gemini_max = get_max_output_tokens("gemini", "gemini-3.6-flash")
        self.assertEqual(gemini_max, 65536)

        # Groq gpt-oss-120b has max_output_tokens = 8000
        groq_max = get_max_output_tokens("groq", "openai/gpt-oss-120b")
        self.assertEqual(groq_max, 8000)

    def test_empty_message_validation(self):
        result = execute_medium_task("")
        self.assertIn("Error:", result)
        self.assertIn("empty", result.lower())


if __name__ == "__main__":
    unittest.main()
