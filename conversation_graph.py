"""
增强的LangGraph对话系统，支持结构化内容定位。

本模块使用LangGraph实现核心对话图，
高级支持结构化内容和位置感知处理。
"""

import asyncio
from typing import Dict, Optional, Any
from models import ConversationState, Message, StructuredMessageContent
from conversation_manager import ConversationManager
from llm import create_llm
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


class ConversationGraph:
    """
    LangGraph对话系统，支持结构化内容和并发控制。
    
    参数:
        max_concurrent: 最大并发数
        llm_type: LLM类型（'mock'、'ollama'、'openai'）
    属性:
        llm: 语言模型实例
        conversation_manager: 对话管理器
        semaphore: 并发信号量
    """

    def __init__(self, max_concurrent: int = 5, llm_type: str = None):
        self.llm = create_llm(llm_type)
        self.conversation_manager = ConversationManager()
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def _process_input(self, state: ConversationState) -> ConversationState:
        """
        加载历史，必要时添加系统提示。
        参数 / 返回: state: ConversationState
        """
        existing_messages = self.conversation_manager.get_conversation_history(
            state.conversation_id
        )
        state.messages = existing_messages
        
        # 如果是第一条消息，则添加系统提示
        if not state.messages and state.system_prompt:
            system_msg = Message(role="system", content=state.system_prompt)
            state.messages.append(system_msg)
            self.conversation_manager.save_message(state.conversation_id, system_msg)
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
            self.conversation_manager.save_message(state.conversation_id, user_msg)
        if state.response:
            assistant_msg = Message(role="assistant", content=state.response)
            self.conversation_manager.save_message(state.conversation_id, assistant_msg)
        
        # 重新加载完整对话历史以更新 state.messages
        state.messages = self.conversation_manager.get_conversation_history(
            state.conversation_id
        )
        return state

    async def chat(self,
                   conversation_id: Optional[str] = None,
                   system_prompt: Optional[str] = None,
                   structured_content: Optional[StructuredMessageContent] = None,
                   is_final: bool = False) -> Dict[str, Any]:
        """
        主聊天接口，支持结构化内容。
        参数:
            conversation_id: 对话ID
            system_prompt: 系统提示
            structured_content: 结构化输入
            is_final: 是否保存到文件
        返回: dict
        """
        async with self.semaphore:  # 控制并发
            state = ConversationState(
                conversation_id=conversation_id or ConversationState().conversation_id,
                system_prompt=system_prompt,
                current_input=structured_content
            )
            
            # 执行对话图：处理 → 生成 → 保存
            state = await self._process_input(state)
            state = await self._generate_response(state)
            state = await self._save_history(state)
            
            # 如果标记为最终，则保存完整对话
            if is_final:
                file_path = await self.conversation_manager.save_conversation_to_file(
                    state.conversation_id
                )
                self.conversation_manager.cleanup_memory(state.conversation_id)
                print(f"💾 Conversation 保存到: {file_path}")
            return {
                "conversation_id": state.conversation_id,
                "response": state.response,
                "message_count": len(state.messages),
                "input_preview": (state.current_input.to_display_text() 
                                if state.current_input else None)
            }
