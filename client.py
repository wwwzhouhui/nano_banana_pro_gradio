#!/usr/bin/env python3
"""
Gemai Nano Banana Pro - API 测试客户端
用于测试 FastAPI 服务器的各个接口

注意：运行此脚本前，请先启动主程序：
    python3 app.py

主程序会自动启动 FastAPI (端口 8000) 和 Gradio (端口 7860)
"""

import requests
import json
import base64
import os
from pathlib import Path


class GemaiClient:
    """Gemai Nano Banana Pro API 客户端"""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def check_health(self):
        """检查服务器健康状态"""
        print("🏥 检查服务器健康状态...")
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 服务器健康")
                print(f"   状态: {result.get('status')}")
                print(f"   时间: {result.get('timestamp')}")
                return True
            else:
                print(f"❌ 服务器返回错误: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False

    def text_to_image(
        self,
        prompt,
        negative_prompt=None,
        num_images=1,
        temperature=0.7,
        aspect_ratio=None,
        style=None,
        save_dir="generated_images"
    ):
        """
        文生图测试

        Args:
            prompt: 提示词
            negative_prompt: 负向提示词
            num_images: 生成数量
            temperature: 创造性
            aspect_ratio: 宽高比
            style: 风格
            save_dir: 保存目录
        """
        print(f"\n🎨 文生图测试")
        print(f"   提示词: {prompt}")
        if negative_prompt:
            print(f"   负向提示词: {negative_prompt}")
        print(f"   生成数量: {num_images}")

        try:
            # 构建请求
            payload = {
                "prompt": prompt,
                "negative_prompt": negative_prompt,
                "num_images": num_images,
                "temperature": temperature,
                "aspect_ratio": aspect_ratio,
                "style": style
            }

            # 发送请求
            print("🚀 发送请求...")
            response = requests.post(
                f"{self.base_url}/text2img",
                json=payload,
                timeout=120
            )

            # 处理响应
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    images = result.get('images', [])
                    print(f"✅ 成功生成 {len(images)} 张图片")

                    # 保存图片
                    saved_count = 0
                    for idx, img_data in enumerate(images):
                        filepath = self._save_image(img_data, save_dir, f"text2img_{idx+1}")
                        if filepath:
                            print(f"   📁 图片 {idx+1} 保存至: {filepath}")
                            saved_count += 1

                    print(f"📊 成功保存 {saved_count}/{len(images)} 张图片")
                    return True
                else:
                    print(f"❌ 生成失败: {result.get('message')}")
                    return False
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                print(f"   错误详情: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 异常: {e}")
            return False

    def image_to_image(
        self,
        input_image_path,
        prompt,
        negative_prompt=None,
        strength=0.7,
        temperature=0.7,
        aspect_ratio=None,
        style=None,
        save_dir="generated_images"
    ):
        """
        图生图测试

        Args:
            input_image_path: 输入图片路径
            prompt: 提示词
            negative_prompt: 负向提示词
            strength: 变换强度
            temperature: 创造性
            aspect_ratio: 宽高比
            style: 风格
            save_dir: 保存目录
        """
        print(f"\n🖼️  图生图测试")
        print(f"   输入图片: {input_image_path}")
        print(f"   提示词: {prompt}")
        if negative_prompt:
            print(f"   负向提示词: {negative_prompt}")
        print(f"   变换强度: {strength}")

        try:
            # 检查文件是否存在
            if not os.path.exists(input_image_path):
                print(f"❌ 输入图片不存在: {input_image_path}")
                return False

            # 上传图片
            print("📤 上传图片...")
            with open(input_image_path, 'rb') as f:
                files = {'file': ('image.jpg', f, 'image/jpeg')}
                response = requests.post(f"{self.base_url}/upload", files=files, timeout=30)

            if response.status_code != 200:
                print(f"❌ 上传失败: HTTP {response.status_code}")
                return False

            upload_result = response.json()
            if not upload_result.get('success'):
                print(f"❌ 上传失败: {upload_result.get('message')}")
                return False

            image_base64 = upload_result.get('image_base64')
            print("✅ 图片上传成功")

            # 构建请求
            payload = {
                "prompt": prompt,
                "image_base64": image_base64,
                "negative_prompt": negative_prompt,
                "strength": strength,
                "temperature": temperature,
                "aspect_ratio": aspect_ratio,
                "style": style
            }

            # 发送请求
            print("🚀 发送图生图请求...")
            response = requests.post(
                f"{self.base_url}/img2img",
                json=payload,
                timeout=120
            )

            # 处理响应
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    images = result.get('images', [])
                    print(f"✅ 成功生成 {len(images)} 张图片")

                    # 保存图片
                    for idx, img_data in enumerate(images):
                        filepath = self._save_image(img_data, save_dir, f"img2img_{idx+1}")
                        if filepath:
                            print(f"   📁 图片保存至: {filepath}")

                    return True
                else:
                    print(f"❌ 生成失败: {result.get('message')}")
                    return False
            else:
                print(f"❌ 请求失败: HTTP {response.status_code}")
                print(f"   错误详情: {response.text}")
                return False

        except Exception as e:
            print(f"❌ 异常: {e}")
            return False

    def _save_image(self, image_data, save_dir, prefix):
        """保存图片"""
        try:
            # 创建目录
            Path(save_dir).mkdir(exist_ok=True)

            # 生成文件名
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            import random
            random_num = random.randint(1000, 9999)
            image_format = image_data.get('format', 'png')
            filename = f"{prefix}_{timestamp}_{random_num}.{image_format}"
            filepath = Path(save_dir) / filename

            # 解码并保存
            base64_data = image_data.get('data', '')
            image_bytes = base64.b64decode(base64_data)

            with open(filepath, 'wb') as f:
                f.write(image_bytes)

            return str(filepath)

        except Exception as e:
            print(f"❌ 保存失败: {e}")
            return None


def main():
    """主函数"""
    print("=" * 60)
    print("🎨 Gemai Nano Banana Pro - API 测试客户端")
    print("=" * 60)

    # 创建客户端
    client = GemaiClient()

    # 1. 健康检查
    if not client.check_health():
        print("\n⚠️  服务器未运行，请先启动主程序")
        print("   运行命令: python3 app.py")
        print("   （app.py 会自动启动 FastAPI 和 Gradio）")
        return

    # 2. 文生图测试
    print("\n" + "=" * 60)
    print("测试 1: 文生图（单张）")
    print("=" * 60)
    client.text_to_image(
        prompt="一只可爱的橘猫在阳光下睡觉",
        negative_prompt="模糊，低质量",
        num_images=1,
        style="realistic"
    )

    # 3. 文生图测试（多张）
    print("\n" + "=" * 60)
    print("测试 2: 文生图（多张）")
    print("=" * 60)
    client.text_to_image(
        prompt="未来科技城市，赛博朋克风格",
        num_images=2,
        aspect_ratio="16:9"
    )

    # 4. 图生图测试
    # 注意：需要先准备一张测试图片
    test_image = "test_image.jpg"
    if os.path.exists(test_image):
        print("\n" + "=" * 60)
        print("测试 3: 图生图")
        print("=" * 60)
        client.image_to_image(
            input_image_path=test_image,
            prompt="转换成动漫风格",
            strength=0.7,
            style="anime"
        )
    else:
        print(f"\n⚠️  跳过图生图测试（测试图片不存在: {test_image}）")
        print("   请准备一张测试图片并命名为 test_image.jpg")

    print("\n" + "=" * 60)
    print("✅ 测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()
