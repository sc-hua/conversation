# LangGraph 多轮对话系统

基于 LangGraph 构建的高性能结构化内容对话系统，支持精确的多模态内容定位和对话管理。

## ⚡ 快速体验

```bash
# 零依赖快速体验 - 推荐！
python main.py

# 或完整功能体验
pip install -r requirements.txt && python examples.py
```

## 🌟 核心创新

我们解决了传统聊天系统的关键痛点：**无法精确控制多模态内容的位置**

<details>
<summary><b>📖 传统方式 vs 我们的创新（点击展开）</b></summary>

### ❌ 传统方式的局限
```python
# 固定顺序：文本 → 图片 → JSON，无法自定义
await chat(text="分析这个", images=["chart.png"], json_data={"metric": 95})
```

### ✅ 我们的创新方案
```python
# 🎯 精确位置控制 - 内容可以任意顺序排列！
content = (StructuredMessageContent()
           .add_text("首先查看概述图表", 0)
           .add_image("overview.png", 1)
           .add_text("关键指标分析", 2)  
           .add_json({"revenue": 1000000, "growth": "15%"}, 3)
           .add_text("详细趋势见下图", 4)
           .add_image("trend.png", 5))

await graph.chat(structured_content=content)
```

</details>

## 🎯 核心功能

✅ **结构化内容定位** - 精确控制文本、图片和JSON在消息中的位置  
✅ **系统提示词支持** - 对话开始时设置AI行为和角色  
✅ **多轮对话管理** - 自动历史管理和上下文保持  
✅ **数据持久化** - 完整的结构化对话存储到JSON文件  
✅ **高并发支持** - 异步处理，可配置并发限制  
✅ **零依赖运行** - 独立版本仅需Python标准库  

## 📦 项目结构

```
process_data/
├── main.py                    # 🔥 零依赖独立版本（推荐入门）
├── models.py                  # 数据模型定义
├── conversation_manager.py    # 对话管理和文件持久化
├── conversation_graph.py      # LangGraph工作流核心
├── examples.py                # 使用示例和工具函数
├── requirements.txt           # 完整版依赖列表
├── .env                       # 环境配置文件
└── README.md                  # 项目文档
```

## 💻 基础使用

### 简单示例
```python
from main import StandaloneConversationGraph, StructuredMessageContent

# 初始化
graph = StandaloneConversationGraph()

# 创建结构化内容
content = (StructuredMessageContent()
           .add_text("请分析这些数据", 0)
           .add_json({"销售额": [100, 200, 150]}, 1)
           .add_text("并提供见解", 2))

# 发送消息
result = await graph.chat(
    system_prompt="你是数据分析专家",
    structured_content=content
)

print(f"AI响应: {result['response']}")
```

## 🚀 高级功能

<details>
<summary><b>🎯 多轮对话管理</b></summary>

```python
# 第一轮对话
response1 = await graph.chat(
    structured_content=content1,
    conversation_id="session_123"
)

# 第二轮对话 - 自动保持上下文
response2 = await graph.chat(
    structured_content=content2,
    conversation_id="session_123"  # 相同ID，自动继续对话
)

# 查看完整历史
history = graph.manager.get_conversation_history("session_123")
```

</details>

<details>
<summary><b>⚡ 高并发批量处理</b></summary>

```python
import asyncio

async def process_multiple_conversations():
    tasks = []
    
    # 创建10个并发对话任务
    for i in range(10):
        task = graph.chat(
            structured_content=create_content_for_task(i),
            conversation_id=f"batch_task_{i}"
        )
        tasks.append(task)
    
    # 并发执行，最多5个同时进行
    results = await asyncio.gather(*tasks)
    return results

# 运行批量处理
results = await process_multiple_conversations()
```

</details>

<details>
<summary><b>💾 数据持久化</b></summary>

```python
# 对话自动保存到JSON文件
conversation_id = "important_meeting_001"
await graph.chat(content, conversation_id=conversation_id)

# 手动保存到文件
file_path = await graph.manager.save_conversation_to_file(conversation_id)
print(f"对话已保存到: {file_path}")

# 保存的文件格式
{
    "conversation_id": "important_meeting_001",
    "system_prompt": "你是专业分析师...",
    "messages": [
        {
            "id": "msg_001", 
            "role": "user",
            "content": {...},  # 结构化内容
            "timestamp": "2025-08-28T10:30:00"
        }
    ],
    "created_at": "2025-08-28T10:30:00",
    "updated_at": "2025-08-28T10:35:00"
}
```

</details>

## 🎨 实际应用场景

<details>
<summary><b>📊 数据分析报告</b></summary>

