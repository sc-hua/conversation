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
        if conversations_dir is None:
            conversations_dir = os.getenv("HISTORY_SAVE_DIR", "./log/conv_log/draft")
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
                            extras=block.get('extras', {})
                        ))
                else:
                    # 简单文本内容
                    content = msg_data['content']
                
                messages.append(Message(
                    msg_id=msg_data['msg_id'],
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
            # 优先使用 resolved_path，如果没有则使用原始 content
            resolved_path = content_block.get_extra('resolved_path')
            media_info['file_path'] = resolved_path if resolved_path else content_block.content
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
                        
                        # 收集媒体文件，使用实际的文件路径
                        file_path = media_info['file_path']
                        if block.type == 'image':
                            current_media_files['images'].append(file_path)
                        elif block.type == 'audio':
                            current_media_files['audios'].append(file_path)
                        elif block.type == 'video':
                            current_media_files['videos'].append(file_path)
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
    
    def export_conversation(self, conversation_file: str, output_file: str = None, output_dir: str = None) -> bool:
        """导出单个对话为 LLaMA-Factory 格式
        
        Args:
            conversation_file: 对话文件名
            output_file: 输出文件名，如果未指定则自动生成
            output_dir: 输出目录，如果未指定则使用对话目录
        """
        conversation = self.load_conversation(conversation_file)
        if not conversation:
            return False
        
        llamafactory_data = self.convert_to_llamafactory_format(conversation)
        
        # 确定输出目录
        if output_dir:
            output_directory = Path(output_dir)
            output_directory.mkdir(parents=True, exist_ok=True)
        else:
            output_directory = self.conversations_dir
        
        # 确定输出文件名
        if not output_file:
            base_name = Path(conversation_file).stem
            output_file = f"{base_name}_llamafactory.json"
        
        try:
            output_path = output_directory / output_file
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump([llamafactory_data], f, ensure_ascii=False, indent=2)
            
            print(f"✅ 导出成功: {output_path}")
            return True
            
        except Exception as e:
            print(f"❌ 导出失败: {e}")
            return False
    
    def export_all_conversations(self, output_file: str = "exported_conversations.json", output_dir: str = None) -> bool:
        """导出所有对话为单个 LLaMA-Factory 格式文件
        
        Args:
            output_file: 输出文件名
            output_dir: 输出目录，如果未指定则使用对话目录
        """
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
        
        # 确定输出目录
        if output_dir:
            output_directory = Path(output_dir)
            output_directory.mkdir(parents=True, exist_ok=True)
        else:
            output_directory = self.conversations_dir
        
        try:
            output_path = output_directory / output_file
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
    
    def preview_conversation(self, conversation_file: str) -> None:
        """预览对话转换结果"""
        conversation = self.load_conversation(conversation_file)
        if not conversation:
            return
        
        print(f"📄 对话预览: {conversation_file}")
        print(f"🆔 对话ID: {conversation.conv_id}")
        print(f"📅 创建时间: {conversation.created_at}")
        print(f"💬 消息数量: {len(conversation.messages)}")
        print()
        
        # 显示消息概览
        for i, message in enumerate(conversation.messages, 1):
            content_preview = ""
            if isinstance(message.content, Content):
                parts = []
                for block in message.content.blocks:
                    if block.type == 'text':
                        text = str(block.content)[:50]
                        if len(str(block.content)) > 50:
                            text += "..."
                        parts.append(text)
                    elif block.type == 'image':
                        parts.append(f"[图片: {block.content}]")
                    elif block.type == 'json':
                        parts.append(f"[JSON数据]")
                content_preview = " ".join(parts)
            else:
                content_preview = str(message.content)[:100]
                if len(str(message.content)) > 100:
                    content_preview += "..."
            
            print(f"{i}. {message.role}: {content_preview}")
        
        print()
        
        # 显示转换后的格式
        llamafactory_data = self.convert_to_llamafactory_format(conversation)
        print("🔄 LLaMA-Factory 格式预览:")
        print(f"  消息数量: {len(llamafactory_data['messages'])}")
        if 'images' in llamafactory_data:
            print(f"  图片文件: {len(llamafactory_data['images'])} 个")
            for img in llamafactory_data['images']:
                print(f"    - {img}")
        if 'audios' in llamafactory_data:
            print(f"  音频文件: {len(llamafactory_data['audios'])} 个")
        if 'videos' in llamafactory_data:
            print(f"  视频文件: {len(llamafactory_data['videos'])} 个")
        print()


def main():
    """命令行工具主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="📚 多模态对话导出工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python export_tools.py list
  python export_tools.py preview conv.json
  python export_tools.py export conv.json --output_file output.json --output_dir ./exports
  python export_tools.py export-all --output_file all_convs.json --output_dir ./exports
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出所有对话文件')
    
    # preview 命令
    preview_parser = subparsers.add_parser('preview', help='预览对话转换结果')
    preview_parser.add_argument('file', help='对话文件名')
    
    # export 命令
    export_parser = subparsers.add_parser('export', help='导出单个对话')
    export_parser.add_argument('file', help='对话文件名')
    export_parser.add_argument('--output_file', help='输出文件名（可选，默认自动生成）')
    export_parser.add_argument('--output_dir', help='输出目录（可选，默认为对话目录）')
    
    # export-all 命令
    export_all_parser = subparsers.add_parser('export-all', help='导出所有对话')
    export_all_parser.add_argument('--output_file', default='exported_conversations.json', help='输出文件名（默认: exported_conversations.json）')
    export_all_parser.add_argument('--output_dir', help='输出目录（可选，默认为对话目录）')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        print()
        
        # 显示可用对话
        exporter = MultimodalExporter()
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
    
    exporter = MultimodalExporter()
    
    if args.command == "list":
        conversations = exporter.list_conversations()
        print(f"📄 对话文件列表 ({len(conversations)} 个):")
        for conv in conversations:
            print(f"  - {conv}")
            
    elif args.command == "preview":
        exporter.preview_conversation(args.file)
        
    elif args.command == "export":
        exporter.export_conversation(args.file, args.output_file, args.output_dir)
        
    elif args.command == "export-all":
        exporter.export_all_conversations(args.output_file, args.output_dir)


if __name__ == "__main__":
    main()
