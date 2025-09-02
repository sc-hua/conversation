"""核心模块包"""

from .modules import Content, Message, ConversationState, History
from .graph import ConversationGraph
from .manager import HistoryManager

# alias ConvState => ConversationState
ConvState = ConversationState

# alias ConvGraph => ConversationGraph
ConvGraph = ConversationGraph

__all__ = [
    'Content',
    'Message',
    'ConversationState',
    'History',
    'ConversationGraph',
    'HistoryManager',
]
