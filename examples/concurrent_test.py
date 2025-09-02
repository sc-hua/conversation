#!/usr/bin/env python3
"""
并发推理测试脚本 - 轻量版

专注于核心并发性能测试，避免复杂依赖，支持图像测试
"""

import asyncio
import time
import json
import os

from dotenv import load_dotenv
load_dotenv()

from conversation.core import ConversationGraph, Content
from conversation.utils.image_utils import load_image

# 全局配置
LLM = "mock"
LLM = "oai"
SAVE_CONVERSATIONS = True  # 全局控制是否保存对话到文件
os.environ['HISTORY_SAVE_PATH'] = './logs/draft'  # 设置保存路径

# 测试图像路径
TEST_IMAGE_PATH = "./data/images/test_image.jpg"

class SimpleConcurrentTest:
    """简化的并发测试类"""

    async def basic_concurrent_test(self, concurrent_levels=[1, 3, 5, 7, 9, 11, 13, 15, 17]):
        """基本并发性能测试"""
        print("🔄 基本并发测试...")
        
        results = []
        for concurrent in concurrent_levels:
            print(f"\n📊 并发数: {concurrent}")
            
            graph = ConversationGraph(llm=LLM, max_concurrent=concurrent)

            # 创建测试任务
            prompts = [f"计算{i}+{i}" for i in range(1, concurrent+1)]
            
            start_time = time.time()
            tasks = [
                graph.chat(content=Content(f"任务{i}: {prompt}"))
                for i, prompt in enumerate(prompts)
            ]
            
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = time.time() - start_time
            
            # 统计结果
            successful = [r for r in completed if not isinstance(r, Exception)]
            success_rate = len(successful) / len(completed) * 100
            
            result = {
                "concurrent": concurrent,
                "success_rate": success_rate,
                "elapsed": elapsed,
                "throughput": len(successful) / elapsed
            }
            results.append(result)
            
            print(f"  成功率: {success_rate:.1f}%")
            print(f"  耗时: {elapsed:.2f}s")
            print(f"  吞吐: {result['throughput']:.1f} req/s")
            
            # 清理
            cleanup_tasks = [
                graph.end(r['conv_id'], save=SAVE_CONVERSATIONS)
                for r in successful if r.get('conv_id')
            ]
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
        
        return results
    
    async def multi_round_concurrent_test(self, num_conversations=3):
        """多轮对话并发测试"""
        print(f"\n🔄 多轮对话并发测试 ({num_conversations}个对话)...")
        
        async def single_conversation(conv_id):
            """单个对话流程"""
            graph = ConversationGraph(llm=LLM)
            
            try:
                # 第一轮
                result1 = await graph.chat(
                    system_prompt=f"你是助手{conv_id}",
                    content=Content(f"对话{conv_id}: 介绍你自己")
                )
                
                # 第二轮
                result2 = await graph.chat(
                    conv_id=result1['conv_id'],
                    content=Content("我刚才说了什么？")
                )
                
                # 清理对话 - 使用全局配置
                await graph.end(result2['conv_id'], save=SAVE_CONVERSATIONS)
                
                return {
                    "conv_id": conv_id,
                    "success": True,
                    "rounds": 2,
                    "final_conv_id": result2['conv_id']
                }
            except Exception as e:
                return {"conv_id": conv_id, "success": False, "error": str(e)}
        
        start_time = time.time()
        conversation_tasks = [
            single_conversation(i) 
            for i in range(num_conversations)
        ]
        
        results = await asyncio.gather(*conversation_tasks)
        elapsed = time.time() - start_time
        
        # 统计
        successful = [r for r in results if r['success']]
        print(f"  成功对话: {len(successful)}/{num_conversations}")
        print(f"  总耗时: {elapsed:.2f}s")
        print(f"  平均每对话: {elapsed/num_conversations:.2f}s")
        
        return {"successful": len(successful), "total": num_conversations, "elapsed": elapsed}
    
    async def image_concurrent_test(self, concurrent_levels=[3, 5, 7]):
        """图像内容并发测试"""
        print("\n🔄 图像并发测试...")
        
        # 检查测试图像是否存在
        if not os.path.exists(TEST_IMAGE_PATH):
            print(f"⚠️  测试图像不存在: {TEST_IMAGE_PATH}")
            return []
        
        results = []
        for concurrent in concurrent_levels:
            print(f"\n📊 图像并发数: {concurrent}")
            
            graph = ConversationGraph(llm=LLM, max_concurrent=concurrent)
            
            try:
                # 创建图像测试任务
                tasks = []
                for i in range(concurrent):
                    content = Content(
                        f"任务{i+1}: 描述这个图片",
                        {'image': TEST_IMAGE_PATH}
                    )
                    tasks.append(graph.chat(content=content))
                
                start_time = time.time()
                completed = await asyncio.gather(*tasks, return_exceptions=True)
                elapsed = time.time() - start_time
                
                # 统计结果
                successful = [r for r in completed if not isinstance(r, Exception)]
                success_rate = len(successful) / len(completed) * 100
                
                result = {
                    "concurrent": concurrent,
                    "success_rate": success_rate,
                    "elapsed": elapsed,
                    "throughput": len(successful) / elapsed,
                    "type": "image"
                }
                results.append(result)
                
                print(f"  成功率: {success_rate:.1f}%")
                print(f"  耗时: {elapsed:.2f}s")
                print(f"  吞吐: {result['throughput']:.1f} req/s")
                
                # 清理
                cleanup_tasks = [
                    graph.end(r['conv_id'], save=SAVE_CONVERSATIONS)
                    for r in successful if r.get('conv_id')
                ]
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)
                
            except Exception as e:
                print(f"  图像测试失败: {e}")
                continue
        
        return results
    
    async def mixed_content_test(self, num_tasks=6):
        """混合内容并发测试 - 文本和图像混合"""
        print(f"\n🔄 混合内容并发测试 ({num_tasks}个任务)...")
        
        graph = ConversationGraph(llm=LLM, max_concurrent=num_tasks)
        
        tasks = []
        try:
            # 创建混合任务：一半文本，一半图像
            for i in range(num_tasks):
                if i % 2 == 0:
                    # 文本任务
                    content = Content(f"任务{i+1}: 计算{i+1}的平方")
                else:
                    # 图像任务
                    if os.path.exists(TEST_IMAGE_PATH):
                        content = Content(
                            f"任务{i+1}: 简要描述图片内容",
                            {'image': TEST_IMAGE_PATH}
                        )
                    else:
                        content = Content(f"任务{i+1}: 描述一个理想的测试图片")
                
                tasks.append(graph.chat(content=content))
            
            start_time = time.time()
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            elapsed = time.time() - start_time
            
            # 统计结果
            successful = [r for r in completed if not isinstance(r, Exception)]
            text_tasks = len([i for i in range(num_tasks) if i % 2 == 0])
            image_tasks = num_tasks - text_tasks
            
            print(f"  总任务: {num_tasks} (文本: {text_tasks}, 图像: {image_tasks})")
            print(f"  成功: {len(successful)}/{num_tasks}")
            print(f"  总耗时: {elapsed:.2f}s")
            print(f"  平均耗时: {elapsed/num_tasks:.2f}s/任务")
            
            # 清理
            cleanup_tasks = [
                graph.end(r['conv_id'], save=SAVE_CONVERSATIONS)
                for r in successful if r.get('conv_id')
            ]
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            
            return {
                "total_tasks": num_tasks,
                "text_tasks": text_tasks,
                "image_tasks": image_tasks,
                "successful": len(successful),
                "elapsed": elapsed
            }
            
        except Exception as e:
            print(f"  混合测试失败: {e}")
            return None
    
    async def run_all_tests(self):
        """运行全部测试"""
        print("🔄 并发性能测试套件")
        print("=" * 40)

        basic_results = multi_round_results = image_results = mixed_results = None
        
        # basic_results = await self.basic_concurrent_test()
        # multi_round_results = await self.multi_round_concurrent_test()
        image_results = await self.image_concurrent_test()
        mixed_results = await self.mixed_content_test()

        # 保存结果
        all_results = {
            "timestamp": time.time(),
            "basic_concurrent": basic_results,
            "multi_round": multi_round_results,
            "image_concurrent": image_results,
            "mixed_content": mixed_results
        }
        
        result_file = f"logs/test_results_{int(time.time())}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📝 测试结果保存到: {result_file}")
        
        # 显示最优配置
        if basic_results:
            best = max(basic_results, key=lambda x: x['throughput'])
            print(f"🏆 文本最优并发数: {best['concurrent']} (吞吐量: {best['throughput']:.1f} req/s)")
        
        if image_results:
            best_img = max(image_results, key=lambda x: x['throughput'])
            print(f"🖼️  图像最优并发数: {best_img['concurrent']} (吞吐量: {best_img['throughput']:.1f} req/s)")
        
        return all_results


async def main():
    """主测试函数"""
    tester = SimpleConcurrentTest()
    
    try:
        results = await tester.run_all_tests()
        print("\n✅ 并发测试完成!")
        return results
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(main())
