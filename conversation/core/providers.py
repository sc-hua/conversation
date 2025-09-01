"""LLM 集成：提供 Mock、Ollama、OpenAI 的轻量封装。"""

import asyncio
import json
import os
from typing import Dict, List
from abc import ABC, abstractmethod
from .modules import Message, Content


class BaseLLM(ABC):
    """LLM 抽象基类。实现类需实现 convert_messages 和 generate_response。"""

    @abstractmethod
    def convert_messages(self, messages: List[Message], 
                        current_input: Content) -> List[Dict]:
        """将历史消息与结构化输入转换为特定LLM所需的消息格式。"""
        raise NotImplementedError()

    @abstractmethod
    async def generate_response(self, messages: List[Message], 
                              current_input: Content) -> str:
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
    
    def convert_messages(self, messages: List[Message], 
                        current_input: Content) -> List[Dict]:
        """将历史消息与结构化输入序列化为 Ollama 可用的消息列表。"""
        ollama_messages = []
        
        # Convert previous messages
        for msg in messages:
            if isinstance(msg.content, str):
                ollama_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif isinstance(msg.content, Content):
                ollama_messages.append({
                    "role": msg.role,
                    "content": msg.content.to_display_text()
                })
        
        # Convert current input
        if current_input:
            content_parts = []
            for blk in current_input.blocks:
                if blk.type == "text":
                    content_parts.append(blk.content)
                elif blk.type == "image":
                    # 加载并转换图片为 base64 供 Ollama 使用
                    from ..utils import load_image
                    image_data = load_image(blk.content, return_type="base64")
                    if image_data:
                        # Ollama支持base64图片，格式为 data:image/format;base64,data
                        img_format = image_data.get('format', 'PNG').lower()
                        base64_str = image_data.get('base64', '')
                        content_parts.append(f"data:image/{img_format};base64,{base64_str}")
                    else:
                        content_parts.append(f"[图片: {blk.content}]")
                elif blk.type == "json":
                    content_parts.append(f"[JSON数据: {json.dumps(blk.content, ensure_ascii=False)}]")
            
            ollama_messages.append({
                "role": "user",
                "content": " ".join(content_parts)
            })
        
        return ollama_messages
    
    async def generate_response(self, messages: List[Message], 
                              current_input: Content) -> str:
        """调用 Ollama 接口返回文本响应（异步）。"""
        import aiohttp
        
        ollama_messages = self.convert_messages(messages, current_input)
        
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
                response.raise_for_status()
                result = await response.json()
                return result.get('message', {}).get('content', 'No response generated')



class OpenAILLM(BaseLLM):
    """
    OpenAI 语言模型集成。

    支持将结构化内容转换为 OpenAI API 所需格式，且模型与端点可配置。
    """
    
    def __init__(self, model: str = None, api_key: str = None, 
                 base_url: str = None, timeout: int = None):
        """初始化 OpenAI 集成；需要提供或设置 OPENAI_API_KEY。"""
        self.model = model or os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(
            api_key=api_key or os.getenv('OPENAI_API_KEY'),
            base_url=base_url or os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1'),
            timeout=timeout or int(os.getenv('OPENAI_TIMEOUT', '30'))
        )
    
    def convert_messages(self, messages: List[Message], 
                        current_input: Content) -> List[Dict]:
        """把历史消息和结构化输入转换为 OpenAI API 可用格式。"""
        openai_messages = []
        
        # Convert previous messages
        for msg in messages:
            if isinstance(msg.content, str):
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif isinstance(msg.content, Content):
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content.to_display_text()
                })
        
        # Convert current input
        if current_input:
            content_parts = []
            for blk in current_input.blocks:
                if blk.type == "text":
                    content_parts.append({"type": "text", "text": blk.content})
                elif blk.type == "image":
                    # 处理图片：URL直接使用，本地文件转换为base64
                    image_url = blk.content
                    if not (image_url.startswith('http://') or image_url.startswith('https://')):
                        # 本地文件，转换为 base64 data URL
                        from ..utils import load_image
                        image_data = load_image(image_url, return_type="base64")
                        if image_data:
                            img_format = image_data.get('format', 'PNG').lower()
                            base64_str = image_data.get('base64', '')
                            image_url = f"data:image/{img_format};base64,{base64_str}"
                    
                    content_parts.append({
                        "type": "image_url", 
                        "image_url": {"url": image_url}
                    })
                elif blk.type == "json":
                    content_parts.append({
                        "type": "text", 
                        "text": f"JSON数据: {json.dumps(blk.content, ensure_ascii=False)}"
                    })
            
            openai_messages.append({
                "role": "user",
                "content": content_parts if len(content_parts) > 1 else content_parts[0]["text"]
            })
        
        return openai_messages
    
    async def generate_response(self, messages: List[Message], 
                              current_input: Content) -> str:
        """调用 OpenAI 接口并返回文本响应（异步）。"""
        openai_messages = self.convert_messages(messages, current_input)
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages
        )
        
        return response.choices[0].message.content


class MockLLM(BaseLLM):
    """
    Mock 语言模型，用于在无外部依赖情况下的测试。

    模拟具有位置感知内容处理的 LLM 行为，适合在不调用真实 API 时进行测试。
    """
    
    def convert_messages(self, messages: List[Message], 
                        current_input: Content) -> List[Dict]:
        """将历史消息与结构化输入转换为模拟格式（用于测试）。"""
        mock_messages = []
        
        # Convert previous messages  
        for msg in messages:
            if isinstance(msg.content, str):
                mock_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif isinstance(msg.content, Content):
                mock_messages.append({
                    "role": msg.role,
                    "content": msg.content.to_display_text()
                })
        
        # Convert current input
        if current_input:
            mock_messages.append({
                "role": "user",
                "content": current_input.to_display_text()
            })
        
        return mock_messages
    
    async def generate_response(self, messages: List[Message], 
                              current_input: Content) -> str:
        """基于结构化输入生成模拟回复（用于测试，无外部依赖）。"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        responses = ["我按指定顺序分析了您的内容："]
        
        # 处理每个内容块，按顺序
        for i, blk in enumerate(current_input.blocks):
            block_desc = f"第{i+1}项"

            if blk.type == "text":
                responses.append(f"{block_desc}: 文本内容 - {blk.content}")
            elif blk.type == "image":
                responses.append(f"{block_desc}: 图片文件 - {blk.content}")
            elif blk.type == "json":
                key_count = len(blk.content) if isinstance(blk.content, dict) else 0
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
