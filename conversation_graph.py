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
    LangGraph 实现，支持可配置的 LLM。

    实现三节点对话工作流：输入处理、响应生成和历史保存，完整支持带位置信息的多模态内容。

    属性:
        llm: 可配置的语言模型实例
        conversation_manager: 管理对话持久化
        semaphore: 控制并发处理
    """
    
    def __init__(self, max_concurrent: int = 5, llm_type: str = None):
        """
        初始化对话图并配置可选的 LLM。

        参数:
            max_concurrent: 最大并发对话数
            llm_type: 要使用的 LLM 类型（'mock'、'ollama'、'openai'）
        """
        self.llm = create_llm(llm_type)
        self.conversation_manager = ConversationManager()
        self.semaphore = asyncio.Semaphore(max_concurrent)
    
    async def _process_input(self, state: ConversationState) -> ConversationState:
        """
        Process user input and load conversation history.
        
        First node in the conversation graph that handles input processing
        and loads existing conversation history if available.
        
        参数:
            state: 当前对话状态
            
        返回:
            加载历史后的更新对话状态
        """
    # 加载现有对话历史
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
        使用语言模型生成AI响应。
        
        对话图中的第二个节点，处理结构化
        输入并生成适当的响应。
        
        参数:
            state: 当前对话状态
            
        返回:
            生成响应后的更新对话状态
        """
        if state.current_input:
            response = await self.llm.generate_response(state.messages, state.current_input)
            state.response = response
        return state
    
    async def _save_history(self, state: ConversationState) -> ConversationState:
        """
        将对话消息保存到历史记录。
        
        对话图中的第三个节点，将用户
        输入和AI响应持久化到对话历史。
        
        参数:
            state: 当前对话状态
            
        返回:
            保存消息后的更新对话状态
        """
        # 保存带结构化内容的用户消息
        if state.current_input:
            user_msg = Message(role="user", content=state.current_input)
            # 仅保存到 conversation manager，而不添加到 state.messages
            # 以避免在下次加载对话时重复
            self.conversation_manager.save_message(state.conversation_id, user_msg)
        
        # 保存助手响应
        if state.response:
            assistant_msg = Message(role="assistant", content=state.response)
            # 仅保存到 conversation manager
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
        带结构化内容支持的主聊天接口。
        
        处理对话轮次，支持复杂的多模态
        内容定位并维护对话历史。
        
        参数:
            conversation_id: 现有对话ID或None表示新对话
            system_prompt: AI行为的系统提示词（仅首条消息）
            structured_content: 带位置内容块的结构化输入
            is_final: 是否将完整对话保存到文件
            
        返回:
            包含conversation_id、response、message_count和input_preview的字典
        """
        async with self.semaphore:  # 控制并发
            # Create conversation state
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
