#!/usr/bin/env python3
"""
Quick test to verify Claude API connection before running GEPA optimization.
"""

import os
from anthropic import Anthropic

def test_claude_connection():
    """Test connection to Claude API via Bedrock."""

    print("🔍 Testing Claude API connection...")
    print()

    # Check environment variables
    auth_token = os.getenv("ANTHROPIC_AUTH_TOKEN")
    base_url = os.getenv("ANTHROPIC_BEDROCK_BASE_URL")

    if not auth_token:
        print("❌ ANTHROPIC_AUTH_TOKEN not set")
        return False

    if not base_url:
        print("❌ ANTHROPIC_BEDROCK_BASE_URL not set")
        return False

    print(f"✓ Auth token: {auth_token[:10]}...")
    print(f"✓ Base URL: {base_url}")
    print()

    try:
        # Initialize client
        client = Anthropic(
            api_key=auth_token,
            base_url=base_url
        )

        print("📡 Sending test request to Claude Haiku 3.5...")

        # Test with Haiku (cheaper, faster)
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Say 'Hello from Claude!' if you can hear me."}
            ]
        )

        print(f"✅ Response received: {response.content[0].text}")
        print()

        print("📡 Testing Claude Sonnet 3.5...")

        # Test with Sonnet
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=100,
            messages=[
                {"role": "user", "content": "Respond with 'Ready for GEPA optimization!' if you're working."}
            ]
        )

        print(f"✅ Response received: {response.content[0].text}")
        print()

        print("🎉 Claude API connection successful!")
        print("   Ready to run GEPA optimization with:")
        print("   - Task model: claude-3-5-sonnet-20241022")
        print("   - Reflection model: claude-3-5-haiku-20241022")
        print()
        print("Next steps:")
        print("   python gepa_optimize.py --iterations 10  # Quick test")
        print("   python gepa_optimize.py --iterations 100 # Full optimization")

        return True

    except Exception as e:
        print(f"❌ Error connecting to Claude API: {e}")
        print()
        print("Troubleshooting:")
        print("1. Verify your auth token is valid")
        print("2. Check network connectivity to Salesforce proxy")
        print("3. Ensure CLAUDE_CODE_USE_BEDROCK=1 is set")
        return False

if __name__ == "__main__":
    success = test_claude_connection()
    exit(0 if success else 1)
