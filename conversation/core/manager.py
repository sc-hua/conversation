import os
import aiofiles
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from .modules import Message, History
from ..utils.logging import get_logger, log_exception, warn_once
from ..utils.id_utils import shortcut_id


class HistoryManager:
    """
    History Manager: 多轮对话系统的核心管理组件。

    提供对话历史的管理、持久化和导出功能。
    支持内存存储和文件持久化的混合模式。
    
    参数:
        save_dir: 保存目录
    属性:
        _map: 内存对话存储 (Dict[str, History])
        save_dir: 文件保存目录 (Path)
        logger: 日志记录器
    """

    def __init__(self, save_dir: str = None):
        self.logger = get_logger("manager")
        self._map: Dict[str, History] = {}
        
        self.save_dir = save_dir or os.getenv("HISTORY_SAVE_DIR", "./log/conv_log/draft")
        self._resolve_save_dir()
    
    def _resolve_save_dir(self):
        self.save_dir = Path(self.save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
        if os.getenv("HISTORY_SAVE_DIR", None) is None:
            warn_once(f"[HistoryManager] | no save_dir or HISTORY_SAVE_DIR env var set, using: {self.save_dir.absolute()}")

    def exists(self, conv_id: str) -> bool:
        return conv_id in self._map
    
    def get_msgs(self, conv_id: str) -> List[Message]:
        if self.exists(conv_id):
            return self._map[conv_id].messages
        return []

    def get_length(self, conv_id: str) -> int:
        """获取对话的消息数量。如果对话不存在，返回 -1 """
        if self.exists(conv_id):
            return len(self.get_msgs(conv_id))
        return -1

    def to_json(self, conv_id: str) -> str:
        """将对话转换为 JSON 字符串。如果对话不存在，返回空字符串。"""
        if self.exists(conv_id):
            return self._map[conv_id].model_dump_json(indent=2, exclude_none=True)
        return ""

    @log_exception
    def save_msg(self, conv_id: str, msg: Message) -> None:
        """保存单条消息到内存。"""
        if conv_id not in self._map:
            self._map[conv_id] = History(conv_id=conv_id)
            self._map[conv_id].created_at = datetime.now()
            self.logger.debug(f"[Create new conversation] | conv_id = {shortcut_id(conv_id)}")
        self._map[conv_id].messages.append(msg)
        self._map[conv_id].updated_at = datetime.now()
        self.logger.debug(f"[Save message] | conv_id = {shortcut_id(conv_id)} | role = {msg.role}")

    @log_exception
    async def save_conversation_to_file(self, conv_id: str) -> str:
        """持久化对话到 JSON 文件。"""
        if not self.exists(conv_id):
            raise ValueError(f"No conversation found with ID: {conv_id}")
        
        filepath = self.save_dir / f"{conv_id}.json"
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            data = self._map[conv_id].model_dump_json(indent=2, exclude_none=True)
            await f.write(data)

        self.logger.info(f"[Conversation saved] | conv_id = {shortcut_id(conv_id)} | messages = {self.get_length(conv_id)}")
        return str(filepath)

    def cleanup_memory(self, conv_id: str) -> None:
        """清理内存中的对话。"""
        if conv_id in self._map:
            del self._map[conv_id]
            self.logger.debug(f"[Cleanup memory] | conv_id = {shortcut_id(conv_id)}")
