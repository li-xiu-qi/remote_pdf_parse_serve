# ApiClient 文档


本文档详细介绍了 `utils/api_client.py` 中的 `ApiClient` 类的使用方法。该客户端是一个独立的 API 客户端，专门用于与 remote_pdf_parse_serve 后端服务交互，支持图片和 PDF 文件的上传及智能处理。

## 🚀 特性

- **简单易用**: 仅依赖 `requests` 库，易于集成到其他项目
- **文件上传**: 支持单个/批量图片上传和文件存储
- **PDF 智能处理**: 支持 PDF 转 Markdown 并可选择性进行图像 AI 分析
- **多 AI 提供商**: PDF 处理支持多种 AI 提供商进行图像分析
- **健壮性强**: 完善的错误处理和超时控制
- **详细日志**: 丰富的处理过程输出，便于调试

## 📋 ApiClient 类

### 类常量

- **`DEFAULT_TIMEOUT_IMAGE`** (int): 图片上传的默认超时时间。默认值: `60` 秒
- **`DEFAULT_TIMEOUT_PDF`** (int): PDF 上传和处理的默认超时时间。默认值: `2400` 秒（40分钟）
- **`DEFAULT_PROVIDER`** (str): 默认的 AI 提供商。默认值: `'zhipu'`

### 构造函数

#### `__init__(self, base_url: str = "http://localhost:8000")`

初始化 ApiClient 实例。

**参数:**

- `base_url` (str): API 服务的基础 URL。默认为 `"http://localhost:8000"`

**示例:**

```python
# 使用默认本地地址
client = ApiClient()

# 使用自定义服务地址
client = ApiClient(base_url="http://192.168.1.100:8000")
```

### 公共方法

#### `health_check(self) -> bool`

检查 API 服务器的健康状态。

**返回:**

- `bool`: 如果服务器正常运行返回 `True`，否则返回 `False`

**示例:**

```python
client = ApiClient()
if client.health_check():
    print("服务器正常运行")
else:
    print("服务器无法访问")
```

#### `upload_single_image(self, image_path: Path, timeout: int = DEFAULT_TIMEOUT_IMAGE) -> Optional[Dict]`

上传单个图片到 `/upload/image` 接口。

**参数:**

- `image_path` (Path): 要上传的图片文件的绝对路径
- `timeout` (int): 请求超时时间（秒）。默认为 `DEFAULT_TIMEOUT_IMAGE`

**返回:**

- `Optional[Dict]`: 成功时返回 API 的 JSON 响应，失败时返回 `None`

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

#### `upload_multiple_images(self, image_paths: List[Path], provider: str = DEFAULT_PROVIDER, max_concurrent: int = 5, timeout: int = DEFAULT_TIMEOUT_IMAGE) -> Optional[Dict]`

上传多个图片到 `/upload/images` 接口进行批量文件存储。

**注意:** 当前版本的 `/upload/images` 接口仅进行文件上传和存储，不包含 AI 智能分析功能。AI 分析功能仅在 PDF 处理中可用。

**参数:**

- `image_paths` (List[Path]): 要上传的图片文件绝对路径列表
- `provider` (str): AI 提供商参数（当前版本此参数不生效，保留用于向后兼容）
- `max_concurrent` (int): 并发处理数参数（当前版本此参数不生效，保留用于向后兼容）
- `timeout` (int): 请求超时时间（秒）。默认为 `DEFAULT_TIMEOUT_IMAGE`

**返回:**

- `Optional[Dict]`: 成功时返回 API 的 JSON 响应，失败时返回 `None`

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

#### `upload_pdf(self, pdf_path: Path, provider: str = DEFAULT_PROVIDER, process_images: bool = True, max_concurrent: int = 5, timeout: int = DEFAULT_TIMEOUT_PDF) -> Optional[Dict]`

上传 PDF 文件到 `/upload/pdf` 接口进行处理和转换。

**参数:**

- `pdf_path` (Path): 要上传的 PDF 文件的绝对路径
- `provider` (str): AI 提供商。支持 `'guiji'`, `'zhipu'`, `'volces'`, `'openai'`。默认为 `DEFAULT_PROVIDER`
- `process_images` (bool): 是否处理 PDF 中的图片。默认为 `True`
- `max_concurrent` (int): AI 并发处理数。默认为 `5`
- `timeout` (int): 请求超时时间（秒）。默认为 `DEFAULT_TIMEOUT_PDF`

**返回:**

- `Optional[Dict]`: 成功时返回 API 的 JSON 响应，失败时返回 `None`

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

## 🚀 快速开始

### 基本使用

```python
from pathlib import Path
from utils.api_client import ApiClient

# 1. 创建客户端实例
client = ApiClient(base_url="http://localhost:8000")

# 2. 检查服务器状态
if not client.health_check():
    print("服务器无法访问，请检查服务是否启动")
    exit(1)

# 3. 上传单个图片
image_path = Path("path/to/your/image.png")
result = client.upload_single_image(image_path)
if result:
    print(f"上传成功: {result['file_info']['url']}")
```

### 高级用法

```python
from pathlib import Path
from utils.api_client import ApiClient

client = ApiClient()

# 批量上传图片（仅文件存储，无 AI 分析）
image_files = [
    Path("assets/images/image1.jpg"),
    Path("assets/images/image2.png"),
    Path("assets/images/image3.gif")
]

result = client.upload_multiple_images(
    image_paths=image_files,
    timeout=120              # 设置超时时间
)

if result:
    uploaded = result.get('uploaded_files', [])
    failed = result.get('failed_files', [])
    print(f"成功上传: {len(uploaded)} 个文件")
    print(f"失败: {len(failed)} 个文件")
    
    # 显示上传成功的文件信息
    for file_info in uploaded:
        print(f"- {file_info['original_filename']} -> {file_info['url']}")
```

