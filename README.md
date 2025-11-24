# 🎨 Gemai Nano Banana Pro

基于 **Gemai API** 的文生图和图生图 Web 应用，使用 **Gradio + FastAPI** 框架构建。

## ✨ 特性

- 🖼️ **文生图（Text-to-Image）**：输入提示词，AI 生成全新图片
- 🎨 **图生图（Image-to-Image）**：基于输入图片 + 提示词生成新图片
- 🌐 **Web 界面**：基于 Gradio 的友好用户界面
- ⚡ **集成架构**：FastAPI 后端与 Gradio 前端集成，单命令启动
- 🔧 **灵活配置**：支持多种风格、宽高比、创造性参数
- 📦 **批量生成**：文生图支持一次生成多张图片（1-4张）
- 🚀 **简化部署**：无需分别启动前后端，app.py 一键启动
- 📝 **日志系统**：完整的日志记录，支持文件轮转，便于问题定位
- 🔐 **用户限制**：支持每日使用次数限制（可配置开关，适用于生产环境）

## 🤖 技术栈

- **前端**：Gradio >= 5.44.1（支持 6.0.0+）
- **后端**：FastAPI 0.116.1 + Uvicorn >= 0.35.0 (standard)
- **API**：Gemai 公益站（OpenAI 标准格式）
- **模型**：gemini-3-pro-image-preview
- **图片处理**：Pillow >= 11.3.0
- **Python 版本**：3.10+（推荐 3.11+）
- **其他依赖**：
  - requests >= 2.32.4
  - python-dotenv >= 1.1.0
  - pydantic 2.5.3
  - python-multipart >= 0.0.6

## 📁 项目结构

```
gemai_nano_banana_pro/
├── app.py                    # 主程序（集成 Gradio + FastAPI 启动）
├── fastapi_server.py         # FastAPI 后端服务器模块
├── client.py                 # API 测试客户端
├── requirements.txt          # Python 依赖
├── .env                      # 环境变量配置
├── .env.example              # 环境变量示例
├── .gitignore                # Git 忽略文件
├── start_services.sh         # 启动脚本（调用 app.py）
├── README.md                 # 项目文档
├── USAGE_LIMIT_GUIDE.md      # 用户限制功能说明
├── LOGGING_GUIDE.md          # 日志系统使用指南
├── Dockerfile                # Docker 镜像配置
├── docker-compose.yml        # Docker Compose 配置
├── .dockerignore             # Docker 忽略文件
├── generated_images/         # 生成的图片目录
├── data/                     # 数据存储目录
│   └── daily_user_usage.json # 用户每日使用记录
└── logs/                     # 日志目录
    ├── gradio_app.log        # Gradio 应用日志
    └── fastapi_server.log    # FastAPI 服务日志
```

**启动流程：**
```
app.py 启动
   ├── 1. 后台线程启动 FastAPI (端口 8000)
   ├── 2. 等待 FastAPI 就绪
   └── 3. 主线程启动 Gradio (端口 7860)
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.10+ （推荐使用 Python 3.11+）
- pip

### 2. 安装依赖

```bash
cd gemai_nano_banana_pro
pip install -r requirements.txt
```

### 3. 配置 API Key

编辑 `.env` 文件，设置您的 Gemai API Key：

```bash
# Gemai API 配置
GEMAI_API_KEY=your_api_key_here
GEMAI_BASE_URL=https://api.gemai.cc

