#!/usr/bin/env python3
"""
测试 ConversationGraph 的图对话流程功能，以及图片加载功能
"""

import asyncio
import uuid
import os
from datetime import datetime

from conversation.core import Content, ConversationGraph


async def test_two_round_conversation():
    """使用 ConversationGraph 测试两轮对话功能"""
    
    # 检查是否有 OpenAI API Key
    openai_key = os.getenv('OPENAI_API_KEY')
    if openai_key and openai_key != 'your_openai_api_key_here':
        # 使用 OpenAI
        llm_name = 'openai'
        print("使用 OpenAI 模型进行测试")
    else:
        # 使用 Mock LLM
        llm_name = 'mock'
        print("使用 Mock 模型进行测试（请在 .env 中配置真实的 OPENAI_API_KEY 以使用 OpenAI）")
    
    # 创建 ConversationGraph 实例
    graph = ConversationGraph(llm=llm_name)
    
    # 设置系统提示
    system_prompt = "你是一个友好的AI助手，能够处理文本和图片内容。"
    
    # 第一轮对话
    print("\n=== 第一轮对话 ===")
    
    # 创建第一个输入
    first_input = Content()
    first_input.add_text("你好，请简单介绍一下你自己。")
    
    # 发送第一轮消息
    result1 = await graph.chat(
        system_prompt=system_prompt,
        content=first_input,
        is_final=False
    )
    
    print(f"用户: {first_input.to_display_text()}")
    print(f"助手: {result1['response']}")
    print(f"对话ID: {result1['conversation_id']}")
    print(f"消息数量: {result1['message_count']}")
    
    # 第二轮对话（使用相同的对话ID继续）
    print("\n=== 第二轮对话 ===")
    
    # 创建第二个输入（包含文本和图片）
    second_input = Content()
    second_input.add_text("我之前说了什么？")
    second_input.add_text("请告诉我今天的天气怎么样？")
    
    # 添加一个实际存在的图片
    if os.path.exists("./images/test_image.jpg"):
        second_input.add_text("另外，请分析一下这张图片：")
        second_input.add_image("test_image.jpg")  # 这里会通过 utils.load_image 加载图片
        print("✓ 图片文件已找到，将包含在对话中")
    else:
        second_input.add_text("（没有找到测试图片文件）")
    
    # 发送第二轮消息（使用相同的 conversation_id）
    result2 = await graph.chat(
        conversation_id=result1['conversation_id'],
        content=second_input,
        is_final=True  # 标记为最终，会自动保存对话到文件
    )
    
    print(f"用户: {second_input.to_display_text()}")
    print(f"助手: {result2['response']}")
    print(f"对话ID: {result2['conversation_id']}")
    print(f"消息数量: {result2['message_count']}")
    
    print("\n=== 对话结束 ===")
    print(f"完整对话已自动保存到文件")
    
    # 显示消息转换结果（用于调试）
    print("\n=== 调试信息：消息转换结果 ===")
    converted_messages = graph.llm.convert_messages(
        graph.conversation_manager.get_conversation_history(result2['conversation_id']),
        second_input
    )
    print(f"转换后的消息格式: {converted_messages}")


if __name__ == "__main__":
    # 运行测试
    try:
        asyncio.run(test_two_round_conversation())
    except Exception as e:
        print(f"测试出错: {e}")
        print("请检查配置和网络连接")
