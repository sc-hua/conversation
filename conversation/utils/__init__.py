"""工具函数模块包"""

from .image_utils import load_image, resolve_image_path
from .export_tools import MultimodalExporter
from .logging import get_logger, log_exception

def shortcut_id(full_id: str, length: int = 8) -> str:
    """截断ID到指定长度"""
    if not full_id:
        return ""
    return full_id[:length]

__all__ = [
    'load_image',
    'resolve_image_path', 
    'MultimodalExporter',
    'get_logger',
    'log_exception',
    'shortcut_id',
]
