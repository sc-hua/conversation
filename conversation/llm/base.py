"""LLM抽象基类定义"""

from abc import ABC, abstractmethod
from typing import List, Dict
from ..core.modules import Message, Content


class BaseLLM(ABC):
    """LLM抽象基类，定义标准接口"""
    
    @abstractmethod
    def convert_messages(self, messages: List[Message], current_input: Content) -> List[Dict]:
        """将消息历史转换为特定LLM格式"""
        pass
    
    @abstractmethod
    async def generate_response(self, messages: List[Message], current_input: Content) -> str:
        """生成回复文本"""
        pass