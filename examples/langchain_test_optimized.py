#!/usr/bin/env python3
"""
LangChain 优化示例 - 轻量高效版
支持多轮对话、系统提示词、对话记录保存、多种LLM、结构化输出
使用conda infer环境，不依赖conversation模块
"""

from dotenv import load_dotenv
load_dotenv()

import os
import json
import base64
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from PIL import Image


# 结构化输出模型定义
class AnalysisResponse(BaseModel):
    """分析响应的结构化输出模型"""
    summary: str = Field(description="内容摘要")
    reasoning: str = Field(description="推理过程")
    confidence: float = Field(description="置信度 0-1", ge=0, le=1)
    tags: List[str] = Field(description="相关标签", default=[])


class ChatManager:
    """轻量级对话管理器"""
    
    def __init__(self, 
                 system_prompt: str = "你是一个有帮助的AI助手。",
                 model_type: str = "openai",
                 model_name: str = "gpt-3.5-turbo",
                 use_structured: bool = False,
                 **model_kwargs):
        
        self.system_prompt = system_prompt
        self.use_structured = use_structured
        self.model_type = model_type
        self.model_name = model_name
        
        # 初始化LLM（简化版，仅支持主流模型）
        if model_type == "openai":
            self.llm = ChatOpenAI(
                model=model_name,
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
                **model_kwargs
            )
        elif model_type == "ollama":
            self.llm = OllamaLLM(
                model=model_name,
                base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
                **model_kwargs
            )
        else:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        # 对话历史
        self.messages = [SystemMessage(content=system_prompt)]
        self.conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 结构化输出解析器（如果需要）
        self.parser = PydanticOutputParser(pydantic_object=AnalysisResponse) if use_structured else None
        
        # 保存目录
        save_dir = os.getenv("HISTORY_SAVE_DIR", "./log/conv_log/draft")
        self.save_dir = Path(save_dir)
        self.save_dir.mkdir(parents=True, exist_ok=True)
    
    def _encode_image(self, image_path: str) -> str:
        """编码图片为base64"""
        with open(image_path, "rb") as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def _create_multimodal_message(self, text: str, image_path: str) -> HumanMessage:
        """创建多模态消息"""
        base64_image = self._encode_image(image_path)
        content = [
            {"type": "text", "text": text},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
        ]
        return HumanMessage(content=content)
    
    def chat(self, user_input: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """进行对话 - 核心功能"""
        try:
            # 如果使用结构化输出，添加格式说明
            if self.use_structured and self.parser:
                format_instructions = self.parser.get_format_instructions()
                user_input += f"\n\n请严格按照以下JSON格式回答，不要添加任何其他内容：\n{format_instructions}"
            
            # 创建用户消息
            if image_path and os.path.exists(image_path):
                user_msg = self._create_multimodal_message(user_input, image_path)
            else:
                user_msg = HumanMessage(content=user_input)
            
            self.messages.append(user_msg)
            
            # 调用模型
            response = self.llm.invoke(self.messages)
            self.messages.append(response)
            
            # 解析响应
            if self.use_structured and self.parser:
                try:
                    # 清理响应内容，移除可能的思考标签
                    clean_response = response.content.strip()
                    # 如果有<think>标签，提取JSON部分
                    if '<think>' in clean_response and '</think>' in clean_response:
                        # 找到</think>后的内容
                        json_start = clean_response.find('</think>') + 8
                        clean_response = clean_response[json_start:].strip()
                    
                    # 尝试提取JSON部分
                    if '{' in clean_response and '}' in clean_response:
                        start = clean_response.find('{')
                        # 找到最后一个}
                        end = clean_response.rfind('}') + 1
                        json_content = clean_response[start:end]
                        parsed = self.parser.parse(json_content)
                    else:
                        parsed = self.parser.parse(clean_response)
                    
                    return {
                        "success": True,
                        "response": parsed.model_dump(),
                        "raw": response.content,
                        "structured": True
                    }
                except Exception as e:
                    return {
                        "success": True,
                        "response": response.content,
                        "raw": response.content,
                        "structured": False,
                        "parse_error": str(e)
                    }
            else:
                return {
                    "success": True,
                    "response": response.content,
                    "raw": response.content,
                    "structured": False
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": None
            }
    
    def save_conversation(self) -> str:
        """保存对话记录"""
        data = {
            "conversation_id": self.conversation_id,
            "timestamp": datetime.now().isoformat(),
            "model": f"{self.model_type}:{self.model_name}",
            "structured_output": self.use_structured,
            "messages": [
                {
                    "type": msg.__class__.__name__,
                    "content": msg.content,
                    "timestamp": datetime.now().isoformat()
                }
                for msg in self.messages
            ]
        }
        
        file_path = self.save_dir / f"{self.conversation_id}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return str(file_path)
    
    def clear_history(self):
        """清空对话历史（保留系统提示）"""
        self.messages = [self.messages[0]]


def demo_basic_chat():
    """基础多轮对话演示"""
    print("=== 基础多轮对话演示 ===")
    
    chat = ChatManager(
        system_prompt="你是一个专业的技术顾问，善于解释复杂概念。",
        model_type="openai",
        model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        temperature=0.7
    )
    
    questions = [
        "什么是机器学习？",
        "监督学习和无监督学习有什么区别？",
        "能举个具体的深度学习应用例子吗？"
    ]
    
    for i, q in enumerate(questions, 1):
        print(f"\n问题 {i}: {q}")
        result = chat.chat(q)
        
        if result["success"]:
            print(f"回答: {result['response']}")
        else:
            print(f"错误: {result['error']}")
    
    file_path = chat.save_conversation()
    print(f"\n对话已保存: {file_path}")


def demo_structured_output():
    """结构化输出演示"""
    print("=== 结构化输出演示 ===")
    
    chat = ChatManager(
        system_prompt="你是一个分析专家，需要提供结构化的分析结果。",
        model_type="openai",
        model_name=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        use_structured=True,
        temperature=0.5
    )
    
    question = "请分析Python编程语言的优缺点"
    print(f"问题: {question}")
    
    result = chat.chat(question)
    
    if result["success"]:
        if result["structured"]:
            print("结构化输出:")
            print(json.dumps(result["response"], ensure_ascii=False, indent=2))
        else:
            print("原始输出 (结构化解析失败):")
            print(result["response"])
            if "parse_error" in result:
                print(f"解析错误: {result['parse_error']}")
    else:
        print(f"错误: {result['error']}")
    
    chat.save_conversation()


def demo_multimodal():
    """多模态对话演示"""
    print("=== 多模态对话演示 ===")
    
    # 检查测试图片
    image_path = "data/images/test_image.jpg"
    if not os.path.exists(image_path):
        print(f"未找到测试图片: {image_path}")
        print("跳过多模态演示")
        return
    
    chat = ChatManager(
        system_prompt="你是一个图像分析专家，能够详细描述图片内容。",
        model_type="openai",
        model_name=os.getenv("OPENAI_MODEL", "gpt-4-vision-preview"),
        use_structured=True,
        temperature=0.3
    )
    
    question = "请分析这张图片的内容，描述你看到了什么"
    print(f"问题: {question}")
    print(f"图片: {image_path}")
    
    result = chat.chat(question, image_path)
    
    if result["success"]:
        if result["structured"]:
            print("结构化分析:")
            response = result["response"]
            print(f"摘要: {response.get('summary', 'N/A')}")
            print(f"推理: {response.get('reasoning', 'N/A')}")
            print(f"置信度: {response.get('confidence', 'N/A')}")
            print(f"标签: {', '.join(response.get('tags', []))}")
        else:
            print("图片分析结果:")
            print(result["response"])
    else:
        print(f"错误: {result['error']}")
    
    chat.save_conversation()


def demo_ollama():
    """Ollama本地模型演示"""
    print("=== Ollama本地模型演示 ===")
    
    try:
        chat = ChatManager(
            system_prompt="你是一个有帮助的AI助手。",
            model_type="ollama",
            model_name="llama2",  # 或其他已安装的模型
            temperature=0.8
        )
        
        question = "简单解释什么是人工智能"
        print(f"问题: {question}")
        
        result = chat.chat(question)
        
        if result["success"]:
            print(f"回答: {result['response']}")
        else:
            print(f"错误: {result['error']}")
            
        chat.save_conversation()
        
    except Exception as e:
        print(f"Ollama演示失败 (可能未安装): {e}")


def main():
    """主函数"""
    print("LangChain 优化演示程序")
    print("环境: conda infer")
    print("=" * 40)
    
    # 检查环境变量
    if not os.getenv("OPENAI_API_KEY"):
        print("警告: 未设置 OPENAI_API_KEY")
        print("请先设置: export OPENAI_API_KEY='your-key'")
        print()
    
    try:
        # 演示1: 基础多轮对话
        demo_basic_chat()
        print("\n" + "="*40)
        
        # 演示2: 结构化输出
        demo_structured_output()
        print("\n" + "="*40)
        
        # 演示3: 多模态对话
        demo_multimodal()
        print("\n" + "="*40)
        
        # 演示4: Ollama本地模型
        demo_ollama()
        
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"程序异常: {e}")
    
    print("\n演示完成！")


if __name__ == "__main__":
    main()
