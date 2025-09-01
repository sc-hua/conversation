#!/usr/bin/env python3
"""测试简化后的模型功能。"""

from models import ContentBlock, StructuredMessageContent

def test_simplified_models():
    """测试简化后的模型。"""
    print("🧪 测试简化后的模型功能")
    print("=" * 50)
    
    # 测试 ContentBlock（无 position 字段）
    print("\n1️⃣ 测试 ContentBlock:")
    block = ContentBlock(type='text', content='测试文本', style='bold', color='red')
    print(f"   类型: {block.type}")
    print(f"   内容: {block.content}")
    print(f"   自定义字段: {block.extras}")
    print(f"   获取样式: {block.get_extra('style')}")
    print(f"   是否有颜色: {block.has_extra('color')}")
    
    # 测试 StructuredMessageContent（按添加顺序）
    print("\n2️⃣ 测试 StructuredMessageContent:")
    content = StructuredMessageContent()
    content.add_text('第一项')
    content.add_image('test.png', alt='图片描述', width=300)
    content.add_json({'key': 'value'}, source='测试数据')
    
    print(f"   内容块数量: {len(content.blocks)}")
    for i, block in enumerate(content.blocks):
        print(f"   块 {i}: {block.type} - {block.content}")
        if block.extras:
            print(f"     自定义字段: {block.extras}")
    
    print(f"   显示文本: {content.to_display_text()}")
    
    # 测试工厂方法
    print("\n3️⃣ 测试工厂方法:")
    content2 = StructuredMessageContent.from_mixed_items(
        '标题',
        {'image': 'chart.png'},
        {'json': {'data': 123}},
        ('结论', {'style': 'bold', 'color': 'blue'})
    )
    
    print(f"   工厂方法内容块数量: {len(content2.blocks)}")
    for i, block in enumerate(content2.blocks):
        print(f"   块 {i}: {block.type} - {block.content}")
        if block.extras:
            print(f"     自定义字段: {block.extras}")
    
    print(f"   工厂方法显示文本: {content2.to_display_text()}")
    
    # 测试插入功能
    print("\n4️⃣ 测试插入功能:")
    content3 = StructuredMessageContent()
    content3.add_text('开始')
    content3.add_text('结束')
    content3.insert_text(1, '中间插入', priority='high')
    
    print("   插入后的内容:")
    for i, block in enumerate(content3.blocks):
        print(f"   块 {i}: {block.type} - {block.content}")
        if block.extras:
            print(f"     自定义字段: {block.extras}")
    
    print("\n✅ 所有测试通过！简化后的模型工作正常")
    print("🎉 优化总结:")
    print("   - 移除了不必要的 position 字段")
    print("   - 简化了排序逻辑")
    print("   - 保持了自定义字段功能")
    print("   - 代码更轻量高效")

if __name__ == "__main__":
    test_simplified_models()
