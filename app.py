#!/usr/bin/env python3
"""
Gemai Nano Banana Pro - Gradio Web Interface
基于 Gemai API 的文生图和图生图 Web 界面
集成 FastAPI 后端服务，单文件启动
"""

import gradio as gr
import requests
import json
import os
import base64
from datetime import datetime
from PIL import Image
import io
from dotenv import load_dotenv, set_key
from pathlib import Path
import threading
import time
import uvicorn
import sys

# 加载环境变量
load_dotenv()

# 导入 FastAPI 应用
from fastapi_server import app as fastapi_app, logger as fastapi_logger


def start_fastapi_server():
    """在后台线程启动 FastAPI 服务器"""
    try:
        fastapi_logger.info("🚀 在后台线程启动 FastAPI 服务器...")
        fastapi_logger.info("   监听地址: http://0.0.0.0:8000")

        # 使用 uvicorn 启动 FastAPI
        config = uvicorn.Config(
            app=fastapi_app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            access_log=True
        )
        server = uvicorn.Server(config)
        server.run()
    except Exception as e:
        fastapi_logger.error(f"❌ FastAPI 服务器启动失败: {e}")
        sys.exit(1)


def wait_for_fastapi_ready(max_retries=30, retry_interval=1):
    """等待 FastAPI 服务器启动完成"""
    print("⏳ 等待 FastAPI 服务器启动...")

    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                print("✅ FastAPI 服务器已启动")
                return True
        except:
            pass

        time.sleep(retry_interval)
        if (i + 1) % 5 == 0:
            print(f"   等待中... ({i + 1}/{max_retries})")

    print("❌ FastAPI 服务器启动超时")
    return False


def load_env_config():
    """加载 .env 文件配置"""
    api_key = os.getenv("GEMAI_API_KEY", "sk-5Tgi5fdeaCfonclflYenie6XHaoXwNdrRoFal5bqWlCXe7ST")
    base_url = os.getenv("GEMAI_BASE_URL", "https://api.gemai.cc")
    return api_key, base_url


def save_env_config(api_key, base_url):
    """保存配置到 .env 文件"""
    try:
        env_file = ".env"
        if not os.path.exists(env_file):
            with open(env_file, 'w') as f:
                f.write("")

        set_key(env_file, "GEMAI_API_KEY", api_key)
        set_key(env_file, "GEMAI_BASE_URL", base_url)

        # 重新加载环境变量
        load_dotenv(override=True)

        return True, "✅ 配置保存成功"
    except Exception as e:
        return False, f"❌ 保存配置失败: {str(e)}"


