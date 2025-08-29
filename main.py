"""
无外部依赖的独立增强对话系统。

本模块为测试和演示目的提供增强对话系统的
完整独立实现。
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from pathlib import Path
import uuid


@dataclass
class ContentBlock:
    """
    带位置控制的单个内容块。
    
    表示可以在消息中特定位置
    定位的独立内容片段。
    
    属性:
        type: 内容类型 - "text"、"image" 或 "json"
        content: 实际内容数据
        position: 排序的位置索引
    """
    type: str
    content: Any
    position: int = 0


@dataclass
class StructuredMessageContent:
    """
    Message content with precise positioning control.
    
    Allows creating complex messages where different content types
    can be interleaved in any order by specifying exact positions.
    
    Attributes:
        blocks: List of content blocks ordered by position
    """
    blocks: List[ContentBlock] = field(default_factory=list)
    
    def add_text(self, text: str, position: int = None) -> 'StructuredMessageContent':
        """
        在指定位置添加文本块。
        
        参数:
            text: 要添加的文本内容
            position: 位置索引（如果为None则自动分配）
            
        返回:
            支持方法链式调用的自身
        """
        pos = position if position is not None else len(self.blocks)
        self.blocks.append(ContentBlock(type="text", content=text, position=pos))
        self._sort_blocks()
        return self
    
    def add_image(self, image_url: str, position: int = None) -> 'StructuredMessageContent':
        """
        在指定位置添加图片块。
        
        参数:
            image_url: 图片URL或base64数据
            position: 位置索引（如果为None则自动分配）
            
        返回:
            支持方法链式调用的自身
        """
        pos = position if position is not None else len(self.blocks)
        self.blocks.append(ContentBlock(type="image", content=image_url, position=pos))
        self._sort_blocks()
        return self
    
    def add_json(self, json_data: Dict[str, Any], position: int = None) -> 'StructuredMessageContent':
        """
        在指定位置添加JSON块。
        
        参数:
            json_data: 要添加的JSON/字典数据
            position: 位置索引（如果为None则自动分配）
            
        返回:
            支持方法链式调用的自身
        """
        pos = position if position is not None else len(self.blocks)
        self.blocks.append(ContentBlock(type="json", content=json_data, position=pos))
        self._sort_blocks()
        return self
    
    def _sort_blocks(self) -> None:
        """按位置索引排序块。"""
        self.blocks.sort(key=lambda x: x.position)
    
    def to_display_text(self) -> str:
        """
        转换为人类可读的文本表示。
        
        返回:
            显示所有内容块的格式化字符串
        """
        parts = []
        for block in self.blocks:
            if block.type == "text":
                parts.append(block.content)
            elif block.type == "image":
                parts.append(f"[Image: {block.content}]")
            elif block.type == "json":
                parts.append(f"[JSON: {json.dumps(block.content, ensure_ascii=False)}]")
        return " ".join(parts)


@dataclass
class Message:
    """
    对话中的单条消息。

    表示一次对话交换，支持简单文本或结构化内容。

    属性:
        role: 消息角色（system、user、assistant）
        content: 消息内容（文本或结构化）
        id: 唯一消息 ID
        timestamp: 创建时间戳
    """
    role: str
    content: Union[str, StructuredMessageContent] = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)


class StandaloneConversationManager:
    """
    轻量级对话管理器，无外部依赖。

    使用 Python 标准库处理对话存储和文件持久化。

    属性:
        conversations: 内存中的对话存储
        save_path: 保存对话文件的目录
    """
    
    def __init__(self, save_path: str = "./conv_logs"):
        """
        初始化对话管理器。

        参数:
            save_path: 保存对话文件的目录路径
        """
        self.conversations: Dict[str, List[Message]] = {}
        self.save_path = Path(save_path)
        self.save_path.mkdir(exist_ok=True)
    
    def save_message(self, conversation_id: str, message: Message) -> None:
        """
        将单条消息保存到内存存储中。

        参数:
            conversation_id: 对话 ID
            message: 要保存的消息对象
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        self.conversations[conversation_id].append(message)
    
    def get_conversation_history(self, conversation_id: str) -> List[Message]:
        """
        从内存中检索对话历史。

        参数:
            conversation_id: 对话 ID

        返回:
            按时间顺序排列的消息列表
        """
        return self.conversations.get(conversation_id, [])
    
    def save_conversation_to_file(self, conversation_id: str) -> str:
        """
        将完整对话持久化为 JSON 文件。

        参数:
            conversation_id: 要保存的对话 ID

        返回:
            保存文件的路径
        """
        messages = self.conversations.get(conversation_id, [])
        if not messages:
            return ""
        
        # 创建可序列化的对话数据
        conversation_data = {
            "conversation_id": conversation_id,
            "created_at": messages[0].timestamp.isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": []
        }
        
        # 序列化消息，支持结构化内容
        for msg in messages:
            msg_data = {
                "id": msg.id,
                "role": msg.role,
                "timestamp": msg.timestamp.isoformat()
            }
            
            # 处理不同的内容类型
            if isinstance(msg.content, StructuredMessageContent):
                msg_data["content"] = {
                    "type": "structured",
                    "blocks": [
                        {
                            "type": block.type,
                            "content": block.content,
                            "position": block.position
                        }
                        for block in msg.content.blocks
                    ]
                }
            else:
                msg_data["content"] = str(msg.content)
            
            conversation_data["messages"].append(msg_data)
        
        # 保存到带时间戳的文件
        filename = f"{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.save_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(conversation_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Conversation saved to: {filepath}")
        return str(filepath)