# 用户限制配置（可选）
# 是否启用用户限制（true/false）
# - true: 启用限制（适用于生产环境，需要 ModelScope 平台部署）
# - false: 关闭限制（适用于本地开发，无需登录）- 默认
ENABLE_USER_LIMIT=false
# 每位用户每天可使用的次数（仅在 ENABLE_USER_LIMIT=true 时生效）
DAILY_USAGE_LIMIT=3
```

> **提示**：项目已内置公益站密钥，可以直接使用，但有限额。建议申请自己的 API Key。

### 4. 启动服务

> **重要提示**：本项目采用**集成启动模式**，`app.py` 会自动启动 FastAPI 后端和 Gradio 前端，无需分别启动。

#### 方式一：直接启动（推荐）

```bash
python3 app.py
```

#### 方式二：使用启动脚本

```bash
bash start_services.sh
```

启动过程：
1. 🔧 FastAPI 服务器在后台线程启动（端口 8000）
2. ⏳ 等待 FastAPI 服务器就绪
3. 🌐 Gradio Web 界面启动（端口 7860）

### 5. 访问应用

打开浏览器访问：
- **Gradio Web 界面**：http://localhost:7860
- **FastAPI API 文档**：http://localhost:8000/docs
- **API 健康检查**：http://localhost:8000/health

## 📖 使用指南

### 文生图（Text-to-Image）

1. 进入 **"✨ 文生图"** 标签页
2. 输入提示词，例如：`一个胖橘猫在跳舞`
3. （可选）设置负向提示词、生成数量、风格、宽高比等参数
4. 点击 **"✨ 生成图片"** 按钮
5. 等待生成完成，查看结果

**参数说明：**
- **提示词**：描述想要生成的图片内容

- **负向提示词**：描述不想要的内容（如：模糊、低质量）

- **生成数量**：1-4 张

- **创造性**：0.0-1.0，越高越有创造性

- **宽高比**：1:1, 16:9, 9:16, 4:3, 3:4

- **风格**：realistic, anime, oil-painting, watercolor, sketch

  ![image-20251124003510879](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20251124003510879.png)

### 图生图（Image-to-Image）

1. 进入 **"🖼️ 图生图"** 标签页
2. 上传一张图片
3. 输入修改提示词，例如：`上面的橘猫头上带个皇冠`
4. （可选）设置变换强度、风格等参数
5. 点击 **"🎨 生成图片"** 按钮
6. 查看生成结果
7. （可选）点击 **"📋 复制到输入区继续修改"** 进行连续编辑

**参数说明：**
- **变换强度**：0.0-1.0，越高变化越大

- 其他参数与文生图相同

  ![image-20251124003438249](https://mypicture-1258720957.cos.ap-nanjing.myqcloud.com/Obsidian/image-20251124003438249.png)

### 系统设置

在 **"⚙️ 系统设置"** 标签页可以：
- 配置 Gemai API Key
- 设置 API Base URL
- 查看使用说明

## 📝 日志系统

项目使用 Python logging 模块进行日志记录，便于问题定位和调试。

### 日志文件位置

```
logs/
├── gradio_app.log        # Gradio 应用日志
└── fastapi_server.log    # FastAPI 服务日志
```

### 日志格式

```
[2025-11-24 22:11:36] INFO [GradioApp]: 用户限制功能已关闭，直接执行
[2025-11-24 22:11:36] WARNING [GradioApp]: 扣除使用次数失败
[2025-11-24 22:11:36] ERROR [GradioApp]: 更新使用记录失败: 测试错误
```

### 查看日志

```bash
# 查看 Gradio 应用日志
cat logs/gradio_app.log

# 查看 FastAPI 服务日志
cat logs/fastapi_server.log

# 实时跟踪日志
tail -f logs/gradio_app.log

# 搜索错误日志
grep "ERROR" logs/gradio_app.log
```

### 日志特性

- **双重输出**：同时输出到控制台和文件
- **自动轮转**：单个文件超过 10MB 自动创建新文件
- **备份保留**：最多保留 5 个备份文件
- **详细记录**：包含时间戳、日志级别、模块名称

> 详细说明请参考：[LOGGING_GUIDE.md](./LOGGING_GUIDE.md)

## 🔐 用户限制功能

项目支持可选的用户每日使用限制功能，适用于生产环境部署。

### 功能模式

| 模式 | 配置 | 适用场景 |
|------|------|---------|
| **本地开发模式**（默认） | `ENABLE_USER_LIMIT=false` | 本地测试、开发调试，无需登录，无限制 |
| **生产环境模式** | `ENABLE_USER_LIMIT=true` | ModelScope 部署，需要用户认证，每日限额 |

### 配置方法

```bash
# .env 文件配置
ENABLE_USER_LIMIT=true    # 启用用户限制
DAILY_USAGE_LIMIT=3       # 每日限制 3 次
```

### 数据存储

用户使用记录存储在 `data/daily_user_usage.json`：

```json
{
  "2025-11-24": {
    "user-123": 2,
    "user-456": 3
  }
}
```

> 详细说明请参考：[USAGE_LIMIT_GUIDE.md](./USAGE_LIMIT_GUIDE.md)

## 💡 提示词技巧

### 文生图示例

```
# 基础示例
一只可爱的橘猫在阳光下睡觉

