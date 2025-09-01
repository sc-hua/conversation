#!/usr/bin/env python3
"""
Test script for Ollama qwen2.5vl:3b integration.

Simple test to verify the LLM integration works correctly
with different configurations.
"""

import asyncio
import os
from dotenv import load_dotenv
from modules import StructuredMessageContent
from llm import create_llm

# Load environment variables
load_dotenv()


async def test_llm(llm_type: str):
    """Test LLM with structured content."""
    print(f"\n🧪 Testing {llm_type.upper()} LLM...")
    
    try:
        # Create LLM instance
        llm = create_llm(llm_type)
        
        # Create test structured content
        content = StructuredMessageContent()
        content.add_text("你好，我想测试对话功能", position=0)
        content.add_json({"test": "data", "count": 3}, position=1)
        content.add_text("请分析这些内容", position=2)
        
        # Generate response
        response = await llm.generate_response([], content)
        
        print(f"✅ Response from {llm_type}: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Error testing {llm_type}: {str(e)}")
        return False


async def main():
    """Run tests for available LLMs."""
    print("🚀 LLM Integration Test")
    print("=" * 50)
    
    # Test different LLM types
    llm_types = ['mock']
    
    # Check if ollama is configured
    ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
    if ollama_url:
        llm_types.append('ollama')
    
    # Check if OpenAI is configured
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key and openai_key != 'your_openai_api_key_here':
        llm_types.append('openai')
    
    results = {}
    for llm_type in llm_types:
        results[llm_type] = await test_llm(llm_type)
    
    print("\n📊 Test Results:")
    print("=" * 50)
    for llm_type, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{llm_type.upper()}: {status}")
    
    # Test current configuration
    current_llm_type = os.getenv('LLM_TYPE', 'mock')
    print(f"\n🎯 Current LLM configuration: {current_llm_type.upper()}")
    
    if current_llm_type == 'ollama':
        print(f"   Model: {os.getenv('OLLAMA_MODEL', 'qwen2.5vl:3b')}")
        print(f"   URL: {os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')}")


if __name__ == "__main__":
    asyncio.run(main())
