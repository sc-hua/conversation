"""
对话管理器，支持结构化内容。

本模块处理 LangGraph 对话系统的对话持久化、历史管理和文件存储。
"""

import json
import os
import aiofiles
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from dotenv import load_dotenv
from modules import Message, StructuredMessageContent

load_dotenv()


class ConversationManager:
    """
    对话历史管理，支持结构化内容。
    参数:
        save_path: 保存目录
    属性:
        conversations: 内存对话存储
        save_path: 文件保存目录
    """

    def __init__(self, save_path: str = None):
        save_path = save_path or os.getenv("CONVERSATION_SAVE_PATH")
        self.conversations: Dict[str, List[Message]] = {}
        self.save_path = Path(save_path)
        self.save_path.mkdir(exist_ok=True)

    def save_message(self, conversation_id: str, message: Message) -> None:
        """
        保存单条消息到内存。
        conversation_id: 对话 ID
        message: Message
        """
        if conversation_id not in self.conversations:
            self.conversations[conversation_id] = []
        self.conversations[conversation_id].append(message)

    def get_conversation_history(self, conversation_id: str) -> List[Message]:
        """
        根据对话 ID 获取对话历史。
        conversation_id: 对话 ID
        返回: List[Message]
        """
        return self.conversations.get(conversation_id, [])

    async def save_conversation_to_file(self, conversation_id: str) -> str:
        """
        持久化对话到 JSON 文件。
        conversation_id: 对话 ID
        返回: 文件路径
        """
        messages = self.conversations.get(conversation_id, [])
        if not messages:
            return ""
        conversation_data = {
            "conversation_id": conversation_id,
            "created_at": messages[0].timestamp.isoformat(),
            "updated_at": datetime.now().isoformat(),
            "messages": []
        }
        for msg in messages:
            msg_data = {
                "id": msg.id,
                "role": msg.role,
                "timestamp": msg.timestamp.isoformat()
            }
            if isinstance(msg.content, StructuredMessageContent):
                msg_data["content"] = {
                    "type": "structured",
                    "blocks": [
                        {
                            "type": block.type,
                            "content": block.content,
                            **({"extras": block.extras} if block.extras else {})  # 保存自定义字段
                        }
                        for block in msg.content.blocks
                    ]
                }
            else:
                msg_data["content"] = str(msg.content)
            conversation_data["messages"].append(msg_data)
        filename = f"{conversation_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = self.save_path / filename
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(conversation_data, indent=2, ensure_ascii=False))
        return str(filepath)

    def cleanup_memory(self, conversation_id: str) -> None:
        """
        清理内存中的对话。
        conversation_id: 对话 ID
        """
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
