"""对话模型与结构化消息块。"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import json


class ContentBlock(BaseModel):
    """单个内容块：text/image/json，支持自定义扩展字段。"""
    type: str = Field(..., description="类型: text|image|json")
    content: Any = Field(..., description="内容")
    extras: Optional[Dict[str, Any]] = Field(default_factory=dict, description="自定义扩展字段")
    
    class Config:
        # 禁止额外字段，统一收集到 extras 中
        extra = "forbid"
    
    def __init__(self, **data):
        """支持 **kwargs 传入自定义字段，自动收集到 extras 中。"""
        # 提取标准字段
        standard_fields = {'type', 'content', 'extras'}
        standard_data = {k: v for k, v in data.items() if k in standard_fields}
        
        # 其余字段作为 extras
        extra_data = {k: v for k, v in data.items() if k not in standard_fields}
        if extra_data:
            existing_extras = standard_data.get('extras', {})
            standard_data['extras'] = {**existing_extras, **extra_data}
        
        super().__init__(**standard_data)
    
    def get_extra(self, key: str, default=None):
        """获取自定义字段值。"""
        return self.extras.get(key, default) if self.extras else default
    
    def set_extra(self, key: str, value: Any):
        """设置自定义字段值。"""
        if self.extras is None:
            self.extras = {}
        self.extras[key] = value
    
    def has_extra(self, key: str) -> bool:
        """检查是否存在指定的自定义字段。"""
        return bool(self.extras and key in self.extras)


class StructuredMessageContent(BaseModel):
    """有序内容块集合，支持添加文本/图片/JSON。"""
    blocks: List[ContentBlock] = Field(default_factory=list, description="内容块列表")

    def add_text(self, text: str, **kwargs) -> "StructuredMessageContent":
        """添加文本块到末尾。"""
        self.blocks.append(ContentBlock(type="text", content=text, **kwargs))
        return self

    def add_image(self, image_url: str, **kwargs) -> "StructuredMessageContent":
        """添加图片块到末尾。
            - image_url: 图片的 URL 地址或者 base64 编码字符串
            - **kwargs: 自定义字段，如 alt_text, width, height 等"""
        self.blocks.append(ContentBlock(type="image", content=image_url, **kwargs))
        return self

    def add_json(self, json_data: Dict[str, Any], **kwargs) -> "StructuredMessageContent":
        """添加 JSON 块到末尾。
            - json_data: JSON 数据
            - **kwargs: 自定义字段，如 schema, validator 等"""
        self.blocks.append(ContentBlock(type="json", content=json_data, **kwargs))
        return self
    
    def insert_text(self, index: int, text: str, **kwargs) -> "StructuredMessageContent":
        """在指定位置插入文本块。"""
        self.blocks.insert(index, ContentBlock(type="text", content=text, **kwargs))
        return self
    
    def insert_image(self, index: int, image_url: str, **kwargs) -> "StructuredMessageContent":
        """在指定位置插入图片块。"""
        self.blocks.insert(index, ContentBlock(type="image", content=image_url, **kwargs))
        return self
    
    def insert_json(self, index: int, json_data: Dict[str, Any], **kwargs) -> "StructuredMessageContent":
        """在指定位置插入 JSON 块。"""
        self.blocks.insert(index, ContentBlock(type="json", content=json_data, **kwargs))
        return self

    @classmethod
    def from_mixed_items(cls, *items) -> "StructuredMessageContent":
        """工厂方法：从混合项构建内容，按传入顺序排列。
        
        支持输入类型：
        - str: 文本内容
        - {'image': 'url'}: 图片
        - {'json': data}: JSON数据
        - (content, extras_dict): 内容和自定义字段
        
        示例:
            content = StructuredMessageContent.from_mixed_items(
                "开始文本",
                {'image': 'chart.png'},
                {'json': {'data': 123}},
                ("结束文本", {'style': 'bold'})  # 带自定义字段
            )
        """
        content = cls()
        
        for item in items:
            if isinstance(item, tuple):
                # 带自定义字段的项目
                if len(item) == 2:
                    data, extras = item
                    extras = extras or {}
                else:
                    raise ValueError(f"元组参数格式错误，应为 (content, extras_dict): {item}")
                
                if isinstance(data, str):
                    content.add_text(data, **extras)
                elif isinstance(data, dict):
                    if 'image' in data:
                        content.add_image(data['image'], **extras)
                    elif 'json' in data:
                        content.add_json(data['json'], **extras)
                    else:
                        content.add_json(data, **extras)  # 默认作为JSON处理
            else:
                # 普通项目，按顺序添加
                if isinstance(item, str):
                    content.add_text(item)
                elif isinstance(item, dict):
                    if 'image' in item:
                        content.add_image(item['image'])
                    elif 'json' in item:
                        content.add_json(item['json'])
                    else:
                        content.add_json(item)  # 默认作为JSON处理
        
        return content

    def to_display_text(self) -> str:
        """把所有块合并为可读字符串，可选择显示自定义字段信息。"""
        parts: List[str] = []
        for block in self.blocks:
            if block.type == "text":
                text = str(block.content)
                # 如果有样式信息，可以在显示时体现
                if block.has_extra('style'):
                    style = block.get_extra('style')
                    text = f"[{style}]{text}[/{style}]" if style in ['bold', 'italic'] else text
                parts.append(text)
            elif block.type == "image":
                img_text = f"[图片: {block.content}]"
                # 显示图片描述信息
                if block.has_extra('alt_text'):
                    img_text = f"[图片: {block.content} - {block.get_extra('alt_text')}]"
                elif block.has_extra('caption'):
                    img_text = f"[图片: {block.content} - {block.get_extra('caption')}]"
                parts.append(img_text)
            elif block.type == "json":
                json_text = f"[JSON: {json.dumps(block.content, ensure_ascii=False)}]"
                # 显示JSON源信息
                if block.has_extra('source'):
                    json_text = f"[JSON({block.get_extra('source')}): {json.dumps(block.content, ensure_ascii=False)}]"
                parts.append(json_text)
        return " ".join(parts)


class Message(BaseModel):
    """对话消息，包含角色、内容和时间戳。"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="消息唯一标识符")
    role: str = Field(..., description="消息角色：system|user|assistant")
    content: Union[str, StructuredMessageContent] = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="消息时间戳")


class ConversationState(BaseModel):
    """运行时的对话状态与历史。"""
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="对话唯一标识符")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    messages: List[Message] = Field(default_factory=list, description="对话消息列表")
    current_input: Optional[StructuredMessageContent] = Field(None, description="当前用户输入")
    response: Optional[str] = Field(None, description="助手回复")
    is_complete: bool = Field(False, description="对话是否已完成")


class ConversationHistory(BaseModel):
    """已完成对话的持久化表示。"""
    conversation_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="对话唯一标识符")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    messages: List[Message] = Field(default_factory=list, description="对话消息列表")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
