"""
Language Model 实现，用于对话系统。

支持多个 LLM 提供者：Mock、Ollama 和 OpenAI。
基于配置驱动并支持环境变量。
"""

import asyncio
import json
import os
from typing import Dict, List
from abc import ABC, abstractmethod
from models import Message, StructuredMessageContent


class BaseLLM(ABC):
    """所有 LLM 实现的基类。"""
    
    @abstractmethod
    async def generate_response(self, messages: List[Message], 
                              current_input: StructuredMessageContent) -> str:
        """基于对话历史和当前输入生成响应。"""
        pass


class OllamaLLM(BaseLLM):
    """
    Ollama 语言模型集成。

    用于 Ollama API 的轻量级 HTTP 客户端，支持结构化内容和多模态输入。
    """
    
    def __init__(self, model: str = None, base_url: str = None, timeout: int = None):
        """
        初始化 Ollama LLM，支持配置参数。

        参数:
            model: 模型名称（默认来自环境变量 OLLAMA_MODEL 或 qwen2.5vl:3b）
            base_url: Ollama API 地址（默认来自环境变量 OLLAMA_BASE_URL 或本地地址）
            timeout: 请求超时时间（默认来自环境变量 OLLAMA_TIMEOUT 或 30 秒）
        """
        self.base_url = base_url or os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = model or os.getenv('OLLAMA_MODEL', 'qwen2.5vl:3b')
        self.timeout = timeout or int(os.getenv('OLLAMA_TIMEOUT', '30'))
    
    def _convert_to_ollama_messages(self, messages: List[Message], 
                                   current_input: StructuredMessageContent) -> List[Dict]:
        """将结构化内容转换为 Ollama 可接受的格式。"""
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
        """使用 Ollama API 生成响应。"""
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
        """使用 requests 的后备同步实现。"""
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
        """
        初始化 OpenAI LLM，支持配置参数。

        参数:
            model: 模型名称（默认来自环境变量 OPENAI_MODEL 或 gpt-3.5-turbo）
            api_key: API 密钥（默认来自环境变量 OPENAI_API_KEY）
            base_url: API 基础地址（默认来自环境变量 OPENAI_BASE_URL）
            timeout: 请求超时时间（默认来自环境变量 OPENAI_TIMEOUT 或 30 秒）
        """
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        self.base_url = base_url or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        self.timeout = timeout or int(os.getenv('OPENAI_TIMEOUT', '30'))
        
        if not self.api_key:
            raise ValueError("OpenAI API key is required")
    
    def _convert_to_openai_messages(self, messages: List[Message], 
                                   current_input: StructuredMessageContent) -> List[Dict]:
        """将结构化内容转换为 OpenAI 可接受的消息格式。"""
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
        """使用 OpenAI API 生成响应。"""
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
        """
        Generate mock response based on structured input.
        
        Analyzes input content blocks in specified order
        and generates contextual response.
        """
        await asyncio.sleep(0.1)  # Simulate API delay
        
        responses = ["我按指定顺序分析了您的内容："]
        
        # Process each block in position order
        for block in current_input.blocks:
            position_text = f"位置 {block.position}"
            
            if block.type == "text":
                responses.append(f"{position_text}: 文本内容 - {block.content}")
            elif block.type == "image":
                responses.append(f"{position_text}: 图片文件 - {block.content}")
            elif block.type == "json":
                key_count = len(block.content) if isinstance(block.content, dict) else 0
                responses.append(f"{position_text}: 包含 {key_count} 个字段的JSON数据")
        
        # Add conversation context
        user_messages = [msg for msg in messages if msg.role == "user"]
        if len(user_messages) > 0:
            responses.append(f"这是我们对话中的第 #{len(user_messages) + 1} 次交互。")
        
        return " ".join(responses)
    

def create_llm(llm_type: str = None, **kwargs) -> BaseLLM:
    """
    工厂函数：根据配置创建 LLM 实例。

    参数:
        llm_type: LLM 类型（'mock'、'ollama'、'openai'）
        **kwargs: 传递给 LLM 初始化的额外参数

    返回:
        已初始化的 LLM 实例
    """
    llm_type = llm_type or os.getenv('LLM_TYPE', 'mock').lower()
    
    if llm_type == 'mock':
        return MockLLM()
    elif llm_type == 'ollama':
        return OllamaLLM(**kwargs)
    elif llm_type == 'openai':
        return OpenAILLM(**kwargs)
    else:
        raise ValueError(f"Unsupported LLM type: {llm_type}")
