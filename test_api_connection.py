#!/usr/bin/env python3
"""
Test Claude API connection for LLM-as-a-judge
"""

import os
from anthropic import Anthropic

# Initialize client with your config
client = Anthropic(
    api_key=os.getenv("ANTHROPIC_AUTH_TOKEN"),
    base_url=os.getenv("ANTHROPIC_BEDROCK_BASE_URL")
)

print("Testing Claude API connection...")
print(f"Auth token: {os.getenv('ANTHROPIC_AUTH_TOKEN')[:20]}...")
print(f"Base URL: {os.getenv('ANTHROPIC_BEDROCK_BASE_URL')}")
print()

try:
    print("Sending test message to Claude Haiku 3.5...")
    response = client.messages.create(
        model="claude-3-5-haiku-20241022",
        max_tokens=100,
        messages=[{"role": "user", "content": "Say 'Hello' and return JSON: {\"score\": 10}"}]
    )

    print(f"✅ Response received!")
    print(f"Type: {type(response)}")
    print(f"Response object: {response}")
    print()

    if hasattr(response, 'content'):
        print(f"Content type: {type(response.content)}")
        print(f"Content: {response.content}")
        print()

        if response.content and len(response.content) > 0:
            print(f"First content block: {response.content[0]}")
            if hasattr(response.content[0], 'text'):
                print(f"Text: {response.content[0].text}")
            else:
                print("⚠️  No 'text' attribute on content[0]")
        else:
            print("⚠️  Content is empty")
    else:
        print("⚠️  No 'content' attribute on response")

    print("\n✅ API connection working!")

except Exception as e:
    print(f"❌ Error: {e}")
    print(f"Error type: {type(e)}")
    import traceback
    traceback.print_exc()
