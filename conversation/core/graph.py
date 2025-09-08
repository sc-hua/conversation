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
from ..utils.logging import get_logger, log_exception, warn_once
from ..utils.id_utils import shortcut_id, new_id


class ConversationGraph:
    """
    LangGraph对话系统，支持结构化内容和并发控制。
    
    参数:
        llm：语言模型类型（'mock'、'ollama'、'openai'）
        max_concurrent: 最大并发数
        history_save_dir: 对话历史保存目录
    属性:
        llm: 语言模型实例
        history_manager: 对话管理器
        semaphore: 并发信号量
    """

    def __init__(
        self, 
        llm: str | BaseLLM | None = None,
        max_concurrent: int = 5,
        history_save_dir: str = None,
    ):
        self.llm = llm if isinstance(llm, BaseLLM) else create_llm(llm)
        self.history_manager = HistoryManager(history_save_dir=history_save_dir)
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.logger = get_logger("graph")

    # HSC: check whether this is needed
    # def generate_conv_id(self) -> str:
    #     return new_id()

    @log_exception
    async def _prepare_messages(self, state: ConversationState) -> ConversationState:
        """
        加载历史，必要时添加系统提示。
        参数 / 返回: state: ConversationState
        """
        # 如果是第一条消息，则添加系统提示
        if (not self.history_manager.get_msgs(state.conv_id) and state.system_prompt):
            self.logger.debug(f"[Add system_prompt] | conv_id = {shortcut_id(state.conv_id)}")
            self.history_manager.save_msg(
                conv_id=state.conv_id,
                msg=Message(role="system", content=state.system_prompt)
            )
        return state

    @log_exception
    async def _generate_response(self, state: ConversationState) -> ConversationState:
        """
        用LLM生成AI回复。
        参数 / 返回: state: ConversationState
        """
        if state.current_input:
            self.logger.info(f"[Generate response] | conv_id = {shortcut_id(state.conv_id)}")
            response = await self.llm.generate_response(
                messages=self.history_manager.get_msgs(state.conv_id), 
                current_input=state.current_input
            )
            state.response = response
        return state

    @log_exception
    async def _save_history(self, state: ConversationState) -> ConversationState:
        """
        保存用户输入和AI回复到历史。
        参数 / 返回: state: ConversationState
        """
        if state.current_input:
            self.history_manager.save_msg(
                conv_id=state.conv_id, 
                msg=Message(role="user", content=state.current_input)
            )
        if state.response:
            self.history_manager.save_msg(
                conv_id=state.conv_id,
                msg=Message(role="assistant", content=state.response)
            )
            self.logger.debug(f"[Save history] | "
                              f"conv_id = {shortcut_id(state.conv_id)} | "
                              f"messages = {self.history_manager.get_length(state.conv_id)}")
        return state

    @log_exception
    async def chat(
        self,
        conv_id: Optional[str] = None,
        system_prompt: Optional[str] = None,
        content: Optional[Content] = None,
        return_history: bool = False,
    ) -> Dict[str, Any]:
        """
        主聊天接口，支持结构化内容。
        参数:
            conv_id: 对话ID
            system_prompt: 系统提示
            content: 结构化输入
        返回: dict
        """
        # # HSC: will remove
        # assert conv_id, "必须提供 conv_id"
        async with self.semaphore:  # 控制并发
            state = ConversationState(
                conv_id=conv_id or ConversationState().conv_id,
                system_prompt=system_prompt,
                current_input=content
            )

            self.logger.info(f"[Start conversation] | conv_id = {shortcut_id(state.conv_id)}")
            # 执行对话图：处理 → 生成 → 保存
            state = await self._prepare_messages(state)
            state = await self._generate_response(state)
            state = await self._save_history(state)

            self.logger.info(f"[End conversation] | "
                             f"conv_id = {shortcut_id(state.conv_id)} | "
                             f"messages = {self.history_manager.get_length(state.conv_id)}")

            result = {
                "conv_id": state.conv_id,
                "response": state.response,
                "message_count": self.history_manager.get_length(state.conv_id),
            }

            if return_history:
                result["history"] = self.history_manager.to_json(state.conv_id)
            return result

    async def end(self, conv_id: str, save: bool) -> str:
        """保存对话到文件并清理内存。"""
        file_path = None
        if save:
            file_path = await self.history_manager.save_conversation_to_file(conv_id)
            self.logger.info(f"[Conversation saved] | file = {file_path}")
        self.history_manager.cleanup_memory(conv_id)
        self.logger.debug(f"[Cleanup memory] | conv_id = {shortcut_id(conv_id)}")
        return file_path