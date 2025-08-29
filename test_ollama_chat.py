#!/usr/bin/env python3
"""
Simple test script for Ollama qwen2.5vl:3b integration.

Tests the complete conversation system with Ollama.
"""

import asyncio
import os
from dotenv import load_dotenv
from conversation_graph import ConversationGraph
from models import StructuredMessageContent

# Load environment variables
load_dotenv()


async def test_ollama_conversation():
    """Test a simple conversation with Ollama qwen2.5vl:3b."""
    print("🤖 Testing Ollama qwen2.5vl:3b Conversation")
    print("=" * 50)
    
    # Create conversation graph
    graph = ConversationGraph()
    
    # Test 1: Simple text conversation
    print("\n1️⃣ Simple text conversation:")
    simple_content = StructuredMessageContent()
    simple_content.add_text("你好，请介绍一下你自己。")
    
    result1 = await graph.chat(
        system_prompt="你是一个友好的AI助手，使用中文回答问题。",
        structured_content=simple_content
    )
    
    print(f"输入: {result1['input_preview']}")
    print(f"回复: {result1['response']}")
    
    # Test 2: Structured content with JSON
    print("\n2️⃣ Structured content with JSON:")
    structured_content = StructuredMessageContent()
    structured_content.add_text("请分析以下数据：", position=0)
    structured_content.add_json({
        "product": "智能手机",
        "sales": 1500,
        "month": "8月",
        "growth": "+12%"
    }, position=1)
    structured_content.add_text("这些销售数据表现如何？", position=2)
    
    result2 = await graph.chat(
        conversation_id=result1['conversation_id'],  # Continue same conversation
        structured_content=structured_content
    )
    
    print(f"输入: {result2['input_preview']}")
    print(f"回复: {result2['response']}")
    
    # Test 3: Multi-modal with image reference
    print("\n3️⃣ Multi-modal content:")
    multimodal_content = StructuredMessageContent()
    multimodal_content.add_text("我有一张图片和数据需要分析", position=0)
    multimodal_content.add_image("data_chart.png", position=1)
    multimodal_content.add_json({
        "chart_type": "柱状图",
        "data_points": 24,
        "trend": "上升"
    }, position=2)
    multimodal_content.add_text("请综合分析图片和数据", position=3)
    
    result3 = await graph.chat(
        conversation_id=result1['conversation_id'],
        structured_content=multimodal_content,
        is_final=True  # Save conversation to file
    )
    
    print(f"输入: {result3['input_preview']}")
    print(f"回复: {result3['response']}")
    
    print(f"\n✅ 对话完成! 对话ID: {result1['conversation_id']}")
    print(f"📊 总消息数: {result3['message_count']}")


async def main():
    """Run the test."""
    current_llm = os.getenv('LLM_TYPE', 'mock')
    print(f"当前LLM配置: {current_llm.upper()}")
    
    if current_llm == 'ollama':
        model = os.getenv('OLLAMA_MODEL', 'qwen2.5vl:3b')
        url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        print(f"Ollama模型: {model}")
        print(f"Ollama地址: {url}")
    
    try:
        await test_ollama_conversation()
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
