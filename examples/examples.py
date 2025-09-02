"""简洁示例和实用函数，演示结构化内容定位与使用模式。"""

import asyncio

from conversation.core import ConversationGraph, Content


class ConversationBuilder:
    """构建器：生成演示用的多轮对话与结构化内容。"""
    
    def __init__(self):
        """初始化 ConversationGraph 实例。"""
        self.graph = ConversationGraph()
    
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
            {'image': "user_behavior_dashboard.png"},
            "请提供初步分析。"
        )
        
        result1 = await self.graph.chat(
            system_prompt="你是资深用户行为分析师，擅长从多模态数据中提取洞见。",
            content=intro_content,
        )
        
        conv_id = result1['conv_id']
        print(f"初步分析: {result1['response']}\n")
        
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
            {'image': "conversion_funnel.png"},
            {'image': "engagement_timeline.png"},
            "你的建议是什么？"
        )
        
        result2 = await self.graph.chat(
            conv_id=conv_id,
            content=metrics_content
        )
        
        print(f"最终建议: {result2['response']}")
        
        # 结束对话并保存
        await self.graph.end(conv_id, save=True)
        return conv_id
    
    async def create_product_presentation(self) -> str:
        """示例：创建产品演示对话并返回 conv_id。"""
        print("🚀 创建产品演示...")
        presentation_content = Content(
            "新品发布演示",
            {'image': "product_hero_image.jpg"},
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
            "市场分析图：",
            {'image': "market_analysis.png"},
            "请生成一份有吸引力的产品摘要。"
        )

        result = await self.graph.chat(
            system_prompt="你是产品营销专家，负责撰写有吸引力的演示文案。",
            content=presentation_content
        )

        print(f"产品摘要: {result['response']}")
        
        # 结束对话并保存
        await self.graph.end(result['conv_id'], save=True)
        return result['conv_id']


async def demonstrate_custom_fields():
    """演示自定义字段功能：为内容块添加额外属性。"""
    print("🎨 演示自定义字段功能...")
    
    graph = ConversationGraph()
    
    # 创建带自定义字段的内容 - 按添加顺序排列
    content = Content()
    
    # 文本块带样式信息
    content.add_text(
        "重要通知", 
        style="bold", 
        color="red", 
        importance="high"
    )
    
    # 图片块带描述信息
    content.add_image(
        "dashboard.png", 
        alt_text="数据分析仪表板",
        width=800,
        height=600,
        caption="2024年度销售数据概览"
    )
    
    # JSON块带源信息
    content.add_json(
        {"sales": 150000, "growth": "12%"}, 
        schema_version="v1.2",
        validated=True,
        source="财务系统"
    )
    
    # 演示增强的显示功能
    print(f"增强显示: {content.to_display_text()}")
    
    # 演示自定义字段访问
    print("\n自定义字段详情:")
    for i, block in enumerate(content.blocks):
        print(f"块 {i} ({block.type}): {block.content}")
        if block.extras:
            for key, value in block.extras.items():
                print(f"  {key}: {value}")
    
    result = await graph.chat(content=content)
    print(f"\n对话结果: {result['response']}")
    
    return result['conv_id']


async def demonstrate_positioning_control():
    """演示内容构造：顺序添加和插入操作示例。"""
    print("🎯 演示内容构造功能...")
    
    # 使用配置好的环境中的 LLM 类型
    graph = ConversationGraph()
    
    # 测试用例 1: 顺序添加
    content1 = Content()
    content1.add_text("第一项")
    content1.add_text("第二项")
    content1.add_image("middle_image.png")
    content1.add_json({"data": "第四项"})
    
    result1 = await graph.chat(content=content1)
    print(f"顺序添加: {result1['input_preview']}")
    
    # 测试用例 2: 使用工厂方法
    content2 = Content(
        "引言",
        {'image': 'diagram.png'},
        {'json': {'metrics': [1, 2, 3]}},
        ("结论", {'style': 'bold'}),  # 带自定义字段
        "中间部分"
    )
    
    result2 = await graph.chat(content=content2)
    print(f"工厂方法结果: {result2['input_preview']}")
    
    # 测试用例 3: 演示插入操作
    content3 = Content()
    content3.add_text("开始")
    content3.add_text("结束")
    # 在中间插入内容
    content3.insert_text(1, "中间插入的文本")
    content3.insert_image(2, "inserted_image.png")
    
    result3 = await graph.chat(content=content3)
    print(f"插入操作结果: {result3['input_preview']}")


async def batch_conversation_processing():
    """批量并发示例，展示并发限制下的多会话处理。"""
    print("🔥 批量会话并发测试...")
    
    graph = ConversationGraph(max_concurrent=3)
    
    # 创建多个对话请求
    tasks = []
    for i in range(5):
        content = Content(
            f"处理任务 #{i+1}",
            {'json': {"task_id": i+1, "priority": "high" if i % 2 == 0 else "normal"}},
            "请分析并回复"
        )

        task = graph.chat(
            system_prompt=f"你是 AI 助手 #{i+1}",
            content=content,
        )
        tasks.append(task)
    
    # Execute all conversations concurrently
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    end_time = asyncio.get_event_loop().time()
    
    print(f"✅ 已处理 {len(results)} 个会话，耗时 {end_time - start_time:.2f} 秒")
    for i, result in enumerate(results):
        print(f"  会话 {i+1}: {result['conv_id'][:8]}...")


async def main():
    """运行所有演示场景的主函数。"""
    print("🤖 LangGraph 对话系统演示")
    print("=" * 60)
    
    builder = ConversationBuilder()
    
    # 运行不同的演示场景
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
    
    print("\n✅ 所有演示完成！")


if __name__ == "__main__":
    asyncio.run(main())
