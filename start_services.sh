#!/bin/bash
# Gemai Nano Banana Pro - 启动脚本（集成模式）

echo "🚀 Gemai Nano Banana Pro 启动脚本"
echo "=================================="

# 检查 Python 环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.11+"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import fastapi" &> /dev/null; then
    echo "⚠️  缺少依赖，正在安装..."
    pip3 install -r requirements.txt
fi

# 创建必要的目录
mkdir -p generated_images
mkdir -p logs

# 检查环境变量文件
if [ ! -f .env ]; then
    echo "⚠️  .env 文件不存在，从 .env.example 复制..."
    cp .env.example .env
fi

echo ""
echo "=================================="
echo "🎨 启动 Gemai Nano Banana Pro"
echo "=================================="
echo "📦 模式: 集成模式（app.py 自动启动 FastAPI + Gradio）"
echo ""

# 启动应用（集成模式，app.py 会自动启动 FastAPI 和 Gradio）
python3 app.py
