# 统一加载环境变量，避免重复调用
from dotenv import load_dotenv

def load_env():
    load_dotenv()