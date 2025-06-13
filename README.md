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
- **实时反馈**: 上传进度实时显示，错误信息详细反馈

### 🌐 Web 界面

- **用户友好界面**: 提供直观的 Web 操作界面
- **拖拽上传**: 支持文件拖拽上传和点击选择
- **实时预览**: 图片和文件信息实时预览
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
    ├── 📁 templates/              # HTML 模板 (Ant Design 风格)
    │   ├── 🏠 simple_index_antd.html      # 主页
    │   ├── 🖼️ simple_image_upload_antd.html # 图片上传页面
    │   ├── 📄 simple_pdf_upload_antd.html   # PDF上传页面
    │   └── 🎨 simple_base_antd.html        # 基础模板
    ├── 📁 uploads/                # 文件存储
    │   ├── 📁 pdfs/              # PDF 文件存储
    │   ├── 📁 images/            # 图片文件存储
    │   └── 📁 markdown/          # Markdown 文件存储
    └── 📁 temp/                   # 临时文件处理
```

## 🚀 快速开始

> **📋 当前状态**: 本项目已完成主要Bug修复和架构优化，前后端功能正常，无轮询机制，采用同步处理模式。

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

#### 🔴 开发模式 (直接启动)

```bash
python run_server.py
```

#### 🚀 生产模式 (使用 PM2 守护进程)

**安装 PM2:**

```bash
# 安装 PM2 (全局安装)
sudo npm install -g pm2

# 或者使用国内镜像
npm config set registry https://registry.npmmirror.com
sudo npm install -g pm2
```

**启动服务:**

```bash
# 使用 PM2 启动服务
pm2 start ecosystem.config.js

# 或使用便捷脚本
./pm2_commands.sh start

# 指定环境启动
pm2 start ecosystem.config.js --env production
./pm2_commands.sh env prod
```

**PM2 管理命令:**

```bash
# 查看服务状态
pm2 status
pm2 describe pdf-parse-server

# 查看日志
pm2 logs pdf-parse-server
pm2 logs pdf-parse-server --lines 100

# 重启服务
pm2 restart pdf-parse-server
pm2 reload pdf-parse-server  # 零停机重启

# 停止服务
pm2 stop pdf-parse-server

# 删除服务
pm2 delete pdf-parse-server

# 监控界面
pm2 monit

# 设置开机自启
pm2 startup
pm2 save
```

**便捷管理脚本:**

项目提供了 `pm2_commands.sh` 脚本来简化 PM2 操作：

```bash
# 查看帮助
./pm2_commands.sh

# 启动服务
./pm2_commands.sh start

# 查看状态
./pm2_commands.sh status

# 查看日志
./pm2_commands.sh logs

# 重启服务
./pm2_commands.sh restart

# 设置开机自启
./pm2_commands.sh startup
```

🎉 服务成功启动后，访问以下地址：

- **🏠 主页**: <http://localhost:10001/>
- **🖼️ 图片上传**: <http://localhost:10001/image>  
- **📄 PDF上传**: <http://localhost:10001/pdf>
- **📚 API文档**: <http://localhost:10001/docs>
- **📖 ReDoc文档**: <http://localhost:10001/redoc>

### 🧑‍💻 开发者快速验证

```bash
# 1. 测试API健康状态
curl http://localhost:10001/

# 2. 测试图片上传 (使用测试图片)
curl -X POST "http://localhost:10001/upload/image" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@assets/images/image.png"

# 3. 测试PDF处理 (使用测试PDF)
curl -X POST "http://localhost:10001/upload/pdf" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@assets/pdfs/simcse.pdf" \
     -F "provider=zhipu" \
     -F "process_images=true"