# 带风格的示例
未来科技城市，霓虹灯，赛博朋克风格，高清，细节丰富

# 日本动漫风格
日本动漫风格的少女，樱花背景，柔和光线，精美细节

# 油画风格
油画风格的海边日落，温暖色调，印象派

# 英文示例
A cute robot playing with a cat in a garden, anime style, vibrant colors
```

### 图生图示例

```
# 风格转换
转换成动漫风格
Convert to watercolor painting style

# 添加元素
添加夕阳和温暖的光线
Add snow and winter atmosphere

# 改变氛围
让画面更加梦幻，添加星空背景
Make it more cyberpunk with neon lights
```

### 负向提示词示例

```
模糊、低质量、变形、噪点、丑陋
blurry, low quality, distorted, ugly, bad anatomy
```

## 🔧 API 接口

### 1. 健康检查
```bash
GET http://localhost:8000/health
```

### 2. 文生图
```bash
POST http://localhost:8000/text2img
Content-Type: application/json

{
  "prompt": "一只可爱的猫",
  "negative_prompt": "模糊",
  "num_images": 1,
  "temperature": 0.7,
  "aspect_ratio": "1:1",
  "style": "realistic"
}
```

### 3. 图生图
```bash
POST http://localhost:8000/img2img
Content-Type: application/json

{
  "prompt": "转换成动漫风格",
  "image_base64": "BASE64_ENCODED_IMAGE",
  "negative_prompt": "模糊",
  "strength": 0.7,
  "temperature": 0.7,
  "aspect_ratio": "1:1",
  "style": "anime"
}
```

### 4. 上传图片
```bash
POST http://localhost:8000/upload
Content-Type: multipart/form-data

file: <image_file>
```

详细 API 文档请访问：http://localhost:8000/docs

## 📸 生成的图片

所有生成的图片会自动保存到 `generated_images/` 目录，文件命名格式：
```
generated_20240101_123456_1234.png
```

## 🐳 Docker 部署

### 使用 Docker Compose（推荐）

```bash
# 构建并启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 使用 Docker

```bash
# 构建镜像
docker build -t gemai-nano-banana-pro:0.0.1 .

# 运行容器
docker run -d \
  --name gemai-nano-banana-pro \
  -p 8000:8000 \
  -p 7860:7860 \
  -e GEMAI_API_KEY=your_api_key \
  -v $(pwd)/generated_images:/app/generated_images \
  -v $(pwd)/logs:/app/logs \
  gemai-nano-banana-pro:0.0.1

# 查看日志
docker logs -f gemai-nano-banana-pro

# 停止容器
docker stop gemai-nano-banana-pro
```

**Docker 镜像信息：**
- 基础镜像：`python:3.11-slim`
- 版本：`0.0.1`
- 维护者：75271002@qq.com
- 暴露端口：8000 (FastAPI), 7860 (Gradio)

## 🛠️ 开发

### 架构说明

本项目采用**集成启动架构**：
- **主程序**：`app.py` - 程序唯一入口
- **后端模块**：`fastapi_server.py` - 提供 FastAPI 应用实例
- **启动方式**：`app.py` 在后台线程启动 FastAPI，主线程启动 Gradio
- **优势**：简化部署、单命令启动、适合容器化部署

### 项目参考

本项目基于以下项目构建：
- **aitop100_nano_banana**：项目架构和框架参考
- **gemai_image_generator.py**：Gemai API 集成参考

### 主要改进

1. **集成架构**：FastAPI 和 Gradio 集成在 app.py 中，单命令启动
2. **Web 界面**：从命令行工具升级为 Gradio Web 界面（支持 5.44.1 - 6.0.0+）
3. **API 服务**：使用 FastAPI 0.116.1 构建后端服务
4. **双模式支持**：同时支持文生图和图生图
5. **用户友好**：提供参数配置、提示词示例、进度显示等
6. **最新依赖**：使用最新稳定版本的依赖包，兼容 Gradio 6.0+
7. **Docker 支持**：完整的 Docker 和 Docker Compose 配置
8. **简化部署**：无需手动管理前后端进程
9. **版本兼容**：适配 Gradio 6.0+ 新版本 API 变更

## ❓ 常见问题

### 1. 服务器无法启动？
- 检查端口 8000 和 7860 是否被占用
- 确保已安装所有依赖：`pip install -r requirements.txt`
- 确保使用 Python 3.10+：`python3 --version`
- 查看启动日志，检查 FastAPI 是否成功启动

