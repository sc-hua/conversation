"""对话系统核心包"""
from .core import Content, ConvGraph
from .llm import create_llm

__all__ = [
    'Content',
    'ConvState',  # alias for ConversationState
    'ConvGraph',  # alias for ConversationGraph
    'create_llm',
]