```python
# 分析报告内容构建
report_content = (StructuredMessageContent()
    .add_text("📈 Q3业绩总览", 0)
    .add_image("q3_overview.png", 1)
    .add_text("核心指标：", 2)
    .add_json({
        "总收入": "¥5200万",
        "同比增长": "+12.5%",
        "净利润率": "18.3%",
        "客户增长": "+8.7%"
    }, 3)
    .add_text("市场分析：", 4)
    .add_image("market_analysis.png", 5)
    .add_text("下季度预测：", 6)
    .add_json({
        "预期收入": "¥5850万",
        "增长目标": "+12.5%",
        "风险因素": ["市场竞争", "成本上升"]
    }, 7))

# 设置专业分析师角色
analyst_prompt = """你是资深商业分析师，请基于提供的数据和图表，
给出专业的分析意见和建议。重点关注：
1. 关键趋势识别
2. 风险机会评估  
3. 具体行动建议"""

response = await graph.chat(
    structured_content=report_content,
    system_prompt=analyst_prompt
)
```

</details>

<details>
<summary><b>🚀 产品展示</b></summary>

```python
from examples import create_mixed_content

# 使用便捷函数创建内容
content = create_mixed_content(
    "🚀 新产品发布",
    {"image": "product_hero.jpg"},
    "产品特性：",
    {"json": {"price": "$299", "availability": "现货"}},
    "用户评价：",
    {"image": "customer_reviews.png"}
)
```

</details>

## 🔧 技术架构

<details>
<summary><b>📐 系统架构图</b></summary>

### LangGraph 工作流
```
用户输入 → [处理节点] → [生成节点] → [保存节点] → 返回结果
           ↓           ↓           ↓
        内容解析    AI生成响应   持久化存储
```

### 核心组件说明

| 组件 | 功能 | 特色 |
|------|------|------|
| `StructuredMessageContent` | 内容结构化管理 | 精确位置控制 |
| `ConversationManager` | 对话状态管理 | 内存+文件双重存储 |
| `ConversationGraph` | LangGraph工作流 | 三节点异步处理 |
| `MockLLM` | 模拟语言模型 | 测试和演示用 |

### 异步并发控制
- 基于 `asyncio.Semaphore` 的并发限制
- 默认最大并发数：5个对话
- 支持自定义并发参数

</details>

## ⚙️ 环境配置

<details>
<summary><b>🔐 .env 文件配置</b></summary>

```bash
# OpenAI API (如果使用真实LLM)
OPENAI_API_KEY=your_api_key_here

# 对话保存路径
CONVERSATION_SAVE_PATH=./conversations

# 并发限制
MAX_CONCURRENT_CONVERSATIONS=5

# 调试模式
DEBUG_MODE=true
```

### 依赖说明

#### 零依赖版本 (main.py)
- 仅使用Python标准库
- 包含MockLLM用于演示
- 适合快速测试和学习

#### 完整版本依赖
```bash
pip install langgraph>=0.0.45     # LangGraph核心
pip install langchain-core>=0.1.20  # LangChain基础
pip install pydantic>=2.0.0      # 数据验证
pip install aiofiles>=23.2.0     # 异步文件操作
```

</details>

## ❓ 常见问题

<details>
<summary><b>🤔 FAQ</b></summary>

### Q: 为什么需要结构化内容定位？
A: 传统聊天系统中，多模态内容（文本、图片、JSON）的顺序是固定的，无法实现精确的内容编排。我们的方案允许您像编辑文档一样精确控制每个元素的位置。

### Q: 独立版本和完整版本有什么区别？
A: 
- **独立版本** (`main.py`): 零依赖，使用MockLLM，适合学习和测试
- **完整版本**: 支持真实LLM接入，完整的异步文件操作，适合生产环境

### Q: 如何处理大量并发对话？
A: 系统内置异步并发控制，默认支持5个并发对话。可通过配置调整并发数量：
```python
graph = ConversationGraph(max_concurrent=10)
```

### Q: 对话数据如何备份？
A: 每个对话都会自动保存到 `./conversations/` 目录下的JSON文件，文件名格式为 `conversation_{id}_{timestamp}.json`

</details>

## 🎯 最佳实践

<details>
<summary><b>💡 使用建议</b></summary>

1. **内容组织**: 使用结构化内容时，合理规划文本、图片、JSON的顺序
2. **系统提示词**: 明确设定AI角色和期望的回答风格
3. **对话ID管理**: 使用有意义的conversation_id便于后续管理
4. **并发控制**: 根据系统资源合理设置并发数量
5. **错误处理**: 在生产环境中添加适当的异常处理

### 位置规划示例
```python
# 使用间隔便于插入
.add_text("引言", 0)
.add_text("主要内容", 10)  # 留出插入空间
.add_text("结论", 20)

# 用位置范围分组相关内容
# 引言: 0-9, 分析: 10-19, 结果: 20-29, 结论: 30-39
```

</details>

---

## 🎉 为什么选择我们？

1. **🎯 精确控制** - 将内容精确定位到需要的位置
2. **🚀 高性能** - 带并发控制的异步处理  
3. **💾 可靠存储** - 完整的对话持久化
4. **🔧 易于集成** - 简单API配合全面示例
5. **📦 零依赖** - 独立版本便于部署
6. **🔄 向后兼容** - 与现有对话模式配合使用

## 📄 许可证

MIT License - 欢迎使用和贡献！

---

**立即开始体验强大的多模态对话系统！** 🚀
