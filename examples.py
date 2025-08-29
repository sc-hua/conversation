"""
增强对话系统的综合示例和实用程序。

本模块提供实用示例、辅助函数和
结构化内容定位功能的常用模式。
"""

import asyncio
from conversation_graph import ConversationGraph
from models import StructuredMessageContent


def create_mixed_content(*items) -> StructuredMessageContent:
    """
    从混合项目创建结构化内容的辅助函数。
    
    支持多种输入格式以便于内容创建：
    - str: 文本内容
    - 带'image'键的dict: 图片内容  
    - 带'json'键的dict: JSON数据
    - tuple (content, position): 带特定位置的内容
    
    参数:
        *items: 混合内容类型的可变参数
        
    返回:
        带正确位置块的StructuredMessageContent
        
    示例:
        content = create_mixed_content(
            "Start text",
            {'image': 'chart.png'},
            {'json': {'data': 123}},
            ("End text", 10)  # Specific position
        )
    """
    content = StructuredMessageContent()
    
    for i, item in enumerate(items):
        if isinstance(item, tuple):
            # Item with explicit position
            data, position = item
            if isinstance(data, str):
                content.add_text(data, position)
            elif isinstance(data, dict):
                if 'image' in data:
                    content.add_image(data['image'], position)
                elif 'json' in data:
                    content.add_json(data['json'], position)
        else:
            # Auto-position based on index
            if isinstance(item, str):
                content.add_text(item, i)
            elif isinstance(item, dict):
                if 'image' in item:
                    content.add_image(item['image'], i)
                elif 'json' in item:
                    content.add_json(item['json'], i)
                else:
                    content.add_json(item, i)
    
    return content


class ConversationBuilder:
    """
    Helper class for building complex conversation scenarios.
    
    Provides high-level methods for creating common conversation
    patterns with structured content positioning.
    
    Attributes:
        graph: Conversation graph instance
    """
    
    def __init__(self):
        """使用增强图初始化对话构建器。"""
        self.graph = ConversationGraph()
    
    async def create_data_analysis_conversation(self) -> str:
        """
        创建带交错内容的数据分析对话。
        
        演示数据分析场景的复杂内容定位，
        包含混合文本、JSON数据和可视化。
        
        返回:
            创建的对话的对话ID
        """
        print("📊 Creating data analysis conversation...")
        
        # First message: Introduction with structured data
        intro_content = (StructuredMessageContent()
                        .add_text("I need to analyze the following user data.", 0)
                        .add_text("First, here's the basic user profile:", 1)
                        .add_json({
                            "user_id": "U12345",
                            "name": "Alice Johnson", 
                            "age": 28,
                            "location": "San Francisco"
                        }, 2)
                        .add_text("And here's their behavior screenshot:", 3)
                        .add_image("user_behavior_dashboard.png", 4)
                        .add_text("Please provide initial analysis.", 5))
        
        result1 = await self.graph.chat(
            system_prompt="You are a senior user behavior analyst specializing in extracting insights from multimodal data.",
            structured_content=intro_content
        )
        
        conversation_id = result1['conversation_id']
        print(f"Initial analysis: {result1['response']}\n")
        
        # Follow-up with detailed metrics
        metrics_content = (StructuredMessageContent()
                          .add_text("Based on your analysis, here are detailed metrics:", 0)
                          .add_json({
                              "sessions": [
                                  {"date": "2025-01-01", "duration": 45, "pages": 12},
                                  {"date": "2025-01-02", "duration": 32, "pages": 8}
                              ],
                              "conversion_rate": 0.15,
                              "engagement_score": 8.5
                          }, 1)
                          .add_text("And here are the visualization charts:", 2)
                          .add_image("conversion_funnel.png", 3)
                          .add_image("engagement_timeline.png", 4)
                          .add_text("What are your recommendations?", 5))
        
        result2 = await self.graph.chat(
            conversation_id=conversation_id,
            structured_content=metrics_content,
            is_final=True
        )
        
        print(f"Final recommendations: {result2['response']}")
        return conversation_id
    
    async def create_product_presentation(self) -> str:
        """
        创建带结构化布局的产品演示。
        
        演示产品演示的精确内容定位，
        包含营销文案、技术规格和视觉效果。
        
        返回:
            创建的对话的对话ID
        """
        print("🚀 Creating product presentation...")
        
        presentation_content = (StructuredMessageContent()
                               .add_text("New Product Launch Presentation", 0)
                               .add_image("product_hero_image.jpg", 1)
                               .add_text("Key Features:", 2)
                               .add_json({
                                   "features": [
                                       "AI-powered recommendations",
                                       "Real-time collaboration",
                                       "Advanced analytics"
                                   ],
                                   "target_audience": "Enterprise customers"
                               }, 3)
                               .add_text("Technical Specifications:", 4)
                               .add_json({
                                   "performance": {
                                       "response_time": "< 100ms",
                                       "uptime": "99.9%",
                                       "scalability": "1M+ users"
                                   }
                               }, 5)
                               .add_text("Market Analysis Chart:", 6)
                               .add_image("market_analysis.png", 7)
                               .add_text("Please create a compelling product summary.", 8))
        
        result = await self.graph.chat(
            system_prompt="You are a product marketing expert who creates compelling presentations.",
            structured_content=presentation_content,
            is_final=True
        )
        
        print(f"Product summary: {result['response']}")
        return result['conversation_id']


