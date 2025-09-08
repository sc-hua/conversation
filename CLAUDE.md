# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 项目概述

这是一个基于 Python 的对话管理系统，使用 LangGraph 构建，为 LLM 对话提供结构化内容处理。系统支持多个 LLM 提供商（OpenAI、Ollama、Mock），并处理多模态内容，包括文本、图像和结构化数据。

## 核心架构组件

### 核心包结构
- `conversation/core/`: 核心对话引擎和状态管理
  - `graph.py`: 主要的 ConversationGraph 类，实现基于 LangGraph 的对话流程
  - `modules.py`: 数据模型（Content、ContentBlock、Message、ConversationState、History）
  - `manager.py`: 用于对话持久化的 HistoryManager
- `conversation/llm/`: LLM 提供商抽象层
  - `base.py`: BaseLLM 接口
  - `openai.py`: OpenAI 实现
  - `ollama.py`: Ollama 实现  
  - `mock.py`: 用于测试的 Mock LLM
- `conversation/utils/`: 工具模块
  - `logging.py`: 自定义日志记录，支持彩色控制台输出和文件轮转
  - `export_tools.py`: 对话导出功能
  - `image_utils.py`: 图像处理工具
  - `id_utils.py`: ID 生成工具

### 核心概念
- **Content**: ContentBlock 对象的结构化集合，支持混合内容类型
- **ContentBlock**: 支持扩展元数据的单个内容单元（文本、图像、json）
- **ConversationGraph**: 使用 LangGraph 进行对话状态管理的主要协调器
- **HistoryManager**: 处理对话持久化和检索
- **Structured Output**: 支持 LLM 响应中的 Pydantic 模型

## 开发命令

### 环境设置
```bash
# 安装依赖（自动检测 conda/venv）
./install.sh

# 或手动安装：
pip install -e .
```

### 测试
```bash
# 运行基本对话测试
python examples/test.py

# 开发快速测试
python examples/quick_test.py

# 测试结构化输出功能  
python examples/structured_output_test.py

# 并发处理测试
python examples/concurrent_test.py

# 模板测试（新测试模式）
python examples/test_template.py
```

### LLM 提供商选择
设置 `LLM_NAME` 环境变量：
- `mock`: Mock LLM（默认，无需 API 密钥）
- `openai`: OpenAI API（需要 `OPENAI_API_KEY`）
- `ollama`: Ollama 本地模型

## 配置

### 环境变量
- `LLM_NAME`: LLM 提供商（默认："mock"）
- `OPENAI_API_KEY`: OpenAI API 密钥
- `LOG_LEVEL`: 日志级别（默认："INFO"）
- `LOG_DIR`: 日志目录（默认："./log"）

### 使用示例
```python
from conversation.core import Content, ConversationGraph

# 使用特定 LLM 初始化
graph = ConversationGraph(llm="openai")

# 创建结构化内容
content = Content("你好", {"image": "url"}, {"json": data})

# 带结构化输出的聊天
response = await graph.chat(content, return_history=True)
```

## 重要模式

### 内容创建
Content 对象支持灵活的初始化：
- 字符串成为文本块
- 带有 'image'/'json' 键的字典成为类型化块
- (content, extras) 元组添加元数据

### 错误处理
- 对异步/同步函数使用 `@log_exception` 装饰器
- 日志系统提供彩色控制台输出和文件轮转
- 使用 `warn_once()` 进行警告抑制，避免重复消息

### 并发
- ConversationGraph 包含内置信号量用于并发请求限制
- 默认 max_concurrent=5，可按实例配置

### 测试策略
- 示例既作为文档也作为测试
- Mock LLM 提供无需 API 调用的确定性测试
- 测试文件在 examples/ 目录中使用描述性命名模式