import unittest
import os
import sys

# Ensure project root is in sys.path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from configuration.token_estimation.estimator import (
    create_message_payload,
    validate_message_payload,
    estimate_token_from_text,
    estimate_token,
    CHAR_THRESHOLD,
)
from configuration.limits import get_context_limit, MODEL_CONTEXT_LIMITS


class TestTokenEstimator(unittest.TestCase):
    def test_layer1_create_message_payload(self):
        # Test normal string
        payload = create_message_payload("Hello world")
        self.assertIsInstance(payload, dict)
        self.assertIn("message", payload)
        self.assertEqual(payload["message"], "Hello world")

        # Test None input
        payload_none = create_message_payload(None)
        self.assertIsInstance(payload_none, dict)
        self.assertEqual(payload_none["message"], "")

    def test_layer2_validate_message_payload(self):
        # Valid message
        valid_payload = {"message": "Write a python function"}
        self.assertTrue(validate_message_payload(valid_payload))

        # Empty string
        empty_payload = {"message": ""}
        with self.assertRaises(ValueError):
            validate_message_payload(empty_payload)

        # Whitespace-only string
        whitespace_payload = {"message": "   \n\t  "}
        with self.assertRaises(ValueError):
            validate_message_payload(whitespace_payload)

    def test_layer3_estimate_under_60k_chars(self):
        # Short message under 60k chars should use tiktoken BPE cl100k_base
        text = "Hello world! This is a test."
        tokens = estimate_token_from_text(text)
        self.assertGreater(tokens, 0)
        self.assertLess(tokens, 20)

    def test_layer3_estimate_over_60k_chars(self):
        # Payload over 60,000 characters should use char_count // 4
        large_text = "a" * 80000
        tokens = estimate_token_from_text(large_text)
        expected_tokens = 80000 // 4
        self.assertEqual(tokens, expected_tokens)

    def test_end_to_end_estimate_token(self):
        # Valid execution
        token_count = estimate_token("print('hello world')")
        self.assertIsInstance(token_count, int)
        self.assertGreater(token_count, 0)

        # Empty execution raises ValueError
        with self.assertRaises(ValueError):
            estimate_token("")

    def test_model_context_limits(self):
        # Check known models across providers
        self.assertEqual(get_context_limit("openai/gpt-oss-20b"), 131072)
        self.assertEqual(get_context_limit("openai/gpt-oss-120b"), 131072)
        self.assertEqual(get_context_limit("gemini-3.1-flash-lite"), 1048576)
        self.assertEqual(get_context_limit("@cf/qwen/qwen2.5-coder-32b-instruct"), 32768)
        self.assertEqual(get_context_limit("nvidia/nemotron-3-super-120b-a12b"), 1048576)
        self.assertEqual(get_context_limit("gemma4:31b"), 131072)

        # Check unknown model fallback
        self.assertEqual(get_context_limit("non_existent_model"), 8192)


if __name__ == "__main__":
    unittest.main()