### PDF 处理示例

```python
from pathlib import Path
from utils.api_client import ApiClient

client = ApiClient()

# 上传并处理 PDF（启用图片AI分析）
pdf_path = Path("assets/pdfs/document.pdf")
result = client.upload_pdf(
    pdf_path=pdf_path,
    provider="zhipu",        # AI 提供商（用于图片分析）
    process_images=True,     # 启用图片 AI 分析
    max_concurrent=5         # AI 处理并发数
)

if result:
    print("PDF 处理成功!")
    print(f"原始文件: {result['file_info']['original_filename']}")
    print(f"存储文件: {result['file_info']['stored_filename']}")
    print(f"Markdown 路径: {result['file_info']['markdown_path']}")
    print(f"是否处理图片: {result['file_info']['process_images']}")
    
    # 保存 Markdown 内容到本地
    markdown_content = result.get('markdown_content', '')
    if markdown_content:
        with open('converted_document.md', 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print("Markdown 内容已保存到 converted_document.md")

# 仅转换 PDF 为 Markdown（不进行图片分析）
result_no_ai = client.upload_pdf(
    pdf_path=pdf_path,
    process_images=False     # 关闭图片 AI 分析
)

if result_no_ai:
    print("PDF 转换完成（无 AI 分析）")
    processing_info = result_no_ai.get('processing_info', {})
    print(f"PDF 转换: {processing_info.get('pdf_converted')}")
    print(f"图片处理: {processing_info.get('images_processed')}")
```

## 🔧 错误处理

### 常见错误类型

1. **连接错误**: 服务器无法访问
2. **超时错误**: 请求处理时间过长
3. **文件错误**: 文件不存在或格式不支持
4. **API 错误**: 服务器返回错误状态码

### 错误处理示例

```python
from pathlib import Path
from utils.api_client import ApiClient

client = ApiClient()

# 带错误处理的上传示例
def safe_upload_image(image_path: Path) -> bool:
    """安全上传图片，包含完整错误处理"""
    try:
        # 检查文件是否存在
        if not image_path.exists():
            print(f"错误: 文件不存在 - {image_path}")
            return False
        
        # 检查服务器状态
        if not client.health_check():
            print("错误: 服务器无法访问")
            return False
        
        # 上传文件
        result = client.upload_single_image(image_path)
        if result:
            print(f"上传成功: {result['file_info']['url']}")
            return True
        else:
            print("上传失败: API 返回错误")
            return False
            
    except Exception as e:
        print(f"上传过程中发生异常: {e}")
        return False

# 使用示例
image_file = Path("test_image.png")
if safe_upload_image(image_file):
    print("图片上传完成")
else:
    print("图片上传失败")
```

## 📊 API 接口功能对比

| 接口 | 功能 | AI 分析 | 用途 |
|------|------|---------|------|
| `/upload/image` | 单个图片上传 | ❌ | 图片文件存储 |
| `/upload/images` | 批量图片上传 | ❌ | 批量图片文件存储 |
| `/upload/pdf` | PDF 处理 | ✅ (可选) | PDF 转 Markdown + 图片 AI 分析 |

### AI 提供商支持

**仅在 PDF 处理时可用:**

| 提供商 | 标识符 |
|--------|---------|
| **智谱AI** | `zhipu` |
| **硅基流动** | `guiji` |
| **豆包** | `volces` |
| **OpenAI** | `openai` |

## 🎯 最佳实践

### 1. 超时设置

```python
# 根据文件大小调整超时时间
large_pdf = Path("large_document.pdf")
file_size_mb = large_pdf.stat().st_size / (1024 * 1024)

# 大文件使用更长超时时间
timeout = max(2400, int(file_size_mb * 60))  # 每MB给60秒
result = client.upload_pdf(large_pdf, timeout=timeout)
```

### 2. 批量文件上传优化

```python
# 分批处理大量图片文件
from pathlib import Path

def batch_upload_images(image_dir: Path, batch_size: int = 10):
    """分批上传图片，避免一次性处理过多文件"""
    image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))
    
    for i in range(0, len(image_files), batch_size):
        batch = image_files[i:i + batch_size]
        print(f"处理批次 {i//batch_size + 1}: {len(batch)} 个文件")
        
        result = client.upload_multiple_images(
            image_paths=batch,
            timeout=120  # 适当调整超时时间
        )
        
        if result:
            uploaded = len(result.get('uploaded_files', []))
            print(f"批次完成: {uploaded} 个文件上传成功")

# PDF 处理中的 AI 分析优化
def process_pdf_with_ai_analysis(pdf_path: Path, enable_ai: bool = True):
    """处理PDF，可选择性启用AI分析"""
    result = client.upload_pdf(
        pdf_path=pdf_path,
        provider="zhipu",
        process_images=enable_ai,  # 根据需要开关AI分析
        max_concurrent=3           # 控制AI并发数
    )
    return result
```

### 3. 结果验证

```python
def validate_upload_result(result: dict, expected_count: int = 1) -> bool:
    """验证上传结果的完整性"""
    if not result:
        return False
    
    # 单个文件上传
    if expected_count == 1:
        return 'file_info' in result and 'url' in result['file_info']
    
    # 批量文件上传
    uploaded_files = result.get('uploaded_files', [])
    failed_files = result.get('failed_files', [])
    
    return len(uploaded_files) == expected_count and len(failed_files) == 0
```
