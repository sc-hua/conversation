#!/bin/bash
# 
# 对话系统开发环境安装脚本
# 支持conda/venv环境自动检测和包安装
#

set -e

echo "🚀 安装Conversation对话系统..."

# 检测当前Python环境
if [[ -n "${CONDA_DEFAULT_ENV:-}" ]]; then
    echo "✅ 检测到Conda环境: $CONDA_DEFAULT_ENV"
    PYTHON_CMD="python"
elif [[ -n "${VIRTUAL_ENV:-}" ]]; then
    echo "✅ 检测到虚拟环境: $VIRTUAL_ENV"
    PYTHON_CMD="python"
else
    echo "⚠️  未检测到虚拟环境，建议先创建conda或venv环境"
    read -p "是否继续使用系统Python? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 安装已取消"
        exit 1
    fi
    PYTHON_CMD="python3"
fi

# 检查Python版本
PYTHON_VERSION=$($PYTHON_CMD -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Python版本: $PYTHON_VERSION"

if [[ $(echo "$PYTHON_VERSION < 3.8" | bc -l) -eq 1 ]]; then
    echo "❌ 需要Python 3.8+，当前版本: $PYTHON_VERSION"
    exit 1
fi

# 升级pip
echo "📦 升级pip..."
$PYTHON_CMD -m pip install --upgrade pip

# 以开发模式安装包
echo "🔧 安装Conversation包(开发模式)..."
$PYTHON_CMD -m pip install -e .

# 验证安装
echo "🧪 验证安装..."
if $PYTHON_CMD -c "import conversation; print('✅ 导入成功')"; then
    echo "🎉 安装完成！"
    echo ""
    echo "📝 接下来："
    echo "1. 配置.env文件 (参考.env_example)"
    echo "2. 运行测试: python tests/test_simplified.py"
    echo "3. 运行示例: python examples/test.py"
    echo "4. Mock LLM测试: python tests/test_llm.py mock"
else
    echo "❌ 安装验证失败"
    exit 1
fi