class GemaiNanaBananaApp:
    def __init__(self, api_base_url="http://localhost:8000"):
        self.api_base_url = api_base_url

    def check_server_health(self):
        """检查 FastAPI 服务器状态"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            if response.status_code == 200:
                return True, "✅ 服务器运行正常"
            else:
                return False, f"❌ 服务器返回错误: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, f"❌ 无法连接到服务器: {str(e)}"

    def upload_image_to_server(self, image):
        """上传图片到 FastAPI 服务器"""
        try:
            # 将 PIL 图片转换为字节流
            img_byte_arr = io.BytesIO()
            if isinstance(image, str):
                # 如果是文件路径
                with open(image, 'rb') as f:
                    img_byte_arr.write(f.read())
            else:
                # 如果是 PIL Image 对象
                image.save(img_byte_arr, format='JPEG')

            img_byte_arr.seek(0)

            # 上传图片
            files = {'file': ('image.jpg', img_byte_arr, 'image/jpeg')}
            response = requests.post(f"{self.api_base_url}/upload", files=files, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    return result.get('image_base64'), "✅ 图片上传成功"
                else:
                    return None, f"❌ 上传失败: {result.get('message', '未知错误')}"
            else:
                return None, f"❌ 上传失败: HTTP {response.status_code}"
        except Exception as e:
            return None, f"❌ 上传异常: {str(e)}"

    def save_base64_image(self, image_data_dict):
        """保存 base64 编码的图片"""
        try:
            image_format = image_data_dict.get('format', 'png')
            base64_data = image_data_dict.get('data', '')

            # 创建输出目录
            output_dir = Path("generated_images")
            output_dir.mkdir(exist_ok=True)

            # 生成文件名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            import random
            random_num = random.randint(1000, 9999)
            filename = f"generated_{timestamp}_{random_num}.{image_format}"
            filepath = output_dir / filename

            # 解码并保存
            image_bytes = base64.b64decode(base64_data)
            with open(filepath, 'wb') as f:
                f.write(image_bytes)

            print(f"✅ 图片已保存: {filepath}")
            return str(filepath)

        except Exception as e:
            print(f"❌ 保存图片失败: {e}")
            return None

    def text_to_image(
        self,
        prompt,
        negative_prompt,
        num_images,
        temperature,
        aspect_ratio,
        style,
        progress=gr.Progress()
    ):
        """文生图功能"""
        if not prompt.strip():
            gr.Warning("❌ 请输入提示词")
            return []

        print(f"🎨 开始文生图: {prompt}")

        # 检查服务器状态
        is_healthy, health_msg = self.check_server_health()
        if not is_healthy:
            gr.Error(health_msg)
            return []

        try:
            progress(0.1, desc="正在准备请求...")

            # 构建请求
            payload = {
                "prompt": prompt,
                "negative_prompt": negative_prompt if negative_prompt else None,
                "num_images": num_images,
                "temperature": temperature,
                "aspect_ratio": aspect_ratio if aspect_ratio != "不限制" else None,
                "style": style if style != "不限制" else None
            }

            progress(0.3, desc="正在调用 AI 生成...")

            # 调用 API
            response = requests.post(
                f"{self.api_base_url}/text2img",
                json=payload,
                timeout=120
            )

            progress(0.8, desc="正在处理响应...")

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    images = result.get('images', [])

                    if not images:
                        gr.Warning("⚠️  未生成图片")
                        return []

                    # 保存并返回图片路径
                    saved_images = []
                    for img_data in images:
                        filepath = self.save_base64_image(img_data)
                        if filepath:
                            saved_images.append(filepath)

                    progress(1.0, desc="完成！")
                    gr.Info(f"✅ 成功生成 {len(saved_images)} 张图片")
                    return saved_images
                else:
                    gr.Error(f"❌ 生成失败: {result.get('message', '未知错误')}")
                    return []
            else:
                gr.Error(f"❌ 请求失败: HTTP {response.status_code}")
                return []

        except Exception as e:
            print(f"❌ 文生图异常: {e}")
            gr.Error(f"❌ 异常: {str(e)}")
            return []

    def image_to_image(
        self,
        input_image,
        prompt,
        negative_prompt,
        strength,
        temperature,
        aspect_ratio,
        style,
        progress=gr.Progress()
    ):
        """图生图功能"""
        if input_image is None:
            gr.Warning("❌ 请上传图片")
            return None

        if not prompt.strip():
            gr.Warning("❌ 请输入提示词")
            return None

        print(f"🖼️  开始图生图: {prompt}")

        # 检查服务器状态
        is_healthy, health_msg = self.check_server_health()
        if not is_healthy:
            gr.Error(health_msg)
            return None

        try:
            progress(0.1, desc="正在上传图片...")

            # 上传图片
            image_base64, upload_msg = self.upload_image_to_server(input_image)
            if not image_base64:
                gr.Error(upload_msg)
                return None

            progress(0.3, desc="正在调用 AI 生成...")

            # 构建请求
            payload = {
                "prompt": prompt,
                "image_base64": image_base64,
                "negative_prompt": negative_prompt if negative_prompt else None,
                "strength": strength,
                "temperature": temperature,
                "aspect_ratio": aspect_ratio if aspect_ratio != "不限制" else None,
                "style": style if style != "不限制" else None
            }

            # 调用 API
            response = requests.post(
                f"{self.api_base_url}/img2img",
                json=payload,
                timeout=120
            )

            progress(0.8, desc="正在处理响应...")

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    images = result.get('images', [])

                    if not images:
                        gr.Warning("⚠️  未生成图片")
                        return None

                    # 保存第一张图片
                    filepath = self.save_base64_image(images[0])

                    if filepath:
                        progress(1.0, desc="完成！")
                        gr.Info("✅ 图生图成功")
                        return filepath
                    else:
                        gr.Error("❌ 保存图片失败")
                        return None
                else:
                    gr.Error(f"❌ 生成失败: {result.get('message', '未知错误')}")
                    return None
            else:
                gr.Error(f"❌ 请求失败: HTTP {response.status_code}")
                return None

        except Exception as e:
            print(f"❌ 图生图异常: {e}")
            gr.Error(f"❌ 异常: {str(e)}")
            return None


def create_gradio_interface():
    """创建 Gradio 界面"""
    app = GemaiNanaBananaApp()

    def handle_config_save(api_key, base_url):
        """处理配置保存"""
        if not api_key.strip():
            return "❌ API Key 不能为空", api_key, base_url

        success, message = save_env_config(api_key.strip(), base_url.strip())
        return message, api_key, base_url

    def load_current_config():
        """加载当前配置"""
        api_key, base_url = load_env_config()
        return api_key, base_url

    with gr.Blocks(title="Gemai Nano Banana Pro") as demo:
        gr.Markdown("# 🎨 Gemai Nano Banana Pro")
        gr.Markdown("基于 Gemai API 的文生图和图生图工具 | 模型: gemini-3-pro-image-preview")

        with gr.Tabs():
            # Tab 1: 文生图
            with gr.TabItem("✨ 文生图"):
                gr.Markdown("### 输入提示词生成图片")

                with gr.Row():
                    with gr.Column():
                        text2img_prompt = gr.Textbox(
                            label="提示词 (Prompt)",
                            placeholder="描述你想要生成的图片，例如：一只可爱的小猫在花园里玩耍",
                            lines=3
                        )
                        text2img_negative = gr.Textbox(
                            label="负向提示词 (Negative Prompt)",
                            placeholder="描述你不想要的内容，例如：模糊、低质量",
                            lines=2
                        )

                        with gr.Row():
                            text2img_num = gr.Slider(
                                label="生成数量",
                                minimum=1,
                                maximum=4,
                                value=1,
                                step=1
                            )
                            text2img_temp = gr.Slider(
                                label="创造性 (Temperature)",
                                minimum=0.0,
                                maximum=1.0,
                                value=0.7,
                                step=0.1
                            )

                        with gr.Row():
                            text2img_ratio = gr.Dropdown(
                                label="宽高比",
                                choices=["不限制", "1:1", "16:9", "9:16", "4:3", "3:4"],
                                value="不限制"
                            )
                            text2img_style = gr.Dropdown(
                                label="风格",
                                choices=["不限制", "realistic", "anime", "oil-painting", "watercolor", "sketch"],
                                value="不限制"
                            )

                        text2img_btn = gr.Button("✨ 生成图片", variant="primary", size="lg")

                        # 提示词示例
                        gr.Markdown("### 💡 提示词示例")
                        gr.Examples(
                            examples=[
                                ["一只可爱的橘猫在阳光下睡觉"],
                                ["未来科技城市，霓虹灯，赛博朋克风格"],
                                ["日本动漫风格的少女，樱花背景"],
                                ["油画风格的海边日落"],
                                ["水彩画风格的森林小屋"],
                                ["A cute robot playing with a cat"],
                                ["Cyberpunk city at night with neon lights"],
                            ],
                            inputs=text2img_prompt
                        )

                    with gr.Column():
                        text2img_output = gr.Gallery(
                            label="生成的图片",
                            show_label=True,
                            columns=2,
                            rows=2,
                            object_fit="contain",
                            height="auto"
                        )

                text2img_btn.click(
                    fn=app.text_to_image,
                    inputs=[
                        text2img_prompt,
                        text2img_negative,
                        text2img_num,
                        text2img_temp,
                        text2img_ratio,
                        text2img_style
                    ],
                    outputs=[text2img_output],
                    show_progress=True
                )

            # Tab 2: 图生图
            with gr.TabItem("🖼️  图生图"):
                gr.Markdown("### 基于图片生成新图片")

                with gr.Row():
                    with gr.Column():
                        img2img_input = gr.Image(
                            label="上传图片",
                            type="pil",
                            sources=["upload", "clipboard"]
                        )
                        img2img_prompt = gr.Textbox(
                            label="修改提示词",
                            placeholder="描述你想要对图片进行的修改，例如：转换成动漫风格",
                            lines=3
                        )
                        img2img_negative = gr.Textbox(
                            label="负向提示词",
                            placeholder="描述你不想要的内容",
                            lines=2
                        )

                        with gr.Row():
                            img2img_strength = gr.Slider(
                                label="变换强度",
                                minimum=0.0,
                                maximum=1.0,
                                value=0.7,
                                step=0.1,
                                info="越高变化越大"
                            )
                            img2img_temp = gr.Slider(
                                label="创造性",
                                minimum=0.0,
                                maximum=1.0,
                                value=0.7,
                                step=0.1
                            )

                        with gr.Row():
                            img2img_ratio = gr.Dropdown(
                                label="宽高比",
                                choices=["不限制", "1:1", "16:9", "9:16", "4:3", "3:4"],
                                value="不限制"
                            )
                            img2img_style = gr.Dropdown(
                                label="风格",
                                choices=["不限制", "realistic", "anime", "oil-painting", "watercolor", "sketch"],
                                value="不限制"
                            )

                        img2img_btn = gr.Button("🎨 生成图片", variant="primary", size="lg")

                        # 提示词示例
                        gr.Markdown("### 💡 提示词示例")
                        gr.Examples(
                            examples=[
                                ["转换成动漫风格"],
                                ["添加夕阳和温暖的光线"],
                                ["转换成油画风格"],
                                ["添加雪花和冬天氛围"],
                                ["让画面更加梦幻"],
                                ["Convert to watercolor painting style"],
                                ["Add a robot in the scene"],
                            ],
                            inputs=img2img_prompt
                        )

                    with gr.Column():
                        img2img_output = gr.Image(
                            label="生成的图片",
                            type="filepath"
                        )
                        copy_to_input_btn = gr.Button("📋 复制到输入区继续修改", variant="secondary")

                img2img_btn.click(
                    fn=app.image_to_image,
                    inputs=[
                        img2img_input,
                        img2img_prompt,
                        img2img_negative,
                        img2img_strength,
                        img2img_temp,
                        img2img_ratio,
                        img2img_style
                    ],
                    outputs=[img2img_output],
                    show_progress=True
                )

                # 复制按钮功能
                def copy_result_to_input(result_image_path):
                    if result_image_path:
                        return Image.open(result_image_path)
                    return None

                copy_to_input_btn.click(
                    fn=copy_result_to_input,
                    inputs=[img2img_output],
                    outputs=[img2img_input]
                )

            # Tab 3: 系统设置
            with gr.TabItem("⚙️ 系统设置"):
                gr.Markdown("### API 配置")
                gr.Markdown("配置 Gemai API 以使用图片生成服务")

                with gr.Row():
                    with gr.Column():
                        api_key_input = gr.Textbox(
                            label="GEMAI_API_KEY",
                            placeholder="请输入您的 Gemai API Key",
                            type="password",
                            lines=1
                        )
                        base_url_input = gr.Textbox(
                            label="GEMAI_BASE_URL",
                            placeholder="API 基础地址",
                            value="https://api.gemai.cc",
                            lines=1
                        )

                        with gr.Row():
                            save_config_btn = gr.Button("💾 保存配置", variant="primary")
                            load_config_btn = gr.Button("🔄 重新加载", variant="secondary")

                        config_status = gr.Textbox(
                            label="状态",
                            interactive=False,
                            lines=1
                        )

                    with gr.Column():
                        gr.Markdown("### 配置说明")
                        gr.Markdown("""
                        **获取 API Key 步骤：**
                        1. 访问 [Gemai 公益站](https://api.gemai.cc)
                        2. 注册/登录账号
                        3. 获取 API Key
                        4. 将 Key 填入左侧输入框
                        5. 点击"保存配置"按钮

                        **注意事项：**
                        - 配置会保存到本地 .env 文件中
                        - 保存后需要重启 FastAPI 服务器生效
                        - 请妥善保管您的 API Key
                        - 默认使用公益站密钥（有限额）

                        **模型信息：**
                        - 模型: gemini-3-pro-image-preview
                        - 支持: 文生图、图生图
                        - 格式: OpenAI 标准格式
                        """)

                # 加载配置按钮
                def on_load_config():
                    api_key, base_url = load_current_config()
                    return api_key, base_url, ""

                load_config_btn.click(
                    fn=on_load_config,
                    inputs=[],
                    outputs=[api_key_input, base_url_input, config_status]
                )

                # 保存配置按钮
                save_config_btn.click(
                    fn=handle_config_save,
                    inputs=[api_key_input, base_url_input],
                    outputs=[config_status, api_key_input, base_url_input]
                )

                # 页面加载时自动加载配置
                demo.load(
                    fn=on_load_config,
                    inputs=[],
                    outputs=[api_key_input, base_url_input, config_status]
                )

        # 底部信息
        with gr.Accordion("ℹ️  使用说明", open=False):
            gr.Markdown("""
            ### 功能说明：
            1. **文生图**：输入提示词，AI 生成全新的图片
            2. **图生图**：上传图片 + 提示词，AI 基于图片生成新图片
            3. **系统设置**：配置 Gemai API Key

            ### 技术架构：
            - 前端：Gradio Web 界面
            - 后端：FastAPI 服务器 (localhost:8000)
            - API：Gemai 公益站（OpenAI 标准格式）
            - 模型：gemini-3-pro-image-preview

            ### 注意事项：
            - 确保 FastAPI 服务器正在运行
            - 支持 JPG、PNG 等常见图片格式
            - 生成的图片会自动保存到 generated_images 目录
            - 配置 Token 后需要重启 FastAPI 服务器

            ### 提示词技巧：
            - 使用详细、具体的描述
            - 可以指定风格、光线、构图等
            - 负向提示词用于排除不想要的元素
            - 支持中英文提示词
            """)

    return demo


if __name__ == "__main__":
    print("=" * 60)
    print("🎨 Gemai Nano Banana Pro")
    print("=" * 60)
    print("📦 启动模式: 集成模式（FastAPI + Gradio）")
    print("=" * 60)

    # 1. 在后台线程启动 FastAPI 服务器
    fastapi_thread = threading.Thread(target=start_fastapi_server, daemon=True)
    fastapi_thread.start()
    print("🔧 FastAPI 服务器正在后台启动...")

    # 2. 等待 FastAPI 服务器就绪
    if not wait_for_fastapi_ready():
        print("❌ 无法启动 FastAPI 服务器，程序退出")
        sys.exit(1)

    # 3. 启动 Gradio 应用
    print("\n" + "=" * 60)
    print("🌐 启动 Gradio Web 界面...")
    print("=" * 60)
    print("📍 访问地址:")
    print("   - Gradio UI: http://localhost:7860")
    print("   - FastAPI Docs: http://localhost:8000/docs")
    print("   - API Health: http://localhost:8000/health")
    print("=" * 60)

    demo = create_gradio_interface()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        inbrowser=True
    )
