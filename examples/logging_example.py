#!/usr/bin/env python3
"""简洁的日志系统使用示例"""

import asyncio
import os
from conversation.utils.logging import get_logger, log_exception

# 获取日志器
logger = get_logger()
chat_logger = get_logger("chat")
file_logger = get_logger("file")


def basic_example():
    """基础使用示例"""
    print("\n=== 基础日志示例 ===")
    logger.debug("调试信息")
    logger.info("程序开始运行")
    logger.warning("这是一个警告")
    logger.error("这是一个错误")


@log_exception
def normal_function():
    """带异常处理的普通函数"""
    logger.info("执行普通函数")
    return "成功"


@log_exception  
async def async_function():
    """带异常处理的异步函数"""
    logger.info("执行异步函数")
    await asyncio.sleep(0.1)
    return "异步成功"


def module_example():
    """多模块日志示例"""
    print("\n=== 模块日志示例 ===")
    chat_logger.info("聊天模块：处理用户消息")
    file_logger.info("文件模块：保存对话")


async def conversation_example():
    """对话系统使用示例"""
    print("\n=== 对话系统示例 ===")
    
    conv_id = "test_123"
    logger.info(f"对话开始 | conv_id={conv_id}")
    
    # 模拟LLM调用
    llm_logger = get_logger("llm")
    llm_logger.info("调用OpenAI API")
    
    await asyncio.sleep(0.2)  # 模拟网络请求
    
    llm_logger.info("API调用成功 | tokens=150")
    logger.info(f"对话结束 | conv_id={conv_id}")


async def main():
    """运行所有示例"""
    print("🚀 日志系统示例")
    
    basic_example()
    normal_function()
    await async_function()
    module_example() 
    await conversation_example()
    
    print("\n✅ 示例完成，查看 ./logs/conversation.log")


if __name__ == "__main__":
    # 设置DEBUG级别查看所有日志
    os.environ["LOG_LEVEL"] = "DEBUG"
    asyncio.run(main())
