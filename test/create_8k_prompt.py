import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from configuration.token_estimation import estimate_token

# Build a prompt that routes to Easy (via semantic router) and exceeds 8,000 tokens
header = "can you fix the formatting of this python file?\n"
# Each line is ~9 tokens
body_lines = ["# line_item_test_variable = 1234567890 + index\n" for _ in range(950)]
prompt = header + "".join(body_lines)

token_count = estimate_token(prompt)
print(f"Generated prompt length: {len(prompt)} characters, estimated tokens: {token_count}")

prompt_file_path = os.path.join(os.path.dirname(__file__), "temp_8k_prompt.txt")
with open(prompt_file_path, "w", encoding="utf-8") as f:
    f.write(prompt)

print(f"Saved prompt to: {prompt_file_path}")
