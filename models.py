"""对话模型与结构化消息块。"""

from typing import Dict, List, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import json


class ContentBlock(BaseModel):
    """单个内容块：text/image/json，含位置索引。"""
    type: str = Field(..., description="类型: text|image|json")
    content: Any = Field(..., description="内容")
    position: int = Field(default=0, description="位置索引，默认为 0")


class StructuredMessageContent(BaseModel):
    """有序内容块集合，支持添加文本/图片/JSON。"""
    blocks: List[ContentBlock] = Field(default_factory=list, description="内容块列表")

    def add_text(self, text: str, position: int | None = None) -> "StructuredMessageContent":
        """添加文本块（可选位置）。"""
        pos = position if position is not None else len(self.blocks)
        self.blocks.append(ContentBlock(type="text", content=text, position=pos))
        self._sort_blocks()
        return self

    def add_image(self, image_url: str, position: int | None = None) -> "StructuredMessageContent":
        """添加图片块（可选位置）。
            - image_url: 图片的 URL 地址或者 base64 编码字符串
            - position: 插入位置（如果为 None，默认为末尾）"""
        pos = position if position is not None else len(self.blocks)
        self.blocks.append(ContentBlock(type="image", content=image_url, position=pos))
        self._sort_blocks()
        return self

    def add_json(self, json_data: Dict[str, Any], position: int | None = None) -> "StructuredMessageContent":
        """添加 JSON 块（可选位置）。
            - json_data: JSON 数据
            - position: 插入位置（如果为 None，默认为末尾）"""
        pos = position if position is not None else len(self.blocks)
        self.blocks.append(ContentBlock(type="json", content=json_data, position=pos))
        self._sort_blocks()
        return self

    def _sort_blocks(self) -> None:
        self.blocks.sort(key=lambda x: x.position)

    def to_display_text(self) -> str:
        """把所有块合并为可读字符串。"""
        parts: List[str] = []
        for block in self.blocks:
            if block.type == "text":
                parts.append(str(block.content))
            elif block.type == "image":
                parts.append(f"[图片: {block.content}]")
            elif block.type == "json":
                parts.append(f"[JSON: {json.dumps(block.content, ensure_ascii=False)}]")
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