class MockLLM:
    """
    Mock 语言模型，用于无 API 依赖的测试。

    模拟带有结构化内容位置感知的智能响应生成。
    """
    
    async def generate_response(self, messages: List[Message], 
                              current_input: StructuredMessageContent) -> str:
        """
        基于结构化输入生成模拟响应。

        参数:
            messages: 之前的对话消息
            current_input: 当前要处理的结构化输入

        返回:
            包含位置感知信息的生成响应文本
        """
        await asyncio.sleep(0.1)  # 模拟处理时间

        responses = ["I analyzed your content in the specified order:"]

        # 处理每个内容块
        for block in current_input.blocks:
            position_text = f"Position {block.position}"

            if block.type == "text":
                responses.append(f"{position_text}: Text - {block.content}")
            elif block.type == "image":
                responses.append(f"{position_text}: Image - {block.content}")
            elif block.type == "json":
                key_count = len(block.content) if isinstance(block.content, dict) else 0
                responses.append(f"{position_text}: JSON with {key_count} fields")

        # 添加对话上下文
        user_messages = [msg for msg in messages if msg.role == "user"]
        if len(user_messages) > 0:
            responses.append(f"This is interaction #{len(user_messages) + 1}.")

        return " ".join(responses)


class StandaloneConversationGraph:
    """
    独立的对话图实现。

    提供完整的对话处理流程，无外部依赖，适合测试和轻量部署。

    属性:
        llm: 用于生成响应的 Mock 语言模型
        conversation_manager: 负责对话持久化
        semaphore: 控制并发处理
    """
    
    def __init__(self, max_concurrent: int = 5):
        """
        初始化对话图。

        参数:
            max_concurrent: 最大并发对话数
        """
        self.llm = MockLLM()
        self.conversation_manager = StandaloneConversationManager()
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def chat(self,
                   conversation_id: Optional[str] = None,
                   system_prompt: Optional[str] = None,
                   structured_content: Optional[StructuredMessageContent] = None,
                   is_final: bool = False) -> Dict[str, Any]:
        """
        主聊天接口，支持结构化内容。

        参数:
            conversation_id: 现有对话 ID 或 None 表示新对话
            system_prompt: AI 行为的系统提示词
            structured_content: 带位置信息的结构化输入
            is_final: 是否将完整对话保存到文件

        返回:
            包含 conversation_id、response、message_count、input_preview 的字典
        """
        async with self.semaphore:  # 控制并发
            # Generate conversation ID if not provided
            conv_id = conversation_id or str(uuid.uuid4())
            
            # 加载现有对话历史
            messages = self.conversation_manager.get_conversation_history(conv_id)
            
            # 如果是第一条消息则添加系统提示
            if not messages and system_prompt:
                system_msg = Message(role="system", content=system_prompt)
                messages.append(system_msg)
                self.conversation_manager.save_message(conv_id, system_msg)
            
            # 如果存在输入则生成响应
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
            
            # 如果是最终对话则保存
            if is_final:
                self.conversation_manager.save_conversation_to_file(conv_id)
            
            return {
                "conversation_id": conv_id,
                "response": response,
                "message_count": len(messages),
                "input_preview": (structured_content.to_display_text() 
                                if structured_content else None)
            }