async def demonstrate_positioning_control():
    """
    演示高级位置控制功能。

    展示多种定位场景，包括非顺序插入、间隔和动态内容排列。
    """
    print("🎯 演示位置控制功能...")
    
    # 使用配置好的环境中的 LLM 类型
    graph = ConversationGraph()
    
    # Test case 1: Non-sequential positioning
    content1 = StructuredMessageContent()
    content1.add_text("This will be last", 100)
    content1.add_text("This will be first", 0)
    content1.add_image("middle_image.png", 50)
    content1.add_json({"early": "data"}, 10)
    
    result1 = await graph.chat(structured_content=content1)
    print(f"Non-sequential positioning: {result1['input_preview']}")
    
    # Test case 2: Using helper function
    content2 = create_mixed_content(
        "Introduction",
        {'image': 'diagram.png'},
        {'json': {'metrics': [1, 2, 3]}},
        ("Conclusion", 20),  # Specific position
        "Middle section"
    )
    
    result2 = await graph.chat(structured_content=content2)
    print(f"Helper function result: {result2['input_preview']}")


async def batch_conversation_processing():
    """
    演示高并发批量处理能力。

    展示如何在并发控制下同时处理多个对话请求。
    """
    print("🔥 Testing batch conversation processing...")
    
    graph = ConversationGraph(max_concurrent=3)
    
    # Create multiple conversation requests
    tasks = []
    for i in range(5):
        content = (StructuredMessageContent()
                  .add_text(f"Process task #{i+1}", 0)
                  .add_json({"task_id": i+1, "priority": "high" if i % 2 == 0 else "normal"}, 1)
                  .add_text("Please analyze and respond", 2))
        
        task = graph.chat(
            system_prompt=f"You are AI assistant #{i+1}",
            structured_content=content
        )
        tasks.append(task)
    
    # Execute all conversations concurrently
    start_time = asyncio.get_event_loop().time()
    results = await asyncio.gather(*tasks)
    end_time = asyncio.get_event_loop().time()
    
    print(f"✅ Processed {len(results)} conversations in {end_time - start_time:.2f} seconds")
    for i, result in enumerate(results):
        print(f"  Conversation {i+1}: {result['conversation_id'][:8]}...")


async def main():
    """
    主演示函数，展示所有功能。

    运行系统的综合示例，包括结构化内容定位、批量处理和真实使用场景。
    """
    print("🤖 LangGraph Conversation System Demo")
    print("=" * 60)
    
    builder = ConversationBuilder()
    
    # Run different demonstration scenarios
    print("\n1️⃣ Data Analysis Scenario:")
    await builder.create_data_analysis_conversation()
    
    print("\n2️⃣ Product Presentation Scenario:")
    await builder.create_product_presentation()
    
    print("\n3️⃣ Positioning Control Demo:")
    await demonstrate_positioning_control()
    
    print("\n4️⃣ Batch Processing Demo:")
    await batch_conversation_processing()
    
    print("\n✅ All demonstrations completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
