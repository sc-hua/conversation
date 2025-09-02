"""LLM模块 - 提供统一的语言模型接口和工厂函数"""

import os
from .base import BaseLLM
from .mock import MockLLM
from .ollama import OllamaLLM
from .openai import OpenAILLM

__all__ = ['BaseLLM', 'MockLLM', 'OllamaLLM', 'OpenAILLM', 'create_llm']


def create_llm(provider: str = None, **kwargs) -> BaseLLM:
    """创建LLM实例，默认从环境变量LLM_NAME读取"""
    provider = provider or os.getenv('LLM_NAME', 'mock').lower()
    
    if provider == "mock":
        return MockLLM(**kwargs)
    elif provider == "ollama":
        return OllamaLLM(**kwargs)
    elif provider in ("openai", "oai"):
        return OpenAILLM(**kwargs)
    else:
        raise ValueError(f"不支持的LLM提供商: {provider}")
