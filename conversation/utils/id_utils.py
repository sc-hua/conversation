"""ID生成和处理工具函数"""

import uuid


def shortcut_id(full_id: str, length: int = 8) -> str:
    """截断ID到指定长度"""
    if not full_id:
        return ""
    return full_id[:length]


def new_id() -> str:
    """生成新的对话ID"""
    return str(uuid.uuid4())
