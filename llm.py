"""LLM 集成：提供 Mock、Ollama、OpenAI 的轻量封装。"""

import asyncio
import json
import os
from typing import Dict, List
from abc import ABC, abstractmethod
from modules import Message, StructuredMessageContent


class BaseLLM(ABC):
    """LLM 抽象基类。实现类需实现 generate_response。"""

    @abstractmethod
    async def generate_response(self, messages: List[Message], 
                              current_input: StructuredMessageContent) -> str:
        """根据消息历史和当前结构化输入返回文本回复。"""
        raise NotImplementedError()


class OllamaLLM(BaseLLM):
    """
    Ollama 语言模型集成。

    用于 Ollama API 的轻量级 HTTP 客户端，支持结构化内容和多模态输入。
    """
    
    def __init__(self, model: str = None, base_url: str = None, timeout: int = None):
        """初始化 Ollama 集成；model/base_url/timeout 可由环境变量覆盖。"""
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = model or os.getenv('OLLAMA_MODEL', 'qwen2.5vl:3b')
        self.timeout = timeout or int(os.getenv('OLLAMA_TIMEOUT', '30'))
    
    def _convert_to_ollama_messages(self, messages: List[Message], 
                                   current_input: StructuredMessageContent) -> List[Dict]:
        """将历史消息与结构化输入序列化为 Ollama 可用的消息列表。"""
        ollama_messages = []
        
        # Convert previous messages
        for msg in messages:
            if isinstance(msg.content, str):
                ollama_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif isinstance(msg.content, StructuredMessageContent):
                ollama_messages.append({
                    "role": msg.role,
                    "content": msg.content.to_display_text()
                })
        
        # Convert current input
        if current_input:
            content_parts = []
            for block in current_input.blocks:
                if block.type == "text":
                    content_parts.append(block.content)
                elif block.type == "image":
                    content_parts.append(f"[图片: {block.content}]")
                elif block.type == "json":
                    content_parts.append(f"[JSON数据: {json.dumps(block.content, ensure_ascii=False)}]")
            
            ollama_messages.append({
                "role": "user",
                "content": " ".join(content_parts)
            })
        
        return ollama_messages
    
    async def generate_response(self, messages: List[Message], 
                              current_input: StructuredMessageContent) -> str:
        """调用 Ollama 接口返回文本响应（异步）。"""
        try:
            import aiohttp
            
            ollama_messages = self._convert_to_ollama_messages(messages, current_input)
            
            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/chat",
                    json=payload
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('message', {}).get('content', 'No response generated')
                    else:
                        error_text = await response.text()
                        return f"Error: Ollama API returned status {response.status}: {error_text}"
                        
        except ImportError:
            # Fallback to requests if aiohttp not available
            return await self._generate_response_sync(messages, current_input)
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}"
    
    async def _generate_response_sync(self, messages: List[Message], 
                                    current_input: StructuredMessageContent) -> str:
        """在缺少 aiohttp 时，使用 requests 的后备实现（仍包装为协程）。"""
        try:
            import requests
            
            ollama_messages = self._convert_to_ollama_messages(messages, current_input)
            
            payload = {
                "model": self.model,
                "messages": ollama_messages,
                "stream": False
            }
            
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('message', {}).get('content', 'No response generated')
            else:
                return f"Error: Ollama API returned status {response.status_code}: {response.text}"
                
        except ImportError:
            return f"Error: Missing HTTP client library (aiohttp or requests)"
        except Exception as e:
            return f"Error connecting to Ollama: {str(e)}"


class OpenAILLM(BaseLLM):
    """
    OpenAI 语言模型集成。

    支持将结构化内容转换为 OpenAI API 所需格式，且模型与端点可配置。
    """
    
    def __init__(self, model: str = None, api_key: str = None, 
                 base_url: str = None, timeout: int = None):
        """初始化 OpenAI 集成；需要提供或设置 OPENAI_API_KEY。"""
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.timeout = timeout or int(os.getenv('OPENAI_TIMEOUT', '30'))
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    def _convert_to_openai_messages(self, messages: List[Message], 
                                   current_input: StructuredMessageContent) -> List[Dict]:
        """把历史消息和结构化输入转换为 OpenAI API 可用格式。"""
        openai_messages = []
        
        # Convert previous messages
        for msg in messages:
            if isinstance(msg.content, str):
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif isinstance(msg.content, StructuredMessageContent):
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content.to_display_text()
                })
        
        # Convert current input
        if current_input:
            content_parts = []
            for block in current_input.blocks:
                if block.type == "text":
                    content_parts.append({"type": "text", "text": block.content})
                elif block.type == "image":
                    content_parts.append({
                        "type": "image_url", 
                        "image_url": {"url": block.content}
                    })
                elif block.type == "json":
                    content_parts.append({
                        "type": "text", 
                        "text": f"JSON数据: {json.dumps(block.content, ensure_ascii=False)}"
                    })
            
            openai_messages.append({
                "role": "user",
                "content": content_parts if len(content_parts) > 1 else content_parts[0]["text"]
            })
        
        return openai_messages
    
    async def generate_response(self, messages: List[Message], 
                              current_input: StructuredMessageContent) -> str:
        """调用 OpenAI 接口并返回文本响应（异步）。"""
        try:
            import aiohttp
            
            openai_messages = self._convert_to_openai_messages(messages, current_input)
            
            payload = {
                "model": self.model,
                "messages": openai_messages
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    json=payload,
                    headers=headers
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result["choices"][0]["message"]["content"]
                    else:
                        error_text = await response.text()
                        return f"Error: OpenAI API returned status {response.status}: {error_text}"
                        
        except ImportError:
            return f"Error: Missing aiohttp library for OpenAI API"
        except Exception as e:
            return f"Error connecting to OpenAI: {str(e)}"


class MockLLM(BaseLLM):
    """
    Mock 语言模型，用于在无外部依赖情况下的测试。

    模拟具有位置感知内容处理的 LLM 行为，适合在不调用真实 API 时进行测试。
    """
    
    async def generate_response(self, messages: List[Message], 
                              current_input: StructuredMessageContent) -> str:
        """基于结构化输入生成模拟回复（用于测试，无外部依赖）。"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        responses = ["我按指定顺序分析了您的内容："]
        
        # 处理每个内容块，按顺序
        for i, block in enumerate(current_input.blocks):
            block_desc = f"第{i+1}项"

            if block.type == "text":
                responses.append(f"{block_desc}: 文本内容 - {block.content}")
            elif block.type == "image":
                responses.append(f"{block_desc}: 图片文件 - {block.content}")
            elif block.type == "json":
                key_count = len(block.content) if isinstance(block.content, dict) else 0
                responses.append(f"{block_desc}: 包含 {key_count} 个字段的JSON数据")        # Add conversation context
        user_messages = [msg for msg in messages if msg.role == "user"]
        if len(user_messages) > 0:
            responses.append(f"这是我们对话中的第 #{len(user_messages) + 1} 次交互。")
        
        return " ".join(responses)
    

def create_llm(llm_type: str = None, **kwargs) -> BaseLLM:
    """根据 llm_type 返回相应的 LLM 实例（默认为 mock）。"""
    llm_type = (llm_type or os.getenv('LLM_TYPE', 'mock')).lower()
    if llm_type == 'mock':
        return MockLLM()
    if llm_type == 'ollama':
        return OllamaLLM(**kwargs)
    if llm_type in ['openai', 'oai']:
        return OpenAILLM(**kwargs)
    raise ValueError(f"Unsupported LLM type: {llm_type}")
