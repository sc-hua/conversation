"""
增强对话管理器，支持结构化内容。

本模块处理LangGraph对话系统的对话持久化、
历史管理和文件存储。
"""

import json
import aiofiles
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from models import Message, StructuredMessageContent


class ConversationManager:
    """
    管理对话历史和持久化，支持结构化内容。
    
    处理内存中的对话存储和永久文件持久化，
    完全支持结构化内容序列化。
    
    属性:
        conversations: 内存中的对话存储
        save_path: 保存对话文件的目录
    """
    
    def __init__(self, save_path: str = "./conversations"):
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
        将单条消息保存到内存存储。
        
        参数:
            conversation_id: 对话的ID
            message: 要保存的消息
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        self.conversations[conversation_id].append(message)
    
    def get_conversation_history(self, conversation_id: str) -> List[Message]:
        """
        从内存中检索对话历史。
        
        参数:
            conversation_id: 对话的ID
            
        返回:
            按时间顺序排列的消息列表
        """
        return self.conversations.get(conversation_id, [])
    
    async def save_conversation_to_file(self, conversation_id: str) -> str:
        """
        将完整对话持久化到JSON文件。
        
        将结构化内容转换为可序列化格式，并将
        完整对话及元数据保存到带时间戳的文件中。
        
        参数:
            conversation_id: 要保存的对话ID
            
        返回:
            保存文件的路径
        """
        messages = self.conversations.get(conversation_id, [])
        if not messages:
            return ""
        
        # Create conversation history object
        conversation_data = {
            "conversation_id": conversation_id,
            "created_at": messages[0].timestamp.isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": []
        }
        
        # Serialize messages with structured content support
        for msg in messages:
            msg_data = {
                "id": msg.id,
                "role": msg.role,
                "timestamp": msg.timestamp.isoformat()
            }
            
            # Handle different content types
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
        
        # Save to file with timestamp
        filename = f"{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.save_path / filename
        
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(conversation_data, indent=2, ensure_ascii=False))
        
        return str(filepath)
    
    def cleanup_memory(self, conversation_id: str) -> None:
        """
        Clean up in-memory storage for a conversation.
        
        Args:
            conversation_id: ID of the conversation to clean up
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
