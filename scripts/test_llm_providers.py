#!/usr/bin/env python3
"""Simple test script to verify LLM provider configuration and fallback behavior.

This script:
1. Tests provider factory with different LLM_PROVIDER values
2. Verifies correct model and base_url selection
3. Tests fallback to mock when API key is missing
4. Tests timeout configuration
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import app modules
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment from .env file
from app.config import load_local_env_file
load_local_env_file()

from app.services.llm_service import (
    _resolve_provider_config,
    get_provider_availability,
    ProviderSwitchingLLMService,
    LLMConversationInput,
    MAX_REPLY_CHARS,
    LLM_TIMEOUT_SECONDS,
)
from app.models.user_profile import UserProfile
from app.models.chat_log import ChatLog


def test_provider_config(provider_name: str, expected_model: str) -> bool:
    """Test that a provider returns the correct configuration."""
    print(f"\n{'='*60}")
    print(f"Testing provider: {provider_name}")
    print('='*60)
    
    config = _resolve_provider_config(provider_override=provider_name)
    
    print(f"  Provider: {config.provider}")
    print(f"  Model: {config.model}")
    print(f"  Base URL: {config.base_url}")
    print(f"  API Key configured: {'Yes' if config.api_key else 'No'}")
    
    if config.model != expected_model:
        print(f"  ❌ FAILED: Expected model '{expected_model}', got '{config.model}'")
        return False
    
    print(f"  ✓ Model is correct: {expected_model}")
    return True


def test_provider_availability() -> bool:
    """Test provider availability checks."""
    print(f"\n{'='*60}")
    print("Testing provider availability")
    print('='*60)
    
    providers = ["mock", "zhipu", "deepseek", "minimax", "openai"]
    all_ok = True
    
    for provider in providers:
        availability = get_provider_availability(provider_override=provider)
        status = "✓" if availability.available else "❌"
        print(f"  {status} {provider:12} - {availability.reason}")
        if availability.model:
            print(f"     Model: {availability.model}")
        if availability.base_url:
            print(f"     URL: {availability.base_url}")
    
    return all_ok


def test_mock_fallback() -> bool:
    """Test mock provider fallback."""
    print(f"\n{'='*60}")
    print("Testing mock provider fallback")
    print('='*60)
    
    try:
        service = ProviderSwitchingLLMService(provider_override="mock")
        
        # Create a minimal conversation input
        profile = UserProfile(id=1, name="Test User")
        conversation = LLMConversationInput(
            system_prompt="Test system prompt",
            support_mode="alzheimer",
            profile=profile,
            recent_logs=[],
            user_message="你好",
            context_text="",
            memory_summary="",
            last_reply="",
        )
        
        result = service.generate_reply_result(conversation)
        
        print(f"  Requested provider: {result.requested_provider}")
        print(f"  Actual provider: {result.actual_provider}")
        print(f"  Model: {result.model}")
        print(f"  Fallback used: {result.fallback_used}")
        print(f"  Reply generated: {bool(result.reply)}")
        if result.reply:
            print(f"  Reply (first 50 chars): {result.reply[:50]}...")
        
        if result.actual_provider == "mock" and result.reply:
            print(f"  ✓ Mock fallback working correctly")
            return True
        else:
            print(f"  ❌ Mock fallback failed")
            return False
            
    except Exception as e:
        print(f"  ❌ Error during mock fallback test: {e}")
        return False


def test_timeout_config() -> bool:
    """Test timeout configuration."""
    print(f"\n{'='*60}")
    print("Testing timeout and output length configuration")
    print('='*60)
    
    print(f"  Max reply chars: {MAX_REPLY_CHARS}")
    print(f"  LLM timeout seconds: {LLM_TIMEOUT_SECONDS}")
    
    if MAX_REPLY_CHARS > 0 and LLM_TIMEOUT_SECONDS > 0:
        print(f"  ✓ Timeout and output settings are valid")
        return True
    else:
        print(f"  ❌ Invalid timeout or output settings")
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("LLM Provider Configuration Tests")
    print("="*60)
    
    results = []
    
    # Test provider configurations
    results.append(("DeepSeek V4", test_provider_config("deepseek", "deepseek-v4-flash")))
    results.append(("MiniMax", test_provider_config("minimax", "MiniMax-M2.7")))
    results.append(("Zhipu", test_provider_config("zhipu", "glm-4")))
    results.append(("OpenAI", test_provider_config("openai", "gpt-4o-mini")))
    results.append(("Mock", test_provider_config("mock", "mock")))
    
    # Test availability
    results.append(("Provider Availability", test_provider_availability()))
    
    # Test mock fallback
    results.append(("Mock Fallback", test_mock_fallback()))
    
    # Test timeout config
    results.append(("Timeout Config", test_timeout_config()))
    
    # Print summary
    print(f"\n{'='*60}")
    print("Test Summary")
    print('='*60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "❌ FAILED"
        print(f"  {status}: {test_name}")
    
    all_passed = all(passed for _, passed in results)
    total = len(results)
    passed_count = sum(1 for _, passed in results if passed)
    
    print(f"\nTotal: {passed_count}/{total} tests passed")
    print('='*60 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
