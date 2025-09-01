#!/usr/bin/env python3
"""
Quick test to verify the message duplication fix.
"""

import asyncio
import os

from conversation.core import ConversationGraph, Content
from conversation.load_env import load_env
load_env()


async def test_no_duplication():
    """Test that messages are not duplicated."""
    print("🧪 Testing Message Duplication Fix")
    print("=" * 40)
    
    graph = ConversationGraph()
    
    # First message
    content1 = Content()
    content1.add_text("Hello, this is message 1")
    
    result1 = await graph.chat(
        system_prompt="You are a helpful assistant.",
        content=content1
    )
    
    print(f"After message 1: {result1['message_count']} messages")
    
    # Second message
    content2 = Content()
    content2.add_text("This is message 2")
    
    result2 = await graph.chat(
        conversation_id=result1['conversation_id'],
        content=content2
    )
    
    print(f"After message 2: {result2['message_count']} messages")
    
    # Third message with final save
    content3 = Content()
    content3.add_text("This is message 3, final")
    
    result3 = await graph.chat(
        conversation_id=result1['conversation_id'],
        content=content3,
        is_final=True
    )
    
    print(f"After message 3: {result3['message_count']} messages")
    
    # Expected: 1 system + 3 user + 3 assistant = 7 messages
    expected = 7
    actual = result3['message_count']
    
    if actual == expected:
        print(f"✅ SUCCESS: Expected {expected} messages, got {actual}")
    else:
        print(f"❌ FAILED: Expected {expected} messages, got {actual}")
    
    return actual == expected


if __name__ == "__main__":
    asyncio.run(test_no_duplication())
