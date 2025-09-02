#!/usr/bin/env python3
"""
测试Ollama图片处理功能
"""

import asyncio
import os
from conversation.core import Content, ConversationGraph

async def test_ollama_image():
    """测试Ollama处理图片的能力"""
    print("🖼️ 测试Ollama图片处理功能...")
    
    # 检查图片文件是否存在
    image_paths = [
        "./data/images/test_image.jpg",
        "./images/test_image.jpg", 
        "./test_image.jpg"
    ]
    
    existing_image = None
    for path in image_paths:
        if os.path.exists(path):
            existing_image = path
            break
    
    if not existing_image:
        print("⚠️ 未找到测试图片，创建文本测试...")
        content = Content()
        content.add_text("请介绍一下你的多模态处理能力")
    else:
        print(f"✅ 找到测试图片: {existing_image}")
        content = Content()
        content.add_text("请描述这张图片中的内容")
        content.add_image(existing_image)
    
    print(f"📝 发送内容: {content.to_display_text()}")
    
    # 创建对话图，强制使用ollama
    graph = ConversationGraph(llm='ollama')
    
    try:
        # 发送请求
        result = await graph.chat(
            system_prompt="你是一个专业的图片分析助手，能够详细描述图片内容。",
            content=content
        )
        
        print("\n🤖 Ollama回复:")
        print("=" * 50)
        print(result['response'])
        print("=" * 50)
        print(f"📊 对话统计: {result['message_count']} 条消息")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        print("请检查:")
        print("1. Ollama服务是否运行: ollama serve")
        print("2. 是否安装了支持视觉的模型: ollama pull qwen2.5vl:3b") 
        print("3. .env中OLLAMA_MODEL配置是否正确")

if __name__ == "__main__":
    asyncio.run(test_ollama_image())