```

## 🏗️ 架构设计

### 处理模式

- **同步处理**: 文件上传后立即进行处理，无需轮询等待
- **实时反馈**: 前端直接获取处理结果，包括文件信息和访问URL
- **错误透明**: 处理失败时立即返回详细错误信息

### 核心组件

- **FastAPI Backend**: 高性能异步Web框架，提供RESTful API
- **MinerU Engine**: PDF解析核心，支持复杂文档结构
- **Multi-AI Integration**: 支持多家AI服务商的视觉分析能力
- **File Management**: 统一的文件处理和存储管理系统

### 安全机制

- **文件类型检查**: 严格的文件格式和大小限制
- **路径安全**: 防止目录遍历攻击
- **临时文件清理**: 自动清理处理过程中的临时文件
- **错误隔离**: 单个文件处理失败不影响其他文件

## 📡 API 接口说明

### 🖼️ 图片处理接口

#### `POST /upload/images`

批量上传图片文件进行 AI 智能分析

**请求参数:**

- **files**: 图片文件数组 (multipart/form-data)
- **provider** (可选): AI 提供商 (`guiji`|`zhipu`|`volces`|`openai`)
- **max_concurrent** (可选): 最大并发数 (默认: 5)

**响应示例:**

```json
{
  "message": "处理完成。成功: 2, 失败: 0",
  "uploaded_files": [
    {
      "original_filename": "image1.png",
      "filename": "abc123def456.png",
      "saved_filename": "abc123def456.png",
      "file_path": "/path/to/uploads/images/abc123def456.png",
      "url": "/uploads/images/abc123def456.png",
      "file_size": 102400,
      "content_type": "image/png"
    }
  ],
  "failed_files": []
}
```

#### `POST /upload/image`

上传单个图片文件

**请求参数:**

- **file**: 图片文件 (multipart/form-data)

**响应示例:**

```json
{
  "message": "文件上传成功",
  "file_info": {
    "original_filename": "image.png",
    "filename": "xyz789abc123.png",
    "saved_filename": "xyz789abc123.png",
    "file_path": "/path/to/uploads/images/xyz789abc123.png",
    "url": "/uploads/images/xyz789abc123.png",
    "file_size": 102400,
    "content_type": "image/png"
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
    "port": 10001,            // 服务端口
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

## 🔧 PM2 部署配置详解

### PM2 配置文件说明

项目使用 `ecosystem.config.js` 作为 PM2 的配置文件，包含以下重要配置：

#### 基本配置
```javascript
{
  name: 'pdf-parse-server',          // 应用名称
  script: 'run_server.py',           // 启动脚本
  interpreter: '/path/to/python',    // Python 解释器路径
  cwd: '/path/to/project',           // 工作目录
  instances: 1,                      // 实例数量
  max_memory_restart: '48G'          // 内存限制 (48GB)
}
```

#### 环境变量配置
- **开发环境** (`env`): DEBUG 模式，本地访问
- **生产环境** (`env_production`): 优化配置，对外访问
- **测试环境** (`env_development`): 调试模式，详细日志

#### 日志配置
```javascript
{
  out_file: './logs/out.log',        // 标准输出日志
  error_file: './logs/error.log',    // 错误日志
  log_file: './logs/combined.log',   // 合并日志
  time: true,                        // 时间戳
  log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
}
```

#### 重启策略
```javascript
{
  autorestart: true,                 // 自动重启
  min_uptime: '30s',                 // 最小运行时间
  max_restarts: 15,                  // 最大重启次数
  restart_delay: 4000,               // 重启延迟 (毫秒)
  kill_timeout: 10000                // 强制停止超时
}
```

### 生产环境部署步骤

#### 1. 系统环境准备
```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Node.js (用于 PM2)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs

# 安装 PM2
sudo npm install -g pm2
```

#### 2. Python 环境配置
```bash
# 创建专用用户 (可选)
sudo useradd -m -s /bin/bash pdfservice
sudo su - pdfservice

# 安装 Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 创建项目环境
conda create -n mineru python=3.10
conda activate mineru

# 安装依赖
pip install -r requirements.txt
```

#### 3. 项目部署
```bash
# 克隆项目
git clone <your-repo-url> /home/pdfservice/pdf-parse-server
cd /home/pdfservice/pdf-parse-server

# 配置环境变量
cp .env.example .env
nano .env  # 配置 API 密钥

# 创建必要目录
mkdir -p logs uploads/{pdfs,images,markdown} temp

# 设置权限
chmod +x pm2_commands.sh
```

#### 4. 启动和配置服务
```bash
# 启动服务
pm2 start ecosystem.config.js --env production

# 设置开机自启
pm2 startup
pm2 save

# 配置日志轮转
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 100M
pm2 set pm2-logrotate:retain 30
```

