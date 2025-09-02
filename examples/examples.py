"""简洁示例和实用函数，演示结构化内容定位与使用模式。"""

import asyncio
import os
import time
from dotenv import load_dotenv
load_dotenv()

# 然后导入conversation模块
from conversation.core import ConversationGraph, Content
from conversation.utils import get_logger
logger = get_logger(__name__)


class ConversationBuilder:
    """构建器：生成演示用的多轮对话与结构化内容。"""
    
    def __init__(self, llm_name: str = None):
        """初始化图实例，默认使用mock模型"""
        if llm_name is None:
            # 简单判断，优先使用mock避免网络依赖
            llm_name = 'mock'
            print("使用 Mock 模型进行演示（轻量级测试）")
        
        self.graph = ConversationGraph(llm=llm_name)
    
    async def create_data_analysis_conversation(self) -> str:
        """示例：创建一轮数据分析对话并返回 conv_id。"""
        print("📊 创建数据分析对话...")
        
        # 第一条消息：带结构化数据的介绍
        intro_content = Content(
            "我需要分析以下用户数据。",
            "首先，这是用户基本信息：",
            {'json': {
                "user_id": "U12345",
                "name": "张敏", 
                "age": 28,
                "location": "旧金山"
            }},
            "这是他们的行为截图：",
            {'image': "test_image.jpg"},
            "请提供初步分析。"
        )
        
        result1 = await self.graph.chat(
            system_prompt="你是资深用户行为分析师，擅长从多模态数据中提取洞见。",
            content=intro_content,
        )
        
        conv_id = result1['conv_id']
        print(f"初步分析: {result1['response'][:100]}...")
        
        # 后续详细指标
        metrics_content = Content(
            "根据你的分析，以下是详细指标：",
            {'json': {
                "sessions": [
                    {"date": "2025-01-01", "duration": 45, "pages": 12},
                    {"date": "2025-01-02", "duration": 32, "pages": 8}
                ],
                "conversion_rate": 0.15,
                "engagement_score": 8.5
            }},
            "以下是可视化图表：",
            {'image': "test_image.jpg"},
            "你的建议是什么？"
        )
        
        result2 = await self.graph.chat(
            conv_id=conv_id,
            content=metrics_content
        )
        
        print(f"最终建议: {result2['response'][:100]}...")
        
        # 结束对话并保存
        await self.graph.end(conv_id, save=True)
        return conv_id
    
    async def create_product_presentation(self) -> str:
        """示例：创建产品演示对话并返回 conv_id。"""
        print("🚀 创建产品演示...")
        presentation_content = Content(
            "新品发布演示",
            {'image': "test_image.jpg"},
            "主要功能：",
            {'json': {
                "features": [
                    "基于AI的推荐",
                    "实时协作",
                    "先进的分析能力"
                ],
                "target_audience": "企业客户"
            }},
            "技术规格：",
            {'json': {
                "performance": {
                    "response_time": "< 100ms",
                    "uptime": "99.9%",
                    "scalability": "1M+ 用户"
                }
            }},
            "请生成一份有吸引力的产品摘要。"
        )

        result = await self.graph.chat(
            system_prompt="你是产品营销专家，负责撰写有吸引力的演示文案。",
            content=presentation_content
        )

        print(f"产品摘要: {result['response'][:100]}...")
        
        # 结束对话并保存
        await self.graph.end(result['conv_id'], save=True)
        return result['conv_id']


async def demonstrate_custom_fields():
    """演示自定义字段功能：为内容块添加额外属性。"""
    print("🎨 演示自定义字段功能...")
    
    # 使用轻量级mock模型
    graph = ConversationGraph(llm='mock')
    
    # 创建带自定义字段的内容
    content = Content()
    content.add_text("重要通知", style="bold", importance="high")
    content.add_image("test_image.jpg", alt_text="测试图片", width=800)
    content.add_json({"sales": 150000, "growth": "12%"}, source="财务系统")
    
    print(f"内容预览: {content.to_display_text()}")
    
    # 显示自定义字段
    for i, block in enumerate(content.blocks):
        if block.extras:
            print(f"块{i} 自定义字段: {list(block.extras.keys())}")
    
    result = await graph.chat(content=content)
    print(f"对话结果: {result['response'][:50]}...")
    
    await graph.end(result['conv_id'], save=False)  # 不保存，简化流程
    return result['conv_id']


