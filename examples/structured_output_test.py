#!/usr/bin/env python3
"""
测试结构化输出功能的简单示例
"""

import asyncio
import os
from typing import List, Literal
from pydantic import BaseModel, Field

# 加载环境变量
from dotenv import load_dotenv
load_dotenv()

from conversation.core import Content, ConversationGraph


# 定义结构化输出模型
class Event(BaseModel):
    event: str = Field(..., description="事件代码，需要为英文，可以有下划线")
    level: Literal["critical", "caution", "suggestion"] = Field(..., description="事件类型")
    analyze: str = Field(..., max_length=50, description="50字以内中文分析事件")
    message: str = Field(..., max_length=15, description="15字以内中文描述, 提示")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度，0.0-1.0")


class Notice(BaseModel):
    notice: str = Field(..., max_length=15, description="15字以内中文描述, 提示")
    priority: float = Field(..., ge=0.0, le=1.0, description="数值越大优先级越高")


class Caption(BaseModel):
    events: List[Event] = Field(..., description="事件列表")
    notices: List[Notice] = Field(..., description="通知列表")


async def test_structured_output():
    """测试结构化输出功能"""
    
    # 检查OpenAI配置
    if not os.getenv('OPENAI_API_KEY'):
        print("❌ 请设置 OPENAI_API_KEY 环境变量")
        return
    
    print("🚀 开始测试结构化输出功能...")
    
    # 创建对话图实例
    graph = ConversationGraph(llm='openai')
    
    # 创建输入内容
    content = Content("随意生成一些事件和通知，要求事件有3个，通知有2个。")
    
    try:
        # 测试普通输出（不使用结构化格式）
        print("\n📝 测试1: 普通文本输出")
        result1 = await graph.chat(
            content=content,
            system_prompt="你是一个助手。"
        )
        print(f"普通输出: {result1['response']}")
        
        # 测试结构化输出
        print("\n🔧 测试2: 结构化JSON输出")
        result2 = await graph.chat(
            content=content,
            system_prompt="你是一个助手。",
            response_format=Caption  # 使用Pydantic模型限制输出格式
        )
        print(f"结构化输出: {result2['response']}")
        
        # 验证JSON格式
        import json
        try:
            parsed = json.loads(result2['response'])
            print("✅ JSON格式验证通过")
            
            # 验证Pydantic模型
            caption = Caption(**parsed)
            print(f"✅ Pydantic模型验证通过")
            print(f"   - 事件数量: {len(caption.events)}")
            print(f"   - 通知数量: {len(caption.notices)}")
            
        except Exception as e:
            print(f"❌ 格式验证失败: {e}")
    
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        
    finally:
        # 清理
        if 'result1' in locals():
            await graph.end(result1['conv_id'], save=False)
        if 'result2' in locals():
            await graph.end(result2['conv_id'], save=False)


async def test_mock_structured_output():
    """使用Mock LLM测试结构化输出接口兼容性"""
    print("\n🧪 测试Mock LLM的结构化输出接口兼容性...")
    
    graph = ConversationGraph(llm='mock')
    content = Content("测试Mock LLM")
    
    try:
        result = await graph.chat(
            content=content,
            response_format=Caption  # Mock LLM应该忽略这个参数
        )
        print(f"✅ Mock LLM兼容性测试通过: {result['response']}")
        await graph.end(result['conv_id'], save=False)
        
    except Exception as e:
        print(f"❌ Mock LLM测试失败: {e}")


if __name__ == "__main__":
    async def run_tests():
        await test_structured_output()
        await test_mock_structured_output()
    
    try:
        asyncio.run(run_tests())
        print("\n🎉 测试完成！")
    except Exception as e:
        print(f"❌ 测试出错: {e}")
