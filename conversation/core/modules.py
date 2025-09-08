"""对话模型与结构化消息块。"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
from ..utils.id_utils import new_id
import json


class ContentBlock(BaseModel):
    """单个内容块：text/image/json，支持自定义扩展字段。"""
    type: str = Field(..., description="类型: text|image|json")
    content: Any = Field(..., description="内容")
    extras: Optional[Dict[str, Any]] = Field(default_factory=dict, description="自定义扩展字段")
    
    def __init__(self, **data):
        # 只保留 type/content/extras，其他全部进 extras
        extras = data.pop('extras', {})
        known = {k: data.pop(k) for k in ['type', 'content'] if k in data}
        extras.update(data)
        super().__init__(**known, extras=extras)
    
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


class Content(BaseModel):
    """有序内容块集合，支持添加文本/图片/JSON。"""
    blocks: List[ContentBlock] = Field(default_factory=list, description="内容块列表")

    def __init__(self, *items):
        """初始化结构化内容，支持混合项构建。
        
        支持输入类型：
        - str: 文本内容（单个文本或多个文本项）
        - {'image': 'url'} 或者 {'json': data}
        - (content, extras_dict): 内容 + 自定义字段
        
        示例:
            # 单文本初始化
            content = Content("这是一段文本")
            
            # 混合内容初始化
            content = Content(
                "开始文本", {'image': 'chart.png'}, {'json': {'data': 123}},
                ("结束文本", {'style': 'bold'})  # 带自定义字段
            )
        """
        super().__init__()
        if len(items) == 1 and isinstance(items[0], str):
            self.add_text(items[0])
            return
                
        # 处理混合输入项
        for item in items:
            extras = {}
            
            # 处理元组格式：(content, extras_dict)
            if isinstance(item, tuple):
                if len(item) != 2:
                    raise ValueError(f"元组参数应为 (content, extras_dict)，当前: {item}")
                item, extras = item
                if not isinstance(extras, dict):
                    raise ValueError(f"extras 必须是字典，当前: {extras}")
            
            # 根据内容类型添加块
            if isinstance(item, str):
                self.add_text(item, **extras)
            elif isinstance(item, dict):
                if 'text' in item:
                    self.add_text(item['text'], **extras)
                elif 'image' in item:
                    self.add_image(item['image'], **extras)
                elif 'json' in item:
                    self.add_json(item['json'], **extras)
                else:
                    raise ValueError(f"不支持的字典格式: {item}，应包含 'image' 或 'json' 键")
            else:
                raise ValueError(f"不支持的输入类型: {type(item)}，当前值: {item}")

    def add_text(self, text: str, **kwargs) -> "Content":
        """添加文本块到末尾，支持自定义字段。"""
        self.blocks.append(ContentBlock(type="text", content=text, **kwargs))
        return self

    def add_image(self, image_url: str, **kwargs) -> "Content":
        """添加图片块到末尾，支持自定义字段。"""
        # HSC: not elegant, move out
        # 存储原始路径和解析后的路径
        # 在extras中存储原始路径，便于后续处理
        from ..utils.image_utils import resolve_image_path
        resolved_path = resolve_image_path(image_url)
        if 'resolved_path' not in kwargs:
            kwargs['resolved_path'] = resolved_path
            
        self.blocks.append(ContentBlock(type="image", content=image_url, **kwargs))
        return self

    def add_json(self, json_data: Dict[str, Any], **kwargs) -> "Content":
        """添加 JSON 块到末尾，支持自定义字段。"""
        self.blocks.append(ContentBlock(type="json", content=json_data, **kwargs))
        return self

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
    msg_id: str = Field(default_factory=new_id, description="消息唯一标识符")
    role: str = Field(..., description="消息角色：system|user|assistant")
    content: Union[str, Content] = Field(..., description="消息内容")
    timestamp: datetime = Field(default_factory=datetime.now, description="消息时间戳")


class ConversationState(BaseModel):
    """运行时的对话状态与历史。"""
    conv_id: str = Field(default_factory=new_id, description="对话唯一标识符")
    system_prompt: Optional[str] = Field(None, description="系统提示词")
    current_input: Optional[Content] = Field(None, description="当前用户输入")
    response: Optional[str] = Field(None, description="助手回复")
    is_complete: bool = Field(False, description="对话是否已完成")
    response_format: Optional[Any] = Field(None, description="期望的回复格式，Pydantic BaseModel类")


class History(BaseModel):
    """已完成对话的内存存储、文件持久化表示。"""
    conv_id: str = Field(default_factory=new_id, description="对话唯一标识符")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")
    messages: List[Message] = Field(default_factory=list, description="对话消息列表")