async def demonstrate_positioning_control():
    """演示内容构造：顺序添加操作示例。"""
    print("🎯 演示内容构造功能...")
    
    graph = ConversationGraph(llm='mock')
    
    # 测试1: 顺序添加
    content1 = Content()
    content1.add_text("开始").add_image("test_image.jpg").add_json({"test": 1})
    result1 = await graph.chat(content=content1)
    print(f"顺序添加: {result1['input_preview'][:50]}...")
    
    # 测试2: 工厂方法构造
    content2 = Content(
        "标题", 
        {'image': 'test_image.jpg'}, 
        {'json': {'data': 123}}
    )
    result2 = await graph.chat(content=content2)
    print(f"工厂方法: {result2['input_preview'][:50]}...")
    
    # 清理
    await graph.end(result1['conv_id'], save=False)
    await graph.end(result2['conv_id'], save=False)


async def batch_conversation_processing():
    """批量并发示例，轻量级并发测试。"""
    print("🔥 批量会话并发测试...")
    
    graph = ConversationGraph(llm='mock', max_concurrent=5)
    
    # 创建简化的测试任务
    tasks = []
    for i in range(3):  # 减少任务数量，提高效率
        content = Content(f"任务 #{i+1}: 简单计算", {'json': {"id": i+1}})
        task = graph.chat(system_prompt="简洁回答", content=content)
        tasks.append(task)
    
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start_time
    
    print(f"✅ 完成 {len(results)} 个会话，耗时 {elapsed:.2f}s")
    
    # 批量清理
    cleanup_tasks = [graph.end(r['conv_id'], save=False) for r in results]
    await asyncio.gather(*cleanup_tasks)


async def concurrent_inference_test():
    """
    简化的并发推理测试：测试基本的并发性能
    """
    print("🚀 并发推理测试...")
    
    # 测试不同的并发级别
    concurrent_levels = [1, 3, 5]
    
    for concurrent in concurrent_levels:
        print(f"\n📊 测试并发数: {concurrent}")
        
        graph = ConversationGraph(llm='mock', max_concurrent=concurrent)
        
        # 创建测试任务
        prompts = ["计算1+1", "解释AI", "写函数", "推荐书籍"]
        tasks = []
        
        start_time = time.time()
        for i, prompt in enumerate(prompts[:concurrent]):
            content = Content(f"任务{i+1}: {prompt}")
            task = graph.chat(content=content)
            tasks.append(task)
        
        # 执行并统计
        results = await asyncio.gather(*tasks, return_exceptions=True)
        elapsed = time.time() - start_time
        
        successful = [r for r in results if not isinstance(r, Exception)]
        
        print(f"  完成率: {len(successful)}/{len(results)}")
        print(f"  耗时: {elapsed:.2f}s")
        print(f"  吞吐: {len(successful)/elapsed:.1f} req/s")
        
        # 清理
        cleanup_tasks = [
            graph.end(r['conv_id'], save=False) 
            for r in successful if hasattr(r, 'get') and r.get('conv_id')
        ]
        if cleanup_tasks:
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)


async def multi_round_conversation_test():
    """多轮对话测试"""
    print("� 多轮对话测试...")
    
    graph = ConversationGraph(llm='mock')
    
    # 第一轮
    content1 = Content("你好，我叫张三")
    result1 = await graph.chat(system_prompt="记住用户信息", content=content1)
    conv_id = result1['conv_id']
    
    # 第二轮 - 测试记忆
    content2 = Content("我刚才说我叫什么？")
    result2 = await graph.chat(conv_id=conv_id, content=content2)
    
    # 第三轮 - 带结构化数据
    content3 = Content(
        "最后一个问题：",
        {'json': {"question": "总结对话", "round": 3}}
    )
    result3 = await graph.chat(conv_id=conv_id, content=content3)
    
    print(f"✅ 完成3轮对话，共{result3['message_count']}条消息")
    
    await graph.end(conv_id, save=True)  # 保存完整对话
    return conv_id


async def main():
    """运行所有演示场景的主函数。"""
    print("🤖 对话系统演示 (轻量版)")
    print("=" * 40)
    
    builder = ConversationBuilder()
    
    # 核心功能演示
    print("\n1️⃣ 数据分析场景:")
    await builder.create_data_analysis_conversation()
    
    print("\n2️⃣ 产品演示场景:")
    await builder.create_product_presentation()
    
    print("\n3️⃣ 自定义字段演示:")
    await demonstrate_custom_fields()
    
    print("\n4️⃣ 内容构造演示:")
    await demonstrate_positioning_control()
    
    print("\n5️⃣ 批量处理演示:")
    await batch_conversation_processing()
    
    print("\n6️⃣ 并发测试:")
    await concurrent_inference_test()
    
    print("\n7️⃣ 多轮对话测试:")
    await multi_round_conversation_test()
    
    print("\n✅ 演示完成！")


if __name__ == "__main__":
    asyncio.run(main())
