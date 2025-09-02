"""
增强的LangGraph对话系统，支持结构化内容定位。

本模块使用LangGraph实现核心对话图，
高级支持结构化内容和位置感知处理。
"""

import asyncio
from typing import Dict, Optional, Any
from .modules import ConversationState, Message, Content
from .manager import HistoryManager
from ..llm import create_llm, BaseLLM


class ConversationGraph:
    """
    LangGraph对话系统，支持结构化内容和并发控制。
    
    参数:
        llm：语言模型类型（'mock'、'ollama'、'openai'）
        max_concurrent: 最大并发数
    属性:
        llm: 语言模型实例
        history_manager: 对话管理器
        semaphore: 并发信号量
    """

    def __init__(self, 
                 llm: str | BaseLLM | None = None, 
                 max_concurrent: int = 5):
        self.llm = llm if isinstance(llm, BaseLLM) else create_llm(llm)
        self.history_manager = HistoryManager()
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def _process_input(self, state: ConversationState) -> ConversationState:
        """
        加载历史，必要时添加系统提示。
        参数 / 返回: state: ConversationState
        """
        existing_messages = self.history_manager.get_history_msgs(state.conv_id)
        state.messages = existing_messages
        
        # 如果是第一条消息，则添加系统提示
        if not state.messages and state.system_prompt:
            system_msg = Message(role="system", content=state.system_prompt)
            state.messages.append(system_msg)
            self.history_manager.save_msg(state.conv_id, system_msg)
        return state

    async def _generate_response(self, state: ConversationState) -> ConversationState:
        """
        用LLM生成AI回复。
        参数 / 返回: state: ConversationState
        """
        if state.current_input:
            response = await self.llm.generate_response(state.messages, state.current_input)
            state.response = response
        return state

    async def _save_history(self, state: ConversationState) -> ConversationState:
        """
        保存用户输入和AI回复到历史。
        参数 / 返回: state: ConversationState
        """
        if state.current_input:
            user_msg = Message(role="user", content=state.current_input)
            self.history_manager.save_msg(state.conv_id, user_msg)
        if state.response:
            assistant_msg = Message(role="assistant", content=state.response)
            self.history_manager.save_msg(state.conv_id, assistant_msg)
        
        # 重新加载完整对话历史以更新 state.messages
        state.messages = self.history_manager.get_history_msgs(
            state.conv_id
        )
        return state

    async def chat(self,
                   conv_id: Optional[str] = None,
                   system_prompt: Optional[str] = None,
                   content: Optional[Content] = None) -> Dict[str, Any]:
        """
        主聊天接口，支持结构化内容。
        参数:
            conv_id: 对话ID
            system_prompt: 系统提示
            content: 结构化输入
        返回: dict
        """
        async with self.semaphore:  # 控制并发
            state = ConversationState(
                conv_id=conv_id or ConversationState().conv_id,
                system_prompt=system_prompt,
                current_input=content
            )
            
            # 执行对话图：处理 → 生成 → 保存
            state = await self._process_input(state)
            state = await self._generate_response(state)
            state = await self._save_history(state)
            
            return {
                "conv_id": state.conv_id,
                "response": state.response,
                "message_count": len(state.messages),
                "input_preview": (state.current_input.to_display_text() 
                                if state.current_input else None)
            }

    async def end(self, conv_id: str, save: bool) -> str:
        """保存对话到文件并清理内存。"""
        if save:
            file_path = await self.history_manager.save_conversation_to_file(conv_id)
            print(f"💾 对话已保存到: {file_path}")
        self.history_manager.cleanup_memory(conv_id)
        return file_path