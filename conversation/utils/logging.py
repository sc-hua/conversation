"""
简洁的日志模块 - 为对话系统提供必要的日志功能
"""

import os
import sys
import logging
import logging.handlers
from pathlib import Path
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
        # 为控制台添加颜色
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
            cls._instance._warned_messages = set()  # 存储已警告的消息
            cls._instance._setup()
        return cls._instance
    
    def _setup(self):
        """初始化日志配置"""
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        log_dir = Path(os.getenv("LOG_DIR", "./log"))
        log_dir.mkdir(parents=True, exist_ok=True)  # 添加parents=True
        log_path = log_dir / "conversation.log"
        
        # 主日志器
        self.logger = logging.getLogger("conversation")
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        if not self.logger.handlers:
            # 如果先处理 ColoredFormatter 的话，文件的输出会被染色，影响阅读，如 [31mERROR[0m
            # 文件输出（先处理，获得原始levelname）
            file_handler = logging.handlers.RotatingFileHandler(
                log_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
            )
            file_handler.setFormatter(RelativePathFormatter(
                '%(asctime)s | %(levelname)s | %(relative_path)s:%(lineno)d | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            ))
            self.logger.addHandler(file_handler)
            
            # 控制台输出（后处理，添加颜色）
            console = logging.StreamHandler(sys.stdout)
            console.setFormatter(ColoredFormatter(
                '%(asctime)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s',
                datefmt='%H:%M:%S'
            ))
            self.logger.addHandler(console)
        
        if not os.getenv("LOG_DIR", ""):
            self.warn_once(f"[Logger] | LOG_DIR env var not set, using {log_dir.absolute()}")

    def get_logger(self, name: str = None):
        """获取子模块日志器"""
        if name:
            return logging.getLogger(f"conversation.{name}")
        return self.logger
    
    def warn_once(self, message: str, logger_name: str = None):
        """只警告一次的功能，避免重复警告同一消息"""
        if message not in self._warned_messages:
            self._warned_messages.add(message)
            logger = self.get_logger(logger_name)
            logger.warning(message, stacklevel=3)
            # 使用 stacklevel=3，跳过: 
            # 1. logger.warning(), 当前位置
            # 2. Logger.warn_once(), 当前方法
            # 3. warn_once(), 全局函数


# 全局日志器
_logger = Logger()


def get_logger(name: str = None):
    """获取日志器"""
    return _logger.get_logger(name)


def warn_once(message: str, logger_name: str = None):
    """只警告一次，避免重复的警告消息
    
    Args:
        message: 警告消息内容
        logger_name: 日志器名称，不指定则使用默认日志器
    """
    return _logger.warn_once(message, logger_name)


def log_exception(func):
    """异常日志装饰器"""
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"[Sync function exception] | {func.__name__} | {str(e)}")
            raise
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        logger = get_logger()
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.error(f"[Async function exception] | {func.__name__} | {str(e)}")
            raise
    
    import asyncio
    return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper