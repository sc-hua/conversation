#!/usr/bin/env python3
"""
多模态对话导出工具

将对话记录转换为 LLaMA-Factory 兼容的多模态格式，
支持图片、音频、视频等多种模态内容。
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from ..core.modules import History, Message, Content, ContentBlock


class MultimodalExporter:
    """多模态对话记录导出器"""
    
    def __init__(self, conversations_dir: str = None):
        """
        初始化导出器
        
        Args:
            conversations_dir: 对话记录目录
        """
        conversations_dir = conversations_dir or os.getenv("HISTORY_SAVE_DIR")
        self.conversations_dir = Path(conversations_dir)
        
    def load_conversation(self, conversation_file: str) -> Optional[History]:
        """加载对话记录文件"""
        try:
            file_path = self.conversations_dir / conversation_file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # 重构消息格式
            messages = []
            for msg_data in data.get('messages', []):
                if isinstance(msg_data['content'], dict) and 'blocks' in msg_data['content']:
                    # 结构化内容
                    content = Content()
                    for block in msg_data['content']['blocks']:
                        content.blocks.append(ContentBlock(
                            type=block['type'],
                            content=block['content'],
                            position=block['position']
                        ))
                    content._sort_blocks()
                else:
                    # 简单文本内容
                    content = msg_data['content']
                
                messages.append(Message(
                    id=msg_data['id'],
                    role=msg_data['role'],
                    content=content,
                    timestamp=datetime.fromisoformat(msg_data['timestamp'])
                ))
            
            return History(
                conv_id=data['conv_id'],
                messages=messages,
                created_at=datetime.fromisoformat(data['created_at']),
                updated_at=datetime.fromisoformat(data['updated_at']),
                system_prompt=data.get('system_prompt'),
                metadata=data.get('metadata')
            )
            
        except Exception as e:
            print(f"❌ 加载对话文件失败 {conversation_file}: {e}")
            return None
    
    def extract_media_content(self, content_block: ContentBlock) -> Dict[str, Any]:
        """提取媒体内容信息"""
        media_info = {
            'placeholder': '',
            'file_path': None,
            'media_type': None
        }
        
        if content_block.type == 'image':
            media_info['placeholder'] = '<image>'
            media_info['file_path'] = content_block.content
            media_info['media_type'] = 'image'
        elif content_block.type == 'audio':
            media_info['placeholder'] = '<audio>'
            media_info['file_path'] = content_block.content
            media_info['media_type'] = 'audio'
        elif content_block.type == 'video':
            media_info['placeholder'] = '<video>'
            media_info['file_path'] = content_block.content
            media_info['media_type'] = 'video'
            
        return media_info
    
    def convert_to_llamafactory_format(self, conversation: History) -> Dict[str, Any]:
        """转换为 LLaMA-Factory 格式"""
        result = {
            'messages': [],
            'images': [],
            'audios': [],
            'videos': []
        }
        
        # 跳过系统消息，只处理用户和助手的对话
        user_assistant_messages = [msg for msg in conversation.messages 
                                 if msg.role in ['user', 'assistant']]
        
        current_message_content = ""
        current_media_files = {'images': [], 'audios': [], 'videos': []}
        
        for i, message in enumerate(user_assistant_messages):
            if isinstance(message.content, Content):
                # 处理结构化内容
                content_parts = []
                
                for block in message.content.blocks:
                    if block.type == 'text':
                        content_parts.append(block.content)
                    elif block.type in ['image', 'audio', 'video']:
                        media_info = self.extract_media_content(block)
                        content_parts.append(media_info['placeholder'])
                        
                        # 收集媒体文件
                        if block.type == 'image':
                            current_media_files['images'].append(block.content)
                        elif block.type == 'audio':
                            current_media_files['audios'].append(block.content)
                        elif block.type == 'video':
                            current_media_files['videos'].append(block.content)
                    elif block.type == 'json':
                        # JSON数据转为文本描述
                        json_text = f"数据: {json.dumps(block.content, ensure_ascii=False)}"
                        content_parts.append(json_text)
                
                current_message_content = "".join(content_parts)
            else:
                # 简单文本内容
                current_message_content = str(message.content)
            
            # 添加消息
            result['messages'].append({
                'role': message.role,
                'content': current_message_content
            })
            
            # 如果是助手消息，表示一轮对话结束，保存媒体文件
            if message.role == 'assistant':
                if current_media_files['images']:
                    result['images'].extend(current_media_files['images'])
                if current_media_files['audios']:
                    result['audios'].extend(current_media_files['audios'])
                if current_media_files['videos']:
                    result['videos'].extend(current_media_files['videos'])
                
                # 重置媒体文件收集器
                current_media_files = {'images': [], 'audios': [], 'videos': []}
        
        # 清理空的媒体数组
        if not result['images']:
            del result['images']
        if not result['audios']:
            del result['audios']
        if not result['videos']:
            del result['videos']
            
        return result
    
    def export_conversation(self, conversation_file: str, output_file: str = None) -> bool:
        """导出单个对话为 LLaMA-Factory 格式"""
        conversation = self.load_conversation(conversation_file)
        if not conversation:
            return False
        
        llamafactory_data = self.convert_to_llamafactory_format(conversation)
        
        # 确定输出文件名
        if not output_file:
            base_name = Path(conversation_file).stem
            output_file = f"{base_name}_llamafactory.json"
        
        try:
            output_path = self.conversations_dir / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump([llamafactory_data], f, ensure_ascii=False, indent=2)
            
            print(f"✅ 导出成功: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False
    
    def export_all_conversations(self, output_file: str = "exported_conversations.json") -> bool:
        """导出所有对话为单个 LLaMA-Factory 格式文件"""
        all_conversations = []
        
        # 遍历所有对话文件
        for file_path in self.conversations_dir.glob("*.json"):
            if file_path.name.endswith("_llamafactory.json"):
                continue  # 跳过已导出的文件
                
            conversation = self.load_conversation(file_path.name)
            if conversation:
                llamafactory_data = self.convert_to_llamafactory_format(conversation)
                all_conversations.append(llamafactory_data)
                print(f"📄 处理: {file_path.name}")
        
        if not all_conversations:
            print("❌ 没有找到可导出的对话记录")
            return False
        
        try:
            output_path = self.conversations_dir / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(all_conversations, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 批量导出成功: {output_path}")
            print(f"📊 导出对话数量: {len(all_conversations)}")
            return True
            
        except Exception as e:
            print(f"❌ 批量导出失败: {e}")
            return False
    
    def list_conversations(self) -> List[str]:
        """列出所有可用的对话文件"""
        conversations = []
        for file_path in self.conversations_dir.glob("*.json"):
            if not file_path.name.endswith("_llamafactory.json"):
                conversations.append(file_path.name)
        return sorted(conversations)


def main():
    """命令行工具主函数"""
    import sys
    
    exporter = MultimodalExporter()
    
    if len(sys.argv) < 2:
        print("📚 多模态对话导出工具")
        print("=" * 40)
        print("用法:")
        print("  python export_tools.py list                    # 列出所有对话")
        print("  python export_tools.py export <file>           # 导出单个对话")
        print("  python export_tools.py export-all              # 导出所有对话")
        print()
        
        # 显示可用对话
        conversations = exporter.list_conversations()
        if conversations:
            print(f"📄 可用对话文件 ({len(conversations)} 个):")
            for i, conv in enumerate(conversations[:5], 1):
                print(f"  {i}. {conv}")
            if len(conversations) > 5:
                print(f"  ... 和其他 {len(conversations) - 5} 个文件")
        else:
            print("❌ 没有找到对话文件")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        conversations = exporter.list_conversations()
        print(f"📄 对话文件列表 ({len(conversations)} 个):")
        for conv in conversations:
            print(f"  - {conv}")
            
    elif command == "export" and len(sys.argv) >= 3:
        file_name = sys.argv[2]
        output_file = sys.argv[3] if len(sys.argv) >= 4 else None
        exporter.export_conversation(file_name, output_file)
        
    elif command == "export-all":
        output_file = sys.argv[2] if len(sys.argv) >= 3 else "exported_conversations.json"
        exporter.export_all_conversations(output_file)
        
    else:
        print("❌ 无效的命令")


if __name__ == "__main__":
    main()
