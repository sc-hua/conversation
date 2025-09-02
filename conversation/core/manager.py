import os
import aiofiles
from pathlib import Path
from typing import Dict, List
from datetime import datetime
from .modules import Message, History
from ..utils import get_logger, log_exception, shortcut_id


class HistoryManager:
    """
    History Manager: 多轮对话系统的核心管理组件。

    提供对话历史的管理、持久化和导出功能。
    支持内存存储和文件持久化的混合模式。
    
    参数:
        save_path: 保存目录
    属性:
        _map: 内存对话存储 (Dict[str, History])
        save_path: 文件保存目录 (Path)
        logger: 日志记录器
    """

    def __init__(self, save_path: str = None):
        # 内存对话存储：conv_id -> History
        self._map: Dict[str, History] = {
            # conv_id：History()        
        }
        save_path = save_path or os.getenv("HISTORY_SAVE_PATH")
        self.save_path = Path(save_path)
        self.save_path.mkdir(parents=True, exist_ok=True)

        # 初始化日志器
        self.logger = get_logger("manager")

    def exists(self, conv_id: str) -> bool:
        return conv_id in self._map
    
    @log_exception
    def save_msg(self, conv_id: str, msg: Message) -> None:
        """保存单条消息到内存。"""
        if conv_id not in self._map:
            self._map[conv_id] = History(conv_id=conv_id)
            self._map[conv_id].created_at = datetime.now()
            self.logger.debug(f"创建新对话 | conv_id={shortcut_id(conv_id)}")
        self._map[conv_id].messages.append(msg)
        self._map[conv_id].updated_at = datetime.now()
        self.logger.debug(f"保存消息 | conv_id={shortcut_id(conv_id)} | role={msg.role}")

    def get_msgs(self, conv_id: str) -> List[Message]:
        return self._map.get(conv_id, History()).messages

    @log_exception
    async def save_conversation_to_file(self, conv_id: str) -> str:
        """持久化对话到 JSON 文件。"""
        if conv_id not in self._map:
            raise ValueError(f"No conversation found with ID: {conv_id}")
        
        # save_path
        filepath = self.save_path / f"{conv_id}.json"
        
        history = self._map[conv_id]
        async with aiofiles.open(filepath, 'w', encoding='utf-8') as f:
            await f.write(history.model_dump_json(indent=2, exclude_none=True))
        
        self.logger.info(f"对话保存成功 | conv_id={shortcut_id(conv_id)} | messages={len(history.messages)}")
        return str(filepath)

    def cleanup_memory(self, conv_id: str) -> None:
        """清理内存中的对话。"""
        if conv_id in self._map:
            del self._map[conv_id]
            self.logger.debug(f"清理内存 | conv_id={shortcut_id(conv_id)}")
