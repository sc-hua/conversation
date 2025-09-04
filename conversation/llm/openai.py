"""OpenAI LLM实现"""

import json
import os
from typing import List, Dict
from .base import BaseLLM
from ..core.modules import Message, Content
from ..utils.image_utils import load_image


class OpenAILLM(BaseLLM):
    """OpenAI语言模型集成，支持多模态输入"""
    
    def __init__(self, model: str = None, api_key: str = None, 
                 base_url: str = None, timeout: int = None):
        """可选覆盖默认配置"""
        self.model = model if model is not None else os.getenv('OPENAI_MODEL')
        self.api_key = api_key if api_key is not None else os.getenv('OPENAI_API_KEY')
        self.base_url = base_url if base_url is not None else os.getenv('OPENAI_BASE_URL')
        self.timeout = timeout if timeout is not None else int(os.getenv('OPENAI_TIMEOUT'))            
        if not self.api_key:
            raise ValueError("需要设置OPENAI_API_KEY环境变量")
        
        # 初始化客户端
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
                timeout=self.timeout,
            )
        except ImportError:
            raise ImportError("请安装openai包: pip install openai")
    
    
    def convert_messages(self, messages: List[Message], 
                        current_input: Content) -> List[Dict]:
        """将历史消息与结构化输入序列化为OpenAI可用的消息列表"""
        openai_messages = []
        
        # 转换历史消息
        for msg in messages:
            if isinstance(msg.content, str):
                openai_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            elif isinstance(msg.content, Content):
                # 检查是否有多模态内容
                content_parts = []
                has_media = False
                
                for blk in msg.content.blocks:
                    if blk.type == "text":
                        content_parts.append({"type": "text", "text": blk.content})
                    elif blk.type == "image":
                        image_data = load_image(blk.content, return_type="base64")
                        if image_data:
                            img_format = image_data.get('format', 'PNG').lower()
                            base64_str = image_data.get('base64', '')
                            content_parts.append({
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{img_format};base64,{base64_str}"
                                }
                            })
                            has_media = True
                        else:
                            content_parts.append({"type": "text", "text": f"[图片: {blk.content}]"})
                    elif blk.type == "json":
                        json_text = json.dumps(blk.content, ensure_ascii=False)
                        content_parts.append({"type": "text", "text": f"[JSON数据: {json_text}]"})
                
                if has_media or len(content_parts) > 1:
                    # 多模态内容
                    openai_messages.append({
                        "role": msg.role,
                        "content": content_parts
                    })
                else:
                    # 纯文本内容
                    text_content = content_parts[0]["text"] if content_parts else ""
                    openai_messages.append({
                        "role": msg.role,
                        "content": text_content
                    })
        
        # 转换当前输入
        if current_input:
            content_parts = []
            has_media = False
            
            for blk in current_input.blocks:
                if blk.type == "text":
                    content_parts.append({"type": "text", "text": blk.content})
                elif blk.type == "image":
                    image_data = load_image(blk.content, return_type="base64")
                    if image_data:
                        img_format = image_data.get('format', 'PNG').lower()
                        base64_str = image_data.get('base64', '')
                        content_parts.append({
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/{img_format};base64,{base64_str}"
                            }
                        })
                        has_media = True
                    else:
                        content_parts.append({"type": "text", "text": f"[图片: {blk.content}]"})
                elif blk.type == "json":
                    json_text = json.dumps(blk.content, ensure_ascii=False)
                    content_parts.append({"type": "text", "text": f"[JSON数据: {json_text}]"})
            
            if has_media or len(content_parts) > 1:
                # 多模态内容
                openai_messages.append({
                    "role": "user",
                    "content": content_parts
                })
            else:
                # 纯文本内容
                text_content = content_parts[0]["text"] if content_parts else ""
                openai_messages.append({
                    "role": "user",
                    "content": text_content
                })
        
        return openai_messages
    
    
    async def generate_response(self, messages: List[Message], 
                              current_input: Content) -> str:
        """调用OpenAI接口返回文本响应（异步）"""
        openai_messages = self.convert_messages(messages, current_input)
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=openai_messages,
        )
        
        return response.choices[0].message.content