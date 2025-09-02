"""
简洁的日志模块 - 为对话系统提供必要的日志功能
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
from typing import Optional
from functools import wraps


def get_relative_path(pathname):
    """获取相对于项目根目录的相对路径"""
    try:
        # 获取项目根目录（conversation 包的上级目录）
        current_dir = Path(__file__).parent.parent.parent  # logging.py -> utils -> conversation -> project_root
        relative_path = Path(pathname).relative_to(current_dir)
        return str(relative_path)
    except ValueError:
        # 如果无法计算相对路径，返回文件名
        return Path(pathname).name


class ColoredFormatter(logging.Formatter):
    """控制台彩色输出格式化器"""
    COLORS = {
        'DEBUG': '\033[36m', 'INFO': '\033[32m', 'WARNING': '\033[33m',
        'ERROR': '\033[31m', 'CRITICAL': '\033[35m', 'ENDC': '\033[0m'
    }
    
    def format(self, record):
        if record.levelname in self.COLORS:
            record.levelname = f"{self.COLORS[record.levelname]}{record.levelname}{self.COLORS['ENDC']}"
        # 添加相对路径字段
        record.relative_path = get_relative_path(record.pathname)
        return super().format(record)


class RelativePathFormatter(logging.Formatter):
    """支持相对路径的文件格式化器"""
    
    def format(self, record):
        # 添加相对路径字段
        record.relative_path = get_relative_path(record.pathname)
        return super().format(record)


class Logger:
    """简化的日志器"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._setup()
        return cls._instance
    
    def _setup(self):
        """初始化日志配置"""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        log_dir = Path(os.getenv("LOG_DIR"))
        
        # 创建目录
        log_dir.mkdir(parents=True, exist_ok=True)  # 添加parents=True
        
        # 主日志器
        self.logger = logging.getLogger("conversation")
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        if not self.logger.handlers:
            # 控制台输出
            console = logging.StreamHandler(sys.stdout)
            console.setFormatter(ColoredFormatter(
                '%(asctime)s | %(levelname)-8s | %(filename)s:%(lineno)d | %(message)s',
                datefmt='%H:%M:%S'
            ))
            self.logger.addHandler(console)
            
            # 文件输出
            file_handler = logging.handlers.RotatingFileHandler(
                log_dir / "conversation.log", maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
            )
            file_handler.setFormatter(RelativePathFormatter(
                '%(asctime)s | %(levelname)-8s | %(relative_path)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            self.logger.addHandler(file_handler)
    
    def get_logger(self, name: str = None):
        """获取子模块日志器"""
        if name:
            return logging.getLogger(f"conversation.{name}")
        return self.logger


# 全局日志器
_logger = Logger()


def get_logger(name: str = None):
    """获取日志器"""
    return _logger.get_logger(name)


def log_exception(func):
    """异常日志装饰器"""
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"函数异常 | {func.__name__} | {str(e)}")
            raise
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"异步函数异常 | {func.__name__} | {str(e)}")
            raise
    
    import asyncio
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper