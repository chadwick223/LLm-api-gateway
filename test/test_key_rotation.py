import sys
import os
import groq
import httpx

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from routing.agent import CodingAgent
import models.easy_models

def main():
    print("="*60)
    print("MOCKING GROQ API TO GUARANTEE RATE LIMIT ERROR")
    print("="*60)
    
    # Initialize agent
    agent = CodingAgent()
    
    # Store the original Groq client before we mock it
    original_groq = models.easy_models.Groq
    call_count = {"count": 0}
    
    # --- MOCK CLASSES ---
    class MockCompletions:
        def __init__(self, real_client):
            self.real_client = real_client
            
        def create(self, *args, **kwargs):
            if call_count["count"] == 0:
                call_count["count"] += 1
                print("\n[MOCK] Intercepted API call! Forcing RateLimitError on the first API key...\n")
                
                # Create a fake httpx Response required by groq.RateLimitError
                fake_request = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
                fake_response = httpx.Response(429, request=fake_request)
                
                raise groq.RateLimitError(
                    "Simulated Rate Limit Error",
                    response=fake_response,
                    body={"error": {"message": "Rate limit exceeded"}}
                )
            else:
                print("\n[MOCK] Second key detected! Allowing request to pass through to real API...\n")
                return self.real_client.chat.completions.create(*args, **kwargs)

    class MockChat:
        def __init__(self, real_client):
            self.completions = MockCompletions(real_client)

    class MockGroq:
        def __init__(self, *args, **kwargs):
            self.real_client = original_groq(*args, **kwargs)
            self.chat = MockChat(self.real_client)

    # Apply the mock directly to the easy_models module
    models.easy_models.Groq = MockGroq

    print("\n" + "="*60)
    print("Now calling agent.run() to verify key rotation...")
    print("="*60 + "\n")
    
    # This will trigger the failover!
    agent.run("correct the syntax issue of this code")

if __name__ == "__main__":
    main()
