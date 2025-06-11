# Remote PDF Parse Service

🚀 一个基于 FastAPI 的智能 PDF 解析和图片处理服务，能够将 PDF 文件转换为 Markdown 格式，并使用多种 AI 视觉模型对图片进行智能分析和描述。

## ✨ 功能特性

### 📄 PDF 智能处理

- **PDF转Markdown**: 使用 MinerU 技术将 PDF 精确转换为 Markdown 格式
- **图片自动提取**: 自动提取 PDF 中的图片并保存到指定目录
- **AI图片分析**: 可选使用 AI 视觉模型生成图片的智能描述和标题
- **路径自动替换**: 将本地图片路径替换为远程访问 URL
- **多提供商支持**: 支持 GUIJI、智谱AI、豆包、OpenAI 等多种 AI 服务提供商

### 🖼️ 图片处理功能

- **批量上传**: 支持单个或多个图片文件同时上传
- **智能分析**: AI 自动生成图片标题和详细描述
- **多格式支持**: 支持 JPG、PNG、GIF、BMP、WebP 等常见格式
- **异步处理**: 高并发异步处理，提升处理效率

### 🌐 Web 界面

- **用户友好界面**: 提供直观的 Web 操作界面
- **实时反馈**: 处理进度实时显示
- **API 文档**: 完整的 Swagger UI 和 ReDoc 接口文档

## 🛠️ 技术栈

- **后端框架**: FastAPI (高性能异步 Web 框架)
- **PDF 处理**: MinerU、magic-pdf (先进的 PDF 解析技术)
- **AI 视觉模型**: 多提供商 API 集成
- **异步处理**: aiohttp、aiofiles (高效异步 I/O)
- **图像处理**: Pillow (专业图像处理库)
- **深度学习**: PyTorch、Transformers (AI 模型支持)

## 📁 项目结构

```
remote_pdf_parse_serve/
├── 📄 README.md                    # 项目说明文档
├── 📄 requirements.txt             # 依赖包清单
├── 🚀 run_server.py                # 服务器启动脚本
├── 📁 assets/                      # 测试资源文件
│   ├── 📁 pdfs/                   # 测试 PDF 文件
│   └── 📁 images/                 # 测试图片文件
├── 📁 tests/                      # 自动化测试
│   ├── 🧪 test_api_pdf.py         # PDF 接口测试
│   └── 🧪 test_api_image.py       # 图片接口测试
├── 📁 utils/                      # 通用工具
│   └── 🔧 download_mineru_models.py
└── 📁 web_serves/                 # 核心服务代码
    ├── 🎯 app.py                  # FastAPI 应用入口
    ├── ⚙️ config.py               # 配置管理
    ├── ⚙️ config.json             # 主配置文件
    ├── ❌ exceptions.py           # 自定义异常
    ├── 📁 routers/                # API 路由模块
    │   ├── 📄 pdf_processing.py   # PDF 处理路由
    │   └── 🖼️ image_upload.py     # 图片上传路由
    ├── 📁 utils/                  # 工具模块
    │   ├── 📂 file_handler.py     # 文件处理工具
    │   └── 📝 logger.py           # 日志管理
    ├── 📁 pdf_utils/              # PDF 处理模块
    │   └── 🔄 mineru_parse.py     # MinerU PDF 解析
    ├── 📁 image_utils/            # 图像分析模块
    │   ├── 🤖 async_image_analysis.py    # 异步图像分析
    │   ├── 🔧 image_analysis_utils.py    # 图像分析工具
    │   └── 💬 prompts.py                 # AI 提示词管理
    ├── 📁 markdown_utils/         # Markdown 处理
    │   ├── 🔄 markdown_image_processor.py
    │   └── 📝 update_markdown_with_analysis.py
    ├── 📁 static/                 # 静态文件
    ├── 📁 templates/              # HTML 模板
    ├── 📁 uploads/                # 文件存储
    │   ├── 📁 pdfs/              # PDF 文件存储
    │   ├── 📁 images/            # 图片文件存储
    │   └── 📁 markdown/          # Markdown 文件存储
    └── 📁 temp/                   # 临时文件处理
```

## 🚀 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd remote_pdf_parse_serve

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 环境配置

创建 `.env` 文件并配置 AI 服务密钥（至少配置一个）：

```env
# 🤖 GUIJI (硅基流动) API
GUIJI_API_KEY=your_guiji_api_key_here
GUIJI_BASE_URL=https://api.siliconflow.cn/v1/
GUIJI_VISION_MODEL=Pro/Qwen/Qwen2.5-VL-7B-Instruct

# 🧠 智谱 AI
ZHIPU_API_KEY=your_zhipu_api_key_here  
ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4/
ZHIPU_VISION_MODEL=glm-4v-flash

# 🌋 豆包 (Volces)
VOLCES_API_KEY=your_volces_api_key_here
VOLCES_BASE_URL=https://ark.cn-beijing.volces.com/api/v3/
VOLCES_VISION_MODEL=doubao-1.5-vision-lite-250315

# 🔥 OpenAI
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_API_BASE=https://api.openai.com/v1/
OPENAI_VISION_MODEL=gpt-4o
```

