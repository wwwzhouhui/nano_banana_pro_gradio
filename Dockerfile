FROM python:3.11-slim

# 设置维护者信息
LABEL maintainer="75271002@qq.com"
LABEL version="0.0.1"
LABEL description="AiTop100 AI-powered image processing tool with FastAPI and Gradio"

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用文件
COPY . .

# 创建必要的目录
RUN mkdir -p generated_images logs

# 暴露端口
EXPOSE 8000 7860

# 设置环境变量
ENV PYTHONUNBUFFERED=1

# 启动命令（集成模式，只需启动 app.py）
CMD ["python3", "app.py"]
