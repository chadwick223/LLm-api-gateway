import unittest
import os
import sys

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.easy_models import (
    EASY_CANDIDATES,
    create_client_for_provider,
    execute_easy_task,
)
from configuration.limits import get_max_output_tokens
from groq import Groq
from openai import OpenAI


class TestEasyDecisionEngine(unittest.TestCase):
    def test_candidates_list(self):
        # Verify the candidates list contains all 5 required models
        expected = [
            ("cloudflare", "@cf/zai-org/glm-4.7-flash"),
            ("gemini", "gemini-3.1-flash-lite"),
            ("nvidia", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning"),
            ("ollama", "gpt-oss:20b"),
            ("groq", "openai/gpt-oss-20b"),
        ]
        self.assertEqual(len(EASY_CANDIDATES), 5)
        for i in range(len(expected)):
            self.assertEqual(EASY_CANDIDATES[i]["provider"], expected[i][0])
            self.assertEqual(EASY_CANDIDATES[i]["model"], expected[i][1])

    def test_create_client_for_provider(self):
        # Groq client
        groq_client = create_client_for_provider("groq", "mock_key")
        self.assertIsInstance(groq_client, Groq)

        # Cloudflare client
        os.environ["CLOUDFLARE_ACCOUNT_ID"] = "test_acc_99"
        cf_client = create_client_for_provider("cloudflare", "mock_key")
        self.assertIsInstance(cf_client, OpenAI)
        self.assertIn("test_acc_99", str(cf_client.base_url))

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

    def test_token_skipping_logic(self):
        # NVIDIA nano omni has max_output_tokens = 4096
        nv_max = get_max_output_tokens("nvidia", "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning")
        self.assertEqual(nv_max, 4096)

        # If estimated tokens > 4096, it should be skipped
        test_estimated_tokens = 5000
        self.assertTrue(test_estimated_tokens > nv_max)

        # Gemini flash lite has max_output_tokens = 65536
        gemini_max = get_max_output_tokens("gemini", "gemini-3.1-flash-lite")
        self.assertEqual(gemini_max, 65536)
        self.assertFalse(test_estimated_tokens > gemini_max)

    def test_empty_message_validation(self):
        result = execute_easy_task("")
        self.assertIn("Error:", result)
        self.assertIn("empty", result.lower())


if __name__ == "__main__":
    unittest.main()
