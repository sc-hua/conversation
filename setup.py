#!/usr/bin/env python3
"""
Conversation项目安装配置
"""

from setuptools import setup, find_packages

setup(
    name="conversation",
    version="0.1.0",
    description="多模态对话系统",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=[
        "pydantic>=2.0.0",
        "aiohttp>=3.8.0",
        "openai>=1.0.0",
        "pillow>=9.0.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9", 
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
