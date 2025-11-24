#!/usr/bin/env python3
"""
Gemai Nano Banana Pro - FastAPI Server
基于 Gemai API (OpenAI 格式) 的文生图和图生图服务
模型: gemini-3-pro-image-preview
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import base64
import json
import requests
import os
import re
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
import sys
from PIL import Image
from io import BytesIO

# Load environment variables
load_dotenv()

# Configure logging
def setup_logging():
    """Setup logging configuration with both file and console output"""
    os.makedirs('logs', exist_ok=True)

    formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logger = logging.getLogger('GemaiServer')
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/fastapi_server.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

logger = setup_logging()

# Pydantic models
class Text2ImgRequest(BaseModel):
    prompt: str
    negative_prompt: Optional[str] = None
    num_images: int = 1
    temperature: float = 0.7
    aspect_ratio: Optional[str] = None
    style: Optional[str] = None

class Img2ImgRequest(BaseModel):
    prompt: str
    image_base64: str
    negative_prompt: Optional[str] = None
    strength: float = 0.7
    temperature: float = 0.7
    aspect_ratio: Optional[str] = None
    style: Optional[str] = None

class GenerateResponse(BaseModel):
    success: bool
    images: list
    message: str

# Initialize FastAPI app
app = FastAPI(
    title="Gemai Nano Banana Pro API",
    description="基于 Gemai API 的文生图和图生图服务",
    version="1.0.0"
)

# Load API configuration
GEMAI_API_KEY = os.getenv("GEMAI_API_KEY", "sk-5Tgi5fdeaCfonclflYenie6XHaoXwNdrRoFal5bqWlCXe7ST")
GEMAI_BASE_URL = os.getenv("GEMAI_BASE_URL", "https://api.gemai.cc")
GEMAI_MODEL = "gemini-3-pro-image-preview"

logger.info(f"🚀 Gemai Nano Banana Pro Server starting...")
logger.info(f"📡 API Base URL: {GEMAI_BASE_URL}")
logger.info(f"🤖 Model: {GEMAI_MODEL}")


def encode_image_from_upload(image_data: bytes) -> str:
    """
    将上传的图片编码为 base64

    Args:
        image_data: 图片字节数据

    Returns:
        base64 编码的图片字符串
    """
    try:
        # 使用 PIL 验证图片并进行压缩
        image = Image.open(BytesIO(image_data))

        # 转换为 RGB 模式
        if image.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode in ('RGBA', 'LA') else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        # 压缩图片
        max_size = 1024
        if image.width > max_size or image.height > max_size:
            logger.info(f"🔧 压缩图片: {image.width}x{image.height}")
            ratio = min(max_size / image.width, max_size / image.height)
            new_size = (int(image.width * ratio), int(image.height * ratio))
            image = image.resize(new_size, Image.Resampling.LANCZOS)
            logger.info(f"   新尺寸: {new_size[0]}x{new_size[1]}")

        # JPEG 格式压缩
        buffered = BytesIO()
        image.save(buffered, format='JPEG', quality=85, optimize=True)
        image_data = buffered.getvalue()

        # 进一步压缩（如果需要）
        if len(image_data) > 512000:  # 500KB
            logger.info(f"⚠️  进一步压缩: {len(image_data)/1024:.2f} KB")
            buffered = BytesIO()
            image.save(buffered, format='JPEG', quality=70, optimize=True)
            image_data = buffered.getvalue()
            logger.info(f"   最终大小: {len(image_data)/1024:.2f} KB")

        # Base64 编码
        base64_image = base64.b64encode(image_data).decode('utf-8')
        logger.info(f"📦 图片已编码: {len(image_data)/1024:.2f} KB")

        return base64_image

    except Exception as e:
        raise Exception(f"图片编码失败: {e}")


def extract_images_from_response(result: Dict[str, Any]) -> list:
    """
    从 API 响应中提取图片数据

    Args:
        result: API 响应结果

    Returns:
        图片数据列表 (base64 格式)
    """
    images = []

    try:
        # OpenAI 标准格式: choices -> message -> content
        if "choices" in result:
            logger.info(f"📌 解析响应，共 {len(result['choices'])} 个选择")

            for choice_idx, choice in enumerate(result["choices"]):
                message = choice.get("message", {})
                content = message.get("content", "")

                if isinstance(content, str):
                    # 方式1: Markdown 格式
                    markdown_pattern = r'!\[.*?\]\(data:image/([^;]+);base64,([^)]+)\)'
                    matches = re.findall(markdown_pattern, content)

                    if matches:
                        logger.info(f"   找到 {len(matches)} 个 Markdown 格式图片")
                        for image_format, base64_data in matches:
                            images.append({
                                'format': image_format,
                                'data': base64_data.strip()
                            })
                    else:
                        # 方式2: data URL 格式
                        data_url_pattern = r'data:image/([^;]+);base64,([A-Za-z0-9+/=\n\r]+)'
                        matches = re.findall(data_url_pattern, content, re.DOTALL)

                        if matches:
                            logger.info(f"   找到 {len(matches)} 个 data URL 格式图片")
                            for image_format, base64_data in matches:
                                clean_data = base64_data.replace('\n', '').replace('\r', '').strip()
                                images.append({
                                    'format': image_format,
                                    'data': clean_data
                                })

        logger.info(f"✓ 提取到 {len(images)} 张图片")
        return images

    except Exception as e:
        logger.error(f"❌ 提取图片失败: {e}")
        return []


@app.get("/")
async def root():
    """Root endpoint"""
    logger.info("📋 Root endpoint accessed")
    return {
        "message": "Gemai Nano Banana Pro API Server",
        "version": "1.0.0",
        "model": GEMAI_MODEL,
        "endpoints": [
            "/text2img - 文生图",
            "/img2img - 图生图",
            "/upload - 上传图片",
            "/health - 健康检查",
            "/docs - API 文档"
        ]
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    logger.info("📋 Health check")
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Gemai Nano Banana Pro"
    }


@app.post("/text2img", response_model=GenerateResponse)
async def text_to_image(request: Text2ImgRequest):
    """
    文生图接口

    Args:
        request: 文生图请求参数

    Returns:
        包含生成图片的响应
    """
    try:
        logger.info(f"🎨 文生图请求: {request.prompt[:50]}...")

        # 构建完整提示词
        full_prompt = request.prompt

        # 添加风格
        if request.style:
            style_map = {
                "realistic": "photorealistic style",
                "anime": "anime style",
                "oil-painting": "oil painting style",
                "watercolor": "watercolor painting style",
                "sketch": "sketch drawing style"
            }
            style_text = style_map.get(request.style, request.style)
            full_prompt = f"{full_prompt}, {style_text}"

        # 添加宽高比
        if request.aspect_ratio:
            full_prompt = f"{full_prompt}, aspect ratio {request.aspect_ratio}"

        # 添加负向提示词
        if request.negative_prompt:
            full_prompt = f"{full_prompt}\n\nNegative prompt: {request.negative_prompt}"

        # 构建请求
        payload = {
            "model": GEMAI_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": full_prompt
                }
            ],
            "temperature": request.temperature,
            "max_tokens": 4096
        }

        # 支持多图生成
        if request.num_images > 1:
            payload["n"] = min(request.num_images, 4)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GEMAI_API_KEY}"
        }

        # 调用 API
        logger.info(f"🚀 调用 Gemai API...")
        endpoint = f"{GEMAI_BASE_URL}/v1/chat/completions"
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=120
        )

        logger.info(f"📡 响应状态码: {response.status_code}")
        response.raise_for_status()

        result = response.json()

        # 提取图片
        images = extract_images_from_response(result)

        if not images:
            logger.warning("⚠️  未找到生成的图片")
            return GenerateResponse(
                success=False,
                images=[],
                message="未能从响应中提取图片"
            )

        logger.info(f"✅ 文生图成功，生成 {len(images)} 张图片")
        return GenerateResponse(
            success=True,
            images=images,
            message=f"成功生成 {len(images)} 张图片"
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API 请求失败: {e}")
        raise HTTPException(status_code=502, detail=f"API 请求失败: {str(e)}")
    except Exception as e:
        logger.exception(f"❌ 内部错误: {e}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")


@app.post("/img2img", response_model=GenerateResponse)
async def image_to_image(request: Img2ImgRequest):
    """
    图生图接口

    Args:
        request: 图生图请求参数

    Returns:
        包含生成图片的响应
    """
    try:
        logger.info(f"🖼️  图生图请求: {request.prompt[:50]}...")

        # 构建完整提示词
        full_prompt = f"Based on the provided image, {request.prompt}"

        # 添加风格
        if request.style:
            style_map = {
                "realistic": "photorealistic style",
                "anime": "anime style",
                "oil-painting": "oil painting style",
                "watercolor": "watercolor painting style",
                "sketch": "sketch drawing style"
            }
            style_text = style_map.get(request.style, request.style)
            full_prompt = f"{full_prompt}, {style_text}"

        # 添加宽高比
        if request.aspect_ratio:
            full_prompt = f"{full_prompt}, maintain aspect ratio {request.aspect_ratio}"

        # 添加强度说明
        if request.strength < 0.3:
            full_prompt = f"{full_prompt}. Keep very close to the original image."
        elif request.strength > 0.7:
            full_prompt = f"{full_prompt}. Feel free to make significant creative changes."

        # 添加负向提示词
        if request.negative_prompt:
            full_prompt = f"{full_prompt}\n\nNegative prompt: {request.negative_prompt}"

        # 构建 multimodal 请求
        payload = {
            "model": GEMAI_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": full_prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{request.image_base64}"
                            }
                        }
                    ]
                }
            ],
            "temperature": request.temperature,
            "max_tokens": 4096
        }

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GEMAI_API_KEY}"
        }

        # 调用 API
        logger.info(f"🚀 调用 Gemai API (图生图模式)...")
        endpoint = f"{GEMAI_BASE_URL}/v1/chat/completions"
        response = requests.post(
            endpoint,
            headers=headers,
            json=payload,
            timeout=120
        )

        logger.info(f"📡 响应状态码: {response.status_code}")
        response.raise_for_status()

        result = response.json()

        # 提取图片
        images = extract_images_from_response(result)

        if not images:
            logger.warning("⚠️  未找到生成的图片")
            return GenerateResponse(
                success=False,
                images=[],
                message="未能从响应中提取图片"
            )

        logger.info(f"✅ 图生图成功，生成 {len(images)} 张图片")
        return GenerateResponse(
            success=True,
            images=images,
            message=f"成功生成 {len(images)} 张图片"
        )

    except requests.exceptions.RequestException as e:
        logger.error(f"❌ API 请求失败: {e}")
        raise HTTPException(status_code=502, detail=f"API 请求失败: {str(e)}")
    except Exception as e:
        logger.exception(f"❌ 内部错误: {e}")
        raise HTTPException(status_code=500, detail=f"内部错误: {str(e)}")


@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    """
    上传图片并返回 base64 编码

    Args:
        file: 上传的图片文件

    Returns:
        包含 base64 编码的响应
    """
    try:
        logger.info(f"📤 图片上传: {file.filename}")

        # 验证文件类型
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="文件必须是图片类型")

        # 读取图片
        image_data = await file.read()

        # 编码图片
        base64_image = encode_image_from_upload(image_data)

        logger.info(f"✅ 图片上传成功")
        return {
            "success": True,
            "image_base64": base64_image,
            "message": "图片上传成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ 上传失败: {e}")
        raise HTTPException(status_code=500, detail=f"上传失败: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 启动 FastAPI 服务器...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