### 3. 下载模型 (可选)

```bash
python utils/download_mineru_models.py
```

### 4. 启动服务

```bash
python run_server.py
```

🎉 服务成功启动后，访问以下地址：

- **🏠 主页**: <http://localhost:8000/>
- **🖼️ 图片上传**: <http://localhost:8000/image>  
- **📄 PDF上传**: <http://localhost:8000/pdf>
- **📚 API文档**: <http://localhost:8000/docs>
- **📖 ReDoc文档**: <http://localhost:8000/redoc>

## 📡 API 接口说明

### 🖼️ 图片处理接口

#### `POST /upload/image`

上传图片文件进行 AI 智能分析

**请求参数:**

- **files**: 图片文件 (multipart/form-data)
- **provider** (可选): AI 提供商 (`guiji`|`zhipu`|`volces`|`openai`)
- **max_concurrent** (可选): 最大并发数 (默认: 5)

**响应示例:**

```json
{
  "message": "图片上传和分析成功",
  "uploaded_files": [
    {
      "original_filename": "image.png",
      "stored_filename": "processed_image.png", 
      "file_size": 102400,
      "remote_url": "http://localhost:8000/uploads/images/processed_image.png",
      "ai_analysis": {
        "title": "美丽的日落风景",
        "description": "这是一张展现了温暖日落时分的美丽风景图片..."
      }
    }
  ],
  "processing_info": {
    "total_files": 1,
    "successful_uploads": 1,
    "ai_analysis_completed": true
  }
}
```

### 📄 PDF 处理接口

#### `POST /upload/pdf`

上传 PDF 文件，转换为 Markdown 并进行图片智能分析

**请求参数:**

- **file**: PDF 文件 (multipart/form-data)
- **provider** (可选): AI 提供商 (默认: `zhipu`)
- **process_images** (可选): 是否处理图片 (默认: `true`)
- **max_concurrent** (可选): AI 并发数 (默认: 5)

**响应示例:**

```json
{
  "message": "PDF处理成功",
  "processing_id": "abc123def456",
  "file_info": {
    "original_filename": "document.pdf",
    "stored_filename": "document_processed.pdf",
    "file_size": 2048000,
    "content_type": "application/pdf",
    "pdf_path": "uploads/pdfs/document_processed.pdf",
    "markdown_path": "uploads/markdown/document_abc123def456.md",
    "creation_time": "2024-12-01T10:00:00",
    "provider": "zhipu",
    "process_images": true
  },
  "markdown_content": "# 文档标题\n\n这是转换后的 Markdown 内容...",
  "processing_info": {
    "pdf_converted": true,
    "images_processed": true,
    "remote_base_url": "http://localhost:8000/uploads/images/",
    "temp_directory_cleaned": true
  }
}
```

## 🧪 测试

### 运行测试套件

```bash
# 测试 PDF 处理功能
python tests/test_api_pdf.py

# 测试图片上传功能
python tests/test_api_image.py
```

### 准备测试文件

确保测试资源文件存在：

- `assets/pdfs/simcse.pdf` - 测试 PDF 文件
- `assets/images/` - 测试图片文件目录

## ⚙️ 配置详解

### 主配置文件: `web_serves/config.json`

```json
{
  "server": {
    "host": "0.0.0.0",        // 服务监听地址
    "port": 8000,             // 服务端口
    "debug": true             // 调试模式
  },
  "api": {
    "title": "PDF解析和图片处理服务",
    "description": "一个支持PDF解析、图片上传和AI图像分析的 FastAPI 服务",
    "version": "1.0.0"
  },
  "upload": {
    "allowed_extensions": [    // 支持的文件格式
      ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".pdf"
    ],
    "max_file_size_mb": 50,   // 最大文件大小 (MB)
    "supported_image_extensions": [
      ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"
    ],
    "supported_pdf_extensions": [".pdf"]
  },
  "storage": {
    "pdf_dir": "uploads/pdfs",           // PDF 存储目录
    "markdown_dir": "uploads/markdown",  // Markdown 存储目录
    "images_dir": "uploads/images",      // 图片存储目录  
    "temp_dir": "temp",                  // 临时文件目录
    "keep_original_files": true,         // 保留原始文件
    "keep_markdown_files": true          // 保留 Markdown 文件
  },
  "ai_services": {
    "default_provider": "zhipu",         // 默认 AI 提供商
    "default_max_concurrent_ai": 5,      // 默认并发数
    "title_max_length": 100,             // 标题最大长度
    "description_max_length": 500        // 描述最大长度
  }
}
```

### AI 服务提供商配置

| 提供商 | 模型示例 | 特点 |
|--------|----------|------|
| **GUIJI(硅基流动)** | `Pro/Qwen/Qwen2.5-VL-7B-Instruct` | 高性能，支持中文，性价比高 |
| **智谱AI** | `glm-4v-flash` | 快速响应，中文优化 |
| **豆包(Volces)** | `doubao-1.5-vision-lite-250315` | 轻量化，成本低 |
| **OpenAI** | `gpt-4o` | 精度高，功能全面 |
