#!/usr/bin/env python3
"""Test script for LLM routing and conversation scenario cost control.

This script verifies:
1. Which conversation scenarios should call real LLM vs. template/mock
2. Whether date/time/reminder questions use optimization paths
3. Whether repeated questions avoid redundant LLM calls
4. Provider fallback behavior
5. Logging and diagnostics accuracy
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add the parent directory to the path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import load_local_env_file
load_local_env_file()

from app.models.user_profile import UserProfile
from app.models.chat_log import ChatLog
from app.services import conversation_style_engine
from app.services.llm_service import (
    LLMConversationInput,
    get_llm_service,
    ProviderSwitchingLLMService,
)


# Test scenarios definition
TEST_SCENARIOS = [
    # Should optimize (not call real LLM for cost control)
    # These scenarios use conversation_style_engine's built-in strategies
    {
        "name": "Clarification Request (Medication)",
        "message": "我应该吃什么药？",
        "should_optimize": True,
        "reason": "Clarification triggers strategy that avoids redundant LLM calls",
        "category": "clarification",
    },
    {
        "name": "Water Reminder Check",
        "message": "我是不是该喝水了？",
        "should_optimize": True,
        "reason": "Current need response uses template, avoids LLM",
        "category": "reminder",
    },
    {
        "name": "Repeated Question (with recent similar)",
        "message": "我是谁？",
        "should_optimize": True,
        "reason": "Repeat question detected, uses repeat_soft_response strategy",
        "category": "repeat",
        "make_recent_similar": True,
    },
    {
        "name": "Memory Question - Direct Lookup",
        "message": "我的女儿叫什么？",
        "should_optimize": True,
        "reason": "Direct memory question can be answered from profile without LLM",
        "category": "memory",
    },
    {
        "name": "Complaint (Why so short?)",
        "message": "为什么只有一句话？",
        "should_optimize": True,
        "reason": "Complaint repair uses template response",
        "category": "complaint",
    },
    # Should allow LLM calls for better personalization
    {
        "name": "Emotional Support",
        "message": "我很害怕，现在怎么办？",
        "should_optimize": False,
        "reason": "Emotional support benefit from LLM personalization",
        "category": "emotional",
    },
    {
        "name": "General Chat",
        "message": "天气真好呀",
        "should_optimize": False,
        "reason": "Normal chat uses LLM for natural responses",
        "category": "general",
    },
    {
        "name": "Reminiscence Guidance",
        "message": "你能帮我想起我小时候的故事吗？",
        "should_optimize": False,
        "reason": "Memory guidance benefits from LLM",
        "category": "reminiscence",
    },
]


def analyze_conversation_scenario(message: str, recent_logs: list[ChatLog] | None = None) -> dict:
    """Analyze whether a message should trigger optimization (avoid LLM)."""
    if recent_logs is None:
        recent_logs = []
    
    state = conversation_style_engine.detect_user_state(message, recent_logs)
    strategy = conversation_style_engine.decide_strategy(state)
    
    # Determine if this should be optimized (no real LLM call)
    # Optimization scenarios based on conversation_style_engine strategies:
    # 1. repeat_soft_response - repeated questions (don't call LLM each time)
    # 2. current_need_response - medication, water, immediate needs
    # 3. clarification_repair - clarifications (use template)
    # 4. complaint_repair - complaint tone (use template repair)
    # 5. memory_question + direct profile lookup - name, family info, etc.
    
    should_avoid_llm = strategy in {
        "repeat_soft_response",
        "current_need_response",
        "clarification_repair",
        "complaint_repair",
    }
    
    # For memory questions, check if it's a direct factual question
    # that can be answered from profile (name, family, age, hometown)
    if state.memory_question and state.input_kind == "memory_question":
        should_avoid_llm = True
    
    return {
        "state": state,
        "strategy": strategy,
        "should_avoid_llm": should_avoid_llm,
        "reason": f"Strategy={strategy}, Input={state.input_kind}",
    }


def test_scenario(scenario: dict) -> dict:
    """Test a single conversation scenario."""
    print(f"\n{'='*70}")
    print(f"Test: {scenario['name']}")
    print(f"Message: {scenario['message']}")
    print(f"Expected: {'Optimize (avoid LLM)' if scenario['should_optimize'] else 'Allow LLM'}")
    print('-'*70)
    
    # Create recent logs
    recent_logs = []
    if scenario.get("make_recent_similar"):
        # Add a similar recent question to trigger repeat detection
        recent_logs = [
            ChatLog(
                id=1,
                user_id=1,
                role="user",
                message="我是谁？",
                timestamp="2026-05-13T10:00:00",
                mode="alzheimer",
                keyword_tags="memory_question",
                repeated_flag=False,
            ),
            ChatLog(
                id=2,
                user_id=1,
                role="assistant",
                message="你是王阿姨，大家都叫你小王。",
                timestamp="2026-05-13T10:00:05",
                mode="alzheimer",
                keyword_tags="memory_response",
                repeated_flag=False,
            ),
        ]
    
    # Analyze the scenario
    analysis = analyze_conversation_scenario(scenario["message"], recent_logs)
    
    # Print analysis
    print(f"Input Kind: {analysis['state'].input_kind}")
    print(f"Strategy: {analysis['strategy']}")
    print(f"Should Avoid LLM: {analysis['should_avoid_llm']}")
    print(f"Analysis: {analysis['reason']}")
    
    # Check if it matches expectation
    matches_expectation = (
        analysis['should_avoid_llm'] == scenario['should_optimize']
    )
    
    status = "✓ PASS" if matches_expectation else "❌ FAIL"
    print(f"\n{status}")
    print(f"Expected optimization: {scenario['should_optimize']}")
    print(f"Got optimization: {analysis['should_avoid_llm']}")
    
    if not matches_expectation:
        print(f"Expected reason: {scenario['reason']}")
    
    return {
        "name": scenario["name"],
        "passed": matches_expectation,
        "strategy": analysis["strategy"],
        "should_avoid_llm": analysis["should_avoid_llm"],
    }


def test_provider_fallback() -> dict:
    """Test provider fallback when API key is missing."""
    print(f"\n{'='*70}")
    print("Test: Provider Fallback (No API Key)")
    print('-'*70)
    
    try:
        # Force use of a provider without API key
        service = ProviderSwitchingLLMService(provider_override="deepseek")
        
        profile = UserProfile(id=1, name="Test User")
        conversation = LLMConversationInput(
            system_prompt="Test",
            support_mode="alzheimer",
            profile=profile,
            recent_logs=[],
            user_message="你好",
            context_text="",
            memory_summary="",
            last_reply="",
        )
        
        result = service.generate_reply_result(conversation)
        
        print(f"Requested Provider: {result.requested_provider}")
        print(f"Actual Provider: {result.actual_provider}")
        print(f"Model: {result.model}")
        print(f"Fallback Used: {result.fallback_used}")
        print(f"Fallback Reason: {result.fallback_reason}")
        
        # Check if fallback worked
        is_fallback = result.fallback_used and result.actual_provider == "mock"
        status = "✓ PASS" if is_fallback else "❌ FAIL"
        print(f"\n{status}")
        
        return {
            "name": "Provider Fallback",
            "passed": is_fallback,
            "fallback_used": result.fallback_used,
            "reason": result.fallback_reason,
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"name": "Provider Fallback", "passed": False, "error": str(e)}


def test_llm_reply_result_completeness() -> dict:
    """Test that LLMReplyResult contains all necessary diagnostic info."""
    print(f"\n{'='*70}")
    print("Test: LLMReplyResult Completeness")
    print('-'*70)
    
    try:
        service = ProviderSwitchingLLMService(provider_override="mock")
        
        profile = UserProfile(id=1, name="Test User")
        conversation = LLMConversationInput(
            system_prompt="Test",
            support_mode="alzheimer",
            profile=profile,
            recent_logs=[],
            user_message="你好",
            context_text="",
            memory_summary="",
            last_reply="",
        )
        
        result = service.generate_reply_result(conversation)
        
        # Check all required fields
        required_fields = [
            "reply",
            "requested_provider",
            "actual_provider",
            "model",
            "fallback_used",
            "fallback_reason",
            "guard_triggered",
            "guard_reason",
        ]
        
        missing_fields = []
        for field in required_fields:
            if not hasattr(result, field):
                missing_fields.append(field)
            else:
                value = getattr(result, field)
                print(f"  {field}: {value!r}")
        
        all_present = len(missing_fields) == 0
        status = "✓ PASS" if all_present else "❌ FAIL"
        print(f"\n{status}")
        
        if missing_fields:
            print(f"Missing fields: {missing_fields}")
        
        return {
            "name": "LLMReplyResult Completeness",
            "passed": all_present,
            "missing_fields": missing_fields,
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {"name": "LLMReplyResult Completeness", "passed": False, "error": str(e)}


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("LLM Routing and Conversation Cost Control Tests")
    print("="*70)
    
    # Run scenario tests
    scenario_results = []
    for scenario in TEST_SCENARIOS:
        result = test_scenario(scenario)
        scenario_results.append(result)
    
    # Run fallback test
    fallback_result = test_provider_fallback()
    
    # Run result completeness test
    completeness_result = test_llm_reply_result_completeness()
    
    # Print summary
    print(f"\n{'='*70}")
    print("Test Summary")
    print('='*70)
    
    print("\n📊 Conversation Scenarios:")
    for result in scenario_results:
        status = "✓" if result["passed"] else "❌"
        print(f"  {status} {result['name']:30} (Strategy: {result['strategy']})")
    
    print("\n🔄 Fallback Tests:")
    print(f"  {'✓' if fallback_result['passed'] else '❌'} {fallback_result['name']}")
    if fallback_result.get('fallback_reason'):
        print(f"     Reason: {fallback_result['fallback_reason']}")
    
    print("\n📋 Result Completeness:")
    print(f"  {'✓' if completeness_result['passed'] else '❌'} {completeness_result['name']}")
    if completeness_result.get('missing_fields'):
        print(f"     Missing: {completeness_result['missing_fields']}")
    
    # Calculate pass rate
    scenario_passed = sum(1 for r in scenario_results if r["passed"])
    total_tests = len(scenario_results) + 2  # scenarios + fallback + completeness
    passed_tests = scenario_passed + (1 if fallback_result["passed"] else 0) + (1 if completeness_result["passed"] else 0)
    
    print(f"\n{'='*70}")
    print(f"Total: {passed_tests}/{total_tests} tests passed")
    print('='*70 + "\n")
    
    return 0 if passed_tests == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())
