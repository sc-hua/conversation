#!/usr/bin/env python3
"""
最简单的结构化输出功能验证脚本
"""

import asyncio
import os
from pydantic import BaseModel, Field

# 快速导入
try:
    from conversation.core import Content, ConversationGraph
    print("✅ 导入成功")
except ImportError as e:
    print(f"❌ 导入失败: {e}")
    exit(1)


# 简单的输出模型
class SimpleResponse(BaseModel):
    message: str = Field(..., description="简单的回复消息")
    confidence: float = Field(..., ge=0.0, le=1.0, description="置信度")


async def quick_test():
    """快速验证结构化输出功能"""
    print("🔧 快速测试结构化输出...")
    
    # 创建图实例 - 优先使用mock以避免API依赖
    graph = ConversationGraph(llm='mock')
    content = Content("你好")
    
    try:
        # 测试带结构化格式的调用
        result = await graph.chat(
            content=content,
            response_format=SimpleResponse
        )
        print(f"✅ 调用成功: {result['response']}")
        await graph.end(result['conv_id'], save=False)
        
        print("🎉 基本功能验证通过！")
        
    except TypeError as e:
        if "unexpected keyword argument" in str(e):
            print(f"❌ 接口不兼容: {e}")
        else:
            print(f"❌ 类型错误: {e}")
    except Exception as e:
        print(f"❌ 其他错误: {e}")


if __name__ == "__main__":
    asyncio.run(quick_test())