### 2. FastAPI 启动超时？
- 增加等待时间：修改 `app.py` 中的 `max_retries` 参数
- 检查 8000 端口是否被其他程序占用
- 查看日志文件：`logs/fastapi_server.log`

### 3. 图片生成失败？
- 检查 API Key 是否正确配置
- 查看日志文件：`logs/fastapi_server.log` 和 `logs/gradio_app.log`
- 确认网络连接正常

### 4. 生成按钮点击无响应？
- **本地开发**：确保 `.env` 文件中 `ENABLE_USER_LIMIT=false`（默认）
- **生产环境**：如果启用了用户限制，需要 ModelScope 平台请求头
- 查看控制台或日志文件中的错误信息：`logs/gradio_app.log`

### 5. 图片质量不理想？
- 优化提示词，使用更详细的描述
- 使用负向提示词排除不想要的元素
- 调整创造性参数（temperature）
- 尝试不同的风格参数

### 6. 生成速度慢？
- 图片生成需要时间，请耐心等待
- 使用公益站密钥可能有限流
- 建议申请自己的 API Key

### 7. 如何查看详细日志？
```bash
# 实时查看日志
tail -f logs/gradio_app.log
tail -f logs/fastapi_server.log

# 搜索错误
grep "ERROR" logs/*.log

# 查看特定时间的日志
grep "2025-11-24 22:" logs/gradio_app.log
```

### 8. Gradio 版本兼容性问题？
- 项目支持 Gradio 5.44.1 及以上版本（包括 6.0.0+）
- 如遇到 theme 相关错误，请确保使用最新版本的代码
- 推荐使用 Gradio 6.0.0+ 获得最佳体验
- 如需降级：`pip install gradio==5.44.1`

## 📝 更新日志

### v0.0.4 (2025-11-24)
- 📝 **日志系统**：用 logging 模块替换所有 print 语句，支持文件轮转和分级日志
- 🔐 **用户限制优化**：添加 `ENABLE_USER_LIMIT` 开关，支持本地开发模式（默认关闭限制）
- 🔧 **配置完善**：
  - 应用启动时自动初始化 `data/daily_user_usage.json`
  - 更新 `.env.example` 配置说明
- 📖 **文档更新**：
  - 新增 `LOGGING_GUIDE.md` 日志系统使用指南
  - 更新 `USAGE_LIMIT_GUIDE.md` 用户限制功能说明
  - 更新 `README.md` 添加日志和用户限制相关章节
- 🐛 **Bug 修复**：修复本地运行时因匿名用户被拦截导致生成按钮无响应的问题

### v0.0.3 (2025-11-24)
- 🔧 **Gradio 6.0 兼容性**：修复 Gradio 6.0.0 版本 theme 参数兼容性问题
- 📦 **依赖更新**：支持 Gradio 6.0.0+ 版本
- 🐛 **Bug 修复**：解决 `BlockContext.__init__() got an unexpected keyword argument 'theme'` 错误
- 📝 **文档更新**：更新 Python 版本要求说明（支持 3.10+）

### v0.0.2 (2025-11-23)
- 🔧 **架构优化**：集成 FastAPI 启动到 app.py
- 🚀 **简化部署**：单命令启动，无需分别管理前后端
- ⚡ **后台线程**：FastAPI 在后台线程运行，提高资源利用率
- 📦 **更新 Dockerfile**：简化为单命令启动
- 📝 **更新文档**：完善架构说明和使用指南

### v0.0.1 (2025-11-23)
- 🎉 首次发布
- ✨ 支持文生图和图生图
- 🌐 Gradio 5.44.1+ Web 界面
- ⚡ FastAPI 0.116.1 后端服务
- 🐳 完整的 Docker 支持
- 🔧 灵活的参数配置
- 📦 使用最新稳定版本依赖

## 📄 许可证

MIT License

## 🙏 致谢

- [Gemai 公益站](https://api.gemai.cc/register?aff=ND9Y) - 提供免费的 API 服务
- [Gradio](https://gradio.app) - 优秀的 Web UI 框架
- [FastAPI](https://fastapi.tiangolo.com) - 现代化的 Python Web 框架

## 📧 联系方式

如有问题或建议，欢迎提 Issue！

---

**Enjoy creating amazing images with AI! 🎨✨**
