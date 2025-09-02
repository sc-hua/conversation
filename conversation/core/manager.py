import os
import aiofiles
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from .modules import Message, History


class HistoryManager:
    """
    History Manager: 多轮对话系统的核心管理组件。

    提供对话历史的管理、持久化和导出功能。
    支持内存存储和文件持久化的混合模式。
    
    参数:
        save_path: 保存目录
    属性:
        history_map: 内存对话存储
        save_path: 文件保存目录
    """

    def __init__(self, save_path: str = None):
        save_path = save_path or os.getenv("HISTORY_SAVE_PATH")
        self.history_map: Dict[str, History] = {
            # conv_id：History()
            # ...
        }
        self.save_path = Path(save_path)
        self.save_path.mkdir(exist_ok=True)

    def save_msg(self, conv_id: str, msg: Message) -> None:
        """保存单条消息到内存。"""
        if conv_id not in self.history_map:
            self.history_map[conv_id] = History(conv_id=conv_id)
            self.history_map[conv_id].created_at = datetime.now()
        self.history_map[conv_id].messages.append(msg)
        self.history_map[conv_id].updated_at = datetime.now()

    def get_history_msgs(self, conv_id: str) -> List[Message]:
        """根据对话 ID 获取对话历史。"""
        return self.history_map.get(conv_id, History()).messages

    async def save_conversation_to_file(self, conv_id: str) -> str:
        """持久化对话到 JSON 文件。"""
        if conv_id not in self.history_map:
            raise ValueError(f"No conversation found with ID: {conv_id}")
        
        # save_path
        now_datetime_str = datetime.now().strftime('%Y%m%d-%H%M%S')
        filename = f"{now_datetime_str}_{conv_id}.json"
        filepath = self.save_path / filename
        
        history = self.history_map[conv_id]
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(history.model_dump_json(indent=2, exclude_none=True))
        return str(filepath)

    def cleanup_memory(self, conv_id: str) -> None:
        """清理内存中的对话。"""
        if conv_id in self.history_map:
            del self.history_map[conv_id]