async def comprehensive_demo():
    """
    Comprehensive demonstration of all features.
    
    Shows structured content positioning, conversation flow,
    and various usage patterns.
    """
    print("🚀 Standalone Conversation System Demo")
    print("=" * 60)
    
    graph = StandaloneConversationGraph()
    
    # Demo 1: Complex structured content
    print("\n1️⃣ Complex Structured Content:")
    content1 = (StructuredMessageContent()
                .add_text("Data Analysis Report", 0)
                .add_text("Executive Summary:", 1)
                .add_json({"status": "completed", "score": 95}, 2)
                .add_text("Detailed visualization:", 3)
                .add_image("analysis_chart.png", 4)
                .add_text("Recommendations:", 5)
                .add_json({"actions": ["optimize", "scale", "monitor"]}, 6))
    
    result1 = await graph.chat(
        system_prompt="You are a data analysis expert.",
        structured_content=content1
    )
    
    print(f"Input: {result1['input_preview']}")
    print(f"Response: {result1['response']}\n")
    
    # Demo 2: Non-sequential positioning
    print("2️⃣ Non-sequential Positioning:")
    content2 = StructuredMessageContent()
    content2.add_text("Conclusion will be here", 100)  # Last
    content2.add_image("intro_image.jpg", 0)           # First
    content2.add_text("Middle explanation", 50)        # Middle
    content2.add_json({"early_data": True}, 10)        # Early
    
    result2 = await graph.chat(
        conversation_id=result1['conversation_id'],
        structured_content=content2
    )
    
    print(f"Input: {result2['input_preview']}")
    print(f"Response: {result2['response']}\n")
    
    # Demo 3: Final conversation with save
    print("3️⃣ Final Message with Save:")
    content3 = (StructuredMessageContent()
                .add_text("Thank you for the analysis!", 0)
                .add_text("Summary image:", 1)
                .add_image("summary_dashboard.png", 2))
    
    result3 = await graph.chat(
        conversation_id=result1['conversation_id'],
        structured_content=content3,
        is_final=True
    )
    
    print(f"Input: {result3['input_preview']}")
    print(f"Response: {result3['response']}")
    print(f"Total messages: {result3['message_count']}")
    
    # Demo 4: Concurrent processing
    print("\n4️⃣ Concurrent Processing Test:")
    tasks = []
    for i in range(3):
        content = (StructuredMessageContent()
                  .add_text(f"Task {i+1}", 0)
                  .add_json({"task_id": i+1}, 1))
        
        task = graph.chat(structured_content=content)
        tasks.append(task)
    
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    end_time = asyncio.get_event_loop().time()
    
    print(f"✅ Processed {len(results)} conversations in {end_time - start_time:.2f}s")
    print("\n🎉 All demos completed successfully!")


if __name__ == "__main__":
    asyncio.run(comprehensive_demo())
