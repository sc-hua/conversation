#!/usr/bin/env python3
"""
Test script to verify Ollama integration with conversation graph.
"""

import os
import asyncio
from dotenv import load_dotenv
load_dotenv()

from conversation.core import ConversationGraph, Content


async def test_ollama_conversation():
    """Test a simple conversation with Ollama qwen2.5vl:3b."""
    print("🤖 Testing Ollama qwen2.5vl:3b Conversation")
    print("=" * 50)
    
    # Create conversation graph
    graph = ConversationGraph()
    
    # Test 1: Simple text conversation
    print("\n1️⃣ Simple text conversation:")
    simple_content = Content()
    simple_content.add_text("你好，请介绍一下你自己。")
    
    result1 = await graph.chat(
        system_prompt="你是一个友好的AI助手，使用中文回答问题。",
        content=simple_content
    )
    
    print(f"输入: {result1['input_preview']}")
    print(f"回复: {result1['response']}")
    
    # Test 2: Content with JSON
    print("\n2️⃣ Content with JSON:")
    content = Content()
    content.add_text("请分析以下数据：")
    content.add_json({
        "销售额": 150000,
        "客户数": 245,
        "增长率": "15%",
        "地区": "华东"
    })
    content.add_text("这些销售数据表现如何？")
    
    result2 = await graph.chat(
        conversation_id=result1['conversation_id'],  # Continue same conversation
        content=content
    )
    
    print(f"输入: {result2['input_preview']}")
    print(f"回复: {result2['response']}")
    
    # Test 3: Multi-modal with image reference
    print("\n3️⃣ Multi-modal content:")
    multimodal_content = Content()
    multimodal_content.add_text("我有一张图片和数据需要分析")
    multimodal_content.add_image("data_chart.png")
    multimodal_content.add_json({
        "图片类型": "数据图表",
        "数据点": 12,
        "趋势": "上升"
    })
    multimodal_content.add_text("请综合分析图片和数据")
    
    result3 = await graph.chat(
        conversation_id=result1['conversation_id'],
        content=multimodal_content,
        is_final=True  # Save conversation to file
    )
    
    print(f"输入: {result3['input_preview']}")
    print(f"回复: {result3['response']}")
    
    print(f"\n✅ 对话完成! 对话ID: {result1['conversation_id']}")
    print(f"📊 总消息数: {result3['message_count']}")


async def main():
    """Run the test."""
    current_llm = os.getenv('LLM_NAME', 'mock')
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
