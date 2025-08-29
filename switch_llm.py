#!/usr/bin/env python3
"""
LLM 类型切换器 - 用于在不同 LLM 类型之间方便切换的脚本。

用法:
    python switch_llm.py mock
    python switch_llm.py ollama
    python switch_llm.py openai
"""

import sys
import os
from pathlib import Path


def switch_llm_type(new_type):
    """在 .env 文件中切换 LLM 类型。"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("❌ 错误：未找到 .env 文件")
        return False
    
    # Valid LLM types
    valid_types = ['mock', 'ollama', 'openai']
    if new_type not in valid_types:
        print(f"❌ 错误：无效的 LLM 类型 '{new_type}'")
        print(f"可选类型：{', '.join(valid_types)}")
        return False
    
    # Read current .env file
    lines = []
    with open(env_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Update LLM_TYPE line
    updated = False
    for i, line in enumerate(lines):
        if line.startswith('LLM_TYPE='):
            lines[i] = f'LLM_TYPE={new_type}\n'
            updated = True
            break
    
    if not updated:
        # Add LLM_TYPE if not found
        lines.insert(1, f'LLM_TYPE={new_type}\n')
    
    # Write back to .env file
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    print(f"✅ LLM 类型已切换为: {new_type.upper()}")
    
    # Show current configuration
    if new_type == 'ollama':
        model = os.getenv('OLLAMA_MODEL', 'qwen2.5vl:3b')
        url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        print(f"   Model: {model}")
        print(f"   URL: {url}")
    elif new_type == 'openai':
        model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
        url = os.getenv('OPENAI_BASE_URL', 'https://api.openai.com/v1')
        print(f"   Model: {model}")
        print(f"   URL: {url}")
        api_key = os.getenv('OPENAI_API_KEY', 'your_openai_api_key_here')
        if api_key == 'your_openai_api_key_here':
            print("   ⚠️  Warning: Please set OPENAI_API_KEY in .env file")
    
    return True


def show_usage():
    """显示使用说明。"""
    print("LLM 类型切换器")
    print("=" * 30)
    print("用法: python switch_llm.py <type>")
    print()
    print("Available types:")
    print("  mock   - 用于测试的 Mock LLM（无需外部依赖）")
    print("  ollama - Ollama qwen2.5vl:3b（需运行 Ollama）")
    print("  openai - OpenAI GPT 系列模型（需配置 API Key）")
    print()
    print("Examples:")
    print("  python switch_llm.py mock")
    print("  python switch_llm.py ollama")
    print("  python switch_llm.py openai")


def main():
    """主函数。"""
    if len(sys.argv) != 2:
        show_usage()
        return
    
    new_type = sys.argv[1].lower()
    
    if new_type in ['-h', '--help', 'help']:
        show_usage()
        return
    
    success = switch_llm_type(new_type)
    
    if success:
        print()
        print("🚀 现在可以测试对话系统了：")
        print("   python test_llm.py")
        print("   python test_ollama_chat.py")
        print("   python examples.py")


if __name__ == "__main__":
    main()
