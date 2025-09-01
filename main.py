"""独立版对话系统示例，使用现有模块避免重复定义。"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# 使用现有模块，避免重复定义
from models import Message, StructuredMessageContent
from conversation_manager import ConversationManager

load_dotenv()


class MockLLM:
    """模拟语言模型，用于无 API 依赖的测试。"""
    
    async def generate_response(self, messages: List[Message], 
                                current_input: StructuredMessageContent) -> str:
        """基于结构化输入生成模拟回复文本。"""
        await asyncio.sleep(0.1)  # 模拟处理延迟

        responses = ["已分析您的内容："]

        # 处理每个内容块
        for i, block in enumerate(current_input.blocks):
            block_desc = f"第{i+1}项"

            if block.type == "text":
                responses.append(f"{block_desc}: 文本 - {block.content}")
            elif block.type == "image":
                responses.append(f"{block_desc}: 图片 - {block.content}")
            elif block.type == "json":
                key_count = len(block.content) if isinstance(block.content, dict) else 0
                responses.append(f"{block_desc}: JSON 包含 {key_count} 个字段")

        # 添加对话上下文信息
        user_messages = [msg for msg in messages if msg.role == "user"]
        if len(user_messages) > 0:
            responses.append(f"这是第 {len(user_messages) + 1} 次交互。")

        return " ".join(responses)


class StandaloneConversationGraph:
    """独立对话图：处理输入、生成回复并保存历史。"""
    
    def __init__(self, max_concurrent: int = 5):
        """初始化：max_concurrent 控制并发量。"""
        self.llm = MockLLM()
        self.conversation_manager = ConversationManager()  # 使用现有的管理器
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def chat(self,
                   conversation_id: Optional[str] = None,
                   system_prompt: Optional[str] = None,
                   structured_content: Optional[StructuredMessageContent] = None,
                   is_final: bool = False
                   ) -> Dict[str, Any]:
        """主聊天接口：处理输入、调用 LLM、保存历史并返回结果字典。"""
        async with self.semaphore:  # 控制并发
            # 生成对话 ID
            conv_id = conversation_id or str(uuid.uuid4())
            
            # 获取现有对话历史
            messages = self.conversation_manager.get_conversation_history(conv_id)
            
            # 如果是第一条消息则添加系统提示
            if not messages and system_prompt:
                system_msg = Message(role="system", content=system_prompt)
                messages.append(system_msg)
                self.conversation_manager.save_message(conv_id, system_msg)
            
            # 处理用户输入并生成响应
            response = None
            if structured_content:
                response = await self.llm.generate_response(messages, structured_content)
                
                # 保存用户消息
                user_msg = Message(role="user", content=structured_content)
                messages.append(user_msg)
                self.conversation_manager.save_message(conv_id, user_msg)
                
                # 保存助手响应
                assistant_msg = Message(role="assistant", content=response)
                messages.append(assistant_msg)
                self.conversation_manager.save_message(conv_id, assistant_msg)
            
            # 如果是最终对话则保存到文件
            if is_final:
                await self.conversation_manager.save_conversation_to_file(conv_id)
            
            return {
                "conversation_id": conv_id,
                "response": response,
                "message_count": len(messages),
                "input_preview": (structured_content.to_display_text() 
                                if structured_content else None)
            }


async def comprehensive_demo():
    """
    综合功能演示。
    
    展示结构化内容定位、对话流程和各种使用模式。
    """
    print("🚀 独立对话系统演示")
    print("=" * 60)
    
    graph = StandaloneConversationGraph()
    
    # 演示 1: 复杂结构化内容
    print("\n1️⃣ 复杂结构化内容：")
    content1 = StructuredMessageContent.from_mixed_items(
        "数据分析报告",
        "执行摘要：",
        {'json': {"状态": "已完成", "得分": 95}},
        "详细可视化：",
        {'image': "analysis_chart.png"},
        "建议：",
        {'json': {"行动": ["优化", "扩展", "监控"]}}
    )
    
    result1 = await graph.chat(
        system_prompt="你是数据分析专家。",
        structured_content=content1
    )
    
    print(f"输入: {result1['input_preview']}")
    print(f"回复: {result1['response']}\n")
    
    # 演示 2: 混合内容类型
    print("2️⃣ 混合内容类型：")
    content2 = StructuredMessageContent.from_mixed_items(
        "项目开始",
        {'image': "intro_image.jpg"},
        "中间说明",
        {'json': {"项目数据": True}},
        "项目结论"
    )
    
    result2 = await graph.chat(
        conversation_id=result1['conversation_id'],
        structured_content=content2
    )
    
    print(f"输入: {result2['input_preview']}")
    print(f"回复: {result2['response']}\n")
    
    # 演示 3: 最终消息并保存
    print("3️⃣ 最终消息并保存：")
    content3 = StructuredMessageContent.from_mixed_items(
        "感谢您的分析！",
        "总结图片：",
        {'image': "summary_dashboard.png"}
    )
    
    result3 = await graph.chat(
        conversation_id=result1['conversation_id'],
        structured_content=content3,
        is_final=True
    )
    
    print(f"输入: {result3['input_preview']}")
    print(f"回复: {result3['response']}")
    print(f"总消息数: {result3['message_count']}")
    
    # 演示 4: 并发处理测试
    print("\n4️⃣ 并发处理测试：")
    tasks = []
    for i in range(3):
        content = StructuredMessageContent.from_mixed_items(
            f"任务 {i+1}",
            {'json': {"任务ID": i+1}}
        )
        
        task = graph.chat(structured_content=content)
        tasks.append(task)
    
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    end_time = asyncio.get_event_loop().time()
    
    print(f"✅ 在 {end_time - start_time:.2f}s 内处理了 {len(results)} 个对话")
    print("\n🎉 所有演示完成！")


if __name__ == "__main__":
    asyncio.run(comprehensive_demo())
