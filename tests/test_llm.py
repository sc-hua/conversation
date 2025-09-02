#!/usr/bin/env python3
"""
Test LLM providers with different content types.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
load_dotenv()

from conversation.core.modules import Content
from conversation.llm import OpenAILLM, OllamaLLM, MockLLM


async def test_llm(llm_name: str):
    """Test LLM with content."""
    print(f"\n🧪 Testing {llm_name.upper()} LLM...")
    
    try:
        # Create LLM instance
        if llm_name == 'openai':
            llm = OpenAILLM()
        elif llm_name == 'ollama':
            llm = OllamaLLM()
        else:
            llm = MockLLM()
        
        # Create test content
        content = Content()
        content.add_text("你好，我想测试对话功能", position=0)
        content.add_json({"test": "data", "count": 3}, position=1)
        content.add_text("请分析这些内容", position=2)
        
        # Generate response
        response = await llm.generate_response([], content)
        
        print(f"✅ Response from {llm_name}: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Error testing {llm_name}: {str(e)}")
        return False


async def main():
    """Run tests for available LLMs."""
    print("🚀 LLM Integration Test")
    print("=" * 50)
    
    # Test different LLM types
    llm_names = ['mock']
    
    # Check if ollama is configured
    ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    if ollama_url:
        llm_names.append('ollama')
    
    # Check if OpenAI is configured
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key and openai_key != 'your_openai_api_key_here':
        llm_names.append('openai')
    
    results = {}
    for llm_name in llm_names:
        results[llm_name] = await test_llm(llm_name)
    
    print("\n📊 Test Results:")
    print("=" * 50)
    for llm_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{llm_name.upper()}: {status}")
    
    # Test current configuration
    current_llm_name = os.getenv('LLM_NAME', 'mock')
    print(f"\n🎯 Current LLM configuration: {current_llm_name.upper()}")

    if current_llm_name == 'ollama':
        print(f"   Model: {os.getenv('OLLAMA_MODEL', 'qwen2.5vl:3b')}")
        print(f"   URL: {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")


if __name__ == "__main__":
    asyncio.run(main())
