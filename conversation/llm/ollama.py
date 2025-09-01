"""Ollama LLM实现"""

import json
import os
from typing import List, Dict
from .base import BaseLLM
from ..core.modules import Message, Content


class OllamaLLM(BaseLLM):
    """Ollama语言模型集成，支持多模态输入"""
    
    def __init__(self, model: str = None, base_url: str = None, timeout: int = None):
        """初始化Ollama集成，model/base_url/timeout可由环境变量覆盖"""
        self.model = (
            model if model is None else 
            os.getenv('OLLAMA_MODEL', 'qwen2.5vl:3b')
        )
        self.base_url = (
            base_url if base_url is None else 
            os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        )
        self.timeout = (
            timeout if timeout is None else
            int(os.getenv('OLLAMA_TIMEOUT', '30'))
        )

    def convert_messages(self, messages: List[Message],
                        current_input: Content) -> List[Dict]:
        """将历史消息与结构化输入序列化为Ollama可用的消息列表"""
        ollama_messages = []
        
        # 转换历史消息
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
        
        # 转换当前输入
        if current_input:
            content_parts = []
            for blk in current_input.blocks:
                if blk.type == "text":
                    content_parts.append(blk.content)
                elif blk.type == "image":
                    # 加载并转换图片为base64供Ollama使用
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
        """调用Ollama接口返回文本响应（异步），支持图片输入"""
        import aiohttp
        
        # 检查当前输入是否包含图片
        has_images = False
        images = []
        
        if current_input:
            for blk in current_input.blocks:
                if blk.type == "image":
                    from ..utils import load_image
                    image_data = load_image(blk.content, return_type="base64")
                    if image_data:
                        images.append(image_data.get('base64', ''))
                        has_images = True
        
        # 如果有图片，使用/api/generate端点
        if has_images:
            # 构建文本prompt
            prompt_parts = []
            for msg in messages:
                if isinstance(msg.content, str):
                    prompt_parts.append(f"{msg.role}: {msg.content}")
                elif isinstance(msg.content, Content):
                    prompt_parts.append(f"{msg.role}: {msg.content.to_display_text()}")
            
            if current_input:
                user_text = []
                for blk in current_input.blocks:
                    if blk.type == "text":
                        user_text.append(blk.content)
                    elif blk.type == "json":
                        user_text.append(f"[JSON数据: {json.dumps(blk.content, ensure_ascii=False)}]")
                prompt_parts.append(f"user: {' '.join(user_text)}")
            
            payload = {
                "model": self.model,
                "prompt": "\n".join(prompt_parts),
                "images": images,
                "stream": False
            }
            
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload
                ) as response:
                    response.raise_for_status()
                    result = await response.json()
                    return result.get('response', 'No response generated')
        
        else:
            # 没有图片，使用原来的/api/chat端点
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
