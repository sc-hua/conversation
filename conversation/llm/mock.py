"""Mock LLM实现，用于测试"""

import asyncio
from typing import List, Dict
from .base import BaseLLM
from ..core.modules import Message, Content


class MockLLM(BaseLLM):
    """
    Mock语言模型，用于在无外部依赖情况下的测试。
    模拟具有位置感知内容处理的LLM行为。
    """
    
    def convert_messages(self, messages: List[Message], 
                        current_input: Content) -> List[Dict]:
        """将历史消息与结构化输入转换为模拟格式（用于测试）"""
        mock_messages = []
        
        # 转换历史消息
        for msg in messages:
            if isinstance(msg.content, str):
                mock_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif isinstance(msg.content, Content):
                mock_messages.append({
                    "role": msg.role,
                    "content": msg.content.to_display_text()
                })
        
        # 转换当前输入
        if current_input:
            mock_messages.append({
                "role": "user",
                "content": current_input.to_display_text()
            })
        
        return mock_messages
    
    async def generate_response(self, messages: List[Message], 
                              current_input: Content) -> str:
        """基于结构化输入生成模拟回复（用于测试，无外部依赖）"""
        await asyncio.sleep(0.1)  # 模拟API延迟
        
        responses = ["我按指定顺序分析了您的内容："]
        
        # 处理每个内容块，按顺序
        for i, blk in enumerate(current_input.blocks):
            block_desc = f"第{i+1}项"

            if blk.type == "text":
                responses.append(f"{block_desc}: 文本内容 - {blk.content}")
            elif blk.type == "image":
                responses.append(f"{block_desc}: 图片文件 - {blk.content}")
            elif blk.type == "json":
                key_count = len(blk.content) if isinstance(blk.content, dict) else 0
                responses.append(f"{block_desc}: 包含 {key_count} 个字段的JSON数据")
        
        # 添加对话上下文
        user_messages = [msg for msg in messages if msg.role == "user"]
        if len(user_messages) > 0:
            responses.append(f"这是我们对话中的第 #{len(user_messages) + 1} 次交互。")
        
        return " ".join(responses)
