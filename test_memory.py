#!/usr/bin/env python3
"""
模型历史记忆能力检验脚本

测试模型是否能够正确记住和引用之前的对话内容，
验证对话历史是否正确传递给模型。
"""

import asyncio
import os
from dotenv import load_dotenv
from conversation_graph import ConversationGraph
from models import StructuredMessageContent

load_dotenv()


async def test_memory_capability():
    """测试模型的历史记忆能力"""
    print("🧠 模型历史记忆能力测试")
    print("=" * 50)
    
    graph = ConversationGraph()
    
    # 测试1: 基础信息记忆
    print("\n📝 测试1: 基础信息记忆")
    
    # 第一轮：提供基础信息
    content1 = StructuredMessageContent()
    content1.add_text("我的名字叫张三，我今年25岁，是一名软件工程师。请记住这些信息。")
    
    result1 = await graph.chat(
        system_prompt="你是一个有记忆能力的AI助手，请记住用户告诉你的信息。",
        structured_content=content1
    )
    
    print(f"💬 用户: {result1['input_preview']}")
    print(f"🤖 助手: {result1['response'][:100]}...")
    
    # 第二轮：测试是否记住了名字
    content2 = StructuredMessageContent()
    content2.add_text("我的名字是什么？")
    
    result2 = await graph.chat(
        conversation_id=result1['conversation_id'],
        structured_content=content2
    )
    
    print(f"💬 用户: {result2['input_preview']}")
    print(f"🤖 助手: {result2['response']}")
    
    # 分析结果
    memory_test1 = "张三" in result2['response'] or "25" in result2['response']
    print(f"✅ 姓名记忆测试: {'通过' if memory_test1 else '失败'}")
    
    # 测试2: 复杂上下文记忆
    print("\n📊 测试2: 复杂数据记忆")
    
    # 第三轮：提供复杂数据
    content3 = StructuredMessageContent()
    content3.add_text("以下是我的项目数据：", position=0)
    content3.add_json({
        "project_name": "智能对话系统",
        "completion": 75,
        "team_size": 5,
        "deadline": "2024年12月"
    }, position=1)
    content3.add_text("请分析这个项目的状态。", position=2)
    
    result3 = await graph.chat(
        conversation_id=result1['conversation_id'],
        structured_content=content3
    )
    
    print(f"💬 用户: {result3['input_preview'][:80]}...")
    print(f"🤖 助手: {result3['response'][:100]}...")
    
    # 第四轮：测试是否记住了项目信息和个人信息
    content4 = StructuredMessageContent()
    content4.add_text("根据我之前提到的个人信息和项目数据，你觉得我能按时完成这个项目吗？")
    
    result4 = await graph.chat(
        conversation_id=result1['conversation_id'],
        structured_content=content4
    )
    
    print(f"💬 用户: {result4['input_preview']}")
    print(f"🤖 助手: {result4['response']}")
    
    # 分析综合记忆能力
    has_personal_info = any(keyword in result4['response'] for keyword in ["张三", "25", "软件工程师"])
    has_project_info = any(keyword in result4['response'] for keyword in ["智能对话", "75", "5"])
    
    print(f"✅ 个人信息记忆: {'通过' if has_personal_info else '失败'}")
    print(f"✅ 项目信息记忆: {'通过' if has_project_info else '失败'}")
    
    # 测试3: 多模态内容记忆
    print("\n🎯 测试3: 多模态内容记忆")
    
    # 第五轮：多模态输入
    content5 = StructuredMessageContent()
    content5.add_text("我刚刚拍了一张我的工作桌照片", position=0)
    content5.add_image("workspace_photo.jpg", position=1)
    content5.add_text("桌子上有我的笔记本电脑和咖啡杯", position=2)
    
    result5 = await graph.chat(
        conversation_id=result1['conversation_id'],
        structured_content=content5
    )
    
    print(f"💬 用户: {result5['input_preview'][:80]}...")
    print(f"🤖 助手: {result5['response'][:100]}...")
    
    # 第六轮：测试多模态记忆
    content6 = StructuredMessageContent()
    content6.add_text("刚才我给你看的照片里有什么？结合我的个人信息，你觉得这个工作环境适合我吗？")
    
    result6 = await graph.chat(
        conversation_id=result1['conversation_id'],
        structured_content=content6,
        is_final=True
    )
    
    print(f"💬 用户: {result6['input_preview']}")
    print(f"🤖 助手: {result6['response']}")
    
    # 最终分析
    has_multimodal_memory = any(keyword in result6['response'] for keyword in ["照片", "图片", "桌子", "笔记本", "咖啡"])
    
    print(f"✅ 多模态内容记忆: {'通过' if has_multimodal_memory else '失败'}")
    
    # 总结
    print(f"\n📈 测试总结:")
    print(f"   对话ID: {result1['conversation_id']}")
    print(f"   总消息数: {result6['message_count']}")
    print(f"   基础记忆: {'✅' if memory_test1 else '❌'}")
    print(f"   综合记忆: {'✅' if (has_personal_info and has_project_info) else '❌'}")
    print(f"   多模态记忆: {'✅' if has_multimodal_memory else '❌'}")
    
    # 评分
    total_tests = 4  # 基础记忆 + 个人信息 + 项目信息 + 多模态
    passed_tests = sum([memory_test1, has_personal_info, has_project_info, has_multimodal_memory])
    score = (passed_tests / total_tests) * 100
    
    print(f"   记忆能力评分: {score:.0f}%")
    
    return result1['conversation_id'], score


async def main():
    """运行记忆能力测试"""
    current_llm = os.getenv('LLM_TYPE', 'mock')
    print(f"当前LLM配置: {current_llm.upper()}")
    
    if current_llm == 'ollama':
        model = os.getenv('OLLAMA_MODEL', 'qwen2.5vl:3b')
        print(f"使用模型: {model}")
    
    try:
        conversation_id, score = await test_memory_capability()
        
        if score >= 75:
            print(f"🎉 模型记忆能力良好！")
        elif score >= 50:
            print(f"⚠️ 模型记忆能力一般，建议检查历史传递逻辑")
        else:
            print(f"❌ 模型记忆能力较差，可能存在历史丢失问题")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
