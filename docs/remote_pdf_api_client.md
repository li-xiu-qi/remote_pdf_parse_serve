# ApiClient 文档

本文档详细介绍了 `utils/api_client.py` 中的 `ApiClient` 类的使用方法。该客户端是一个独立的 API 客户端，专门用于与 remote_pdf_parse_serve 后端服务交互，支持图片和 PDF 文件的上传及智能处理。

## 🚀 特性

- **简单易用**: 仅依赖 `requests` 库，易于集成到其他项目
- **文件上传**: 支持单个/批量图片上传和文件存储
- **PDF 智能处理**: 支持单个/批量 PDF 转 Markdown，可选择性进行图像 AI 分析
- **多解析后端**: 支持 pipeline 和 VLM 多种解析后端
- **多 AI 提供商**: PDF 处理支持多种 AI 提供商进行图像分析
- **健壮性强**: 完善的错误处理和超时控制
- **详细日志**: 丰富的处理过程输出，便于调试

## 📋 ApiClient 类

### 类常量

- **`DEFAULT_TIMEOUT_IMAGE`** (int): 图片上传的默认超时时间。默认值: `60` 秒
- **`DEFAULT_TIMEOUT_PDF`** (int): PDF 上传和处理的默认超时时间。默认值: `2400` 秒（40分钟）
- **`DEFAULT_PROVIDER`** (str): 默认的 AI 提供商。默认值: `'zhipu'`

### 构造函数

#### `__init__(self, base_url: str = "http://localhost:10001")`

初始化 ApiClient 实例。

**参数:**

- `base_url` (str): API 服务的基础 URL。默认为 `"http://localhost:10001"`

**示例:**

```python
# 使用默认本地地址
client = ApiClient()

# 使用自定义服务地址
client = ApiClient(base_url="http://192.168.1.100:10001")
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

---

## 📸 图片上传功能

### `upload_single_image()`

上传单个图片文件进行存储。

#### 方法签名

```python
def upload_single_image(self, image_path: Path, timeout: int = DEFAULT_TIMEOUT_IMAGE) -> Optional[Dict]
```

#### 参数

- `image_path` (Path): 要上传的图片文件的绝对路径
- `timeout` (int): 请求超时时间（秒）。默认: `60`

#### 返回值

- `Optional[Dict]`: 成功时返回包含文件信息的字典，失败时返回 `None`

#### 响应格式

```json
{
    "file_info": {
        "original_filename": "image.jpg",
        "stored_filename": "uuid_image.jpg", 
        "file_size": 12345,
        "url": "/uploads/images/uuid_image.jpg"
    }
}
```

#### 示例

```python
from pathlib import Path
from utils.api_client import ApiClient

client = ApiClient()

# 上传单个图片
image_path = Path("assets/images/photo.jpg")
result = client.upload_single_image(image_path)

if result:
    file_info = result['file_info']
    print(f"上传成功: {file_info['original_filename']}")
    print(f"访问地址: {file_info['url']}")
else:
    print("上传失败")
```

### `upload_multiple_images()`

批量上传多个图片文件进行存储。

#### 方法签名

```python
def upload_multiple_images(self, image_paths: List[Path], 
                         provider: str = DEFAULT_PROVIDER,
                         max_concurrent: int = 5,
                         timeout: int = DEFAULT_TIMEOUT_IMAGE) -> Optional[Dict]
```

#### 参数

- `image_paths` (List[Path]): 要上传的图片文件绝对路径列表
- `provider` (str): AI 提供商（预留参数）。默认: `'zhipu'`
- `max_concurrent` (int): 最大并发处理数。默认: `5`
- `timeout` (int): 请求超时时间（秒）。默认: `60`

#### 返回值

- `Optional[Dict]`: 成功时返回包含上传结果的字典，失败时返回 `None`

#### 响应格式

```json
{
    "uploaded_files": [
        {
            "original_filename": "image1.jpg",
            "stored_filename": "uuid1_image1.jpg",
            "file_size": 12345,
            "url": "/uploads/images/uuid1_image1.jpg"
        }
    ],
    "failed_files": []
}
```

#### 示例

```python
from pathlib import Path
from utils.api_client import ApiClient

client = ApiClient()

# 批量上传图片
image_files = [
    Path("assets/images/image1.jpg"),
    Path("assets/images/image2.png"),
    Path("assets/images/image3.gif")
]

result = client.upload_multiple_images(image_paths=image_files)

if result:
    uploaded = result.get('uploaded_files', [])
    failed = result.get('failed_files', [])
    print(f"成功上传: {len(uploaded)} 个文件")
    print(f"失败: {len(failed)} 个文件")
    
    # 显示上传成功的文件信息
    for file_info in uploaded:
        print(f"- {file_info['original_filename']} -> {file_info['url']}")
```

---

## 📄 PDF 处理功能

### `upload_pdf()`

上传单个 PDF 文件进行解析和转换。

#### 方法签名

```python
def upload_pdf(self, pdf_path: Path, 
               provider: str = DEFAULT_PROVIDER,
               backend: str = "pipeline",
               method: str = "auto",
               parse_images: bool = True, 
               max_concurrent: int = 5,
               use_cache: bool = True,
               timeout: int = DEFAULT_TIMEOUT_PDF) -> Optional[Dict]
```

#### 参数

- `pdf_path` (Path): 要上传的 PDF 文件的绝对路径
- `provider` (str): AI 提供商，用于图片分析。选项: `'guiji'`, `'zhipu'`, `'volces'`, `'openai'`。默认: `'zhipu'`
- `backend` (str): PDF 解析后端。选项: `'pipeline'`, `'vlm-transformers'`, `'vlm-sglang-engine'`, `'vlm-sglang-client'`。默认: `'pipeline'`
- `method` (str): PDF 解析方法。选项: `'auto'`, `'txt'`, `'ocr'`。默认: `'auto'`
- `parse_images` (bool): 是否对 PDF 中的图片进行 AI 分析。默认: `True`
- `max_concurrent` (int): AI 处理最大并发数。默认: `5`
- `use_cache` (bool): 是否使用缓存功能。默认: `True`
- `timeout` (int): 请求超时时间（秒）。默认: `2400`

#### 返回值

- `Optional[Dict]`: 成功时返回包含处理结果的字典，失败时返回 `None`

#### 响应格式

```json
{
    "document": {
        "original_name": "document.pdf",
        "stored_name": "uuid_document.pdf",
        "size_bytes": 123456,
        "mime_type": "application/pdf",
        "storage_path": "uploads/pdfs/uuid_document.pdf",
        "creation_timestamp": "2025-07-04T12:00:00.000000"
    },
    "markdown": {
        "content": "# 文档标题...",
        "path": "uploads/markdown/uuid_document.md",
        "has_images": true,
        "images_processed": true
    }
}
```

#### 示例

```python
from pathlib import Path
from utils.api_client import ApiClient

client = ApiClient()

# 上传并处理 PDF（启用图片AI分析和缓存）
pdf_path = Path("assets/pdfs/document.pdf")
result = client.upload_pdf(
    pdf_path=pdf_path,
    provider="zhipu",        # AI 提供商
    backend="pipeline",      # 解析后端
    method="auto",           # 解析方法
    parse_images=True,       # 启用图片 AI 分析
    max_concurrent=3,        # AI 处理并发数
    use_cache=True           # 启用缓存（默认）
)

if result:
    print("PDF 处理成功!")
    print(f"原始文件: {result['document']['original_name']}")
    
    # 保存 Markdown 内容到本地
    markdown_content = result.get('markdown', {}).get('content', '')
    if markdown_content:
        with open('converted_document.md', 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print("Markdown 内容已保存到 converted_document.md")

# 使用 VLM 后端处理（更快但需要GPU支持）
result_vlm = client.upload_pdf(
    pdf_path=pdf_path,
    backend="vlm-sglang-engine",  # VLM 后端
    parse_images=False,           # 关闭图片 AI 分析
    use_cache=True                # 启用缓存
)

# 强制重新解析（不使用缓存）
result_fresh = client.upload_pdf(
    pdf_path=pdf_path,
    use_cache=False              # 禁用缓存，强制重新解析
)
```

### `upload_multiple_pdfs()`

批量上传和处理多个 PDF 文件。

#### 方法签名

```python
def upload_multiple_pdfs(self, pdf_paths: List[Path], 
                        provider: str = DEFAULT_PROVIDER,
                        backend: str = "pipeline",
                        method: str = "auto",
                        parse_images: bool = True, 
                        max_concurrent: int = 5,
                        use_cache: bool = True,
                        timeout: int = DEFAULT_TIMEOUT_PDF) -> Optional[Dict]
```

#### 参数

- `pdf_paths` (List[Path]): 要上传的 PDF 文件绝对路径列表
- `provider` (str): AI 提供商。默认: `'zhipu'`
- `backend` (str): PDF 解析后端。默认: `'pipeline'`
- `method` (str): PDF 解析方法。默认: `'auto'`
- `parse_images` (bool): 是否处理图片。默认: `True`
- `max_concurrent` (int): AI 处理并发数。默认: `5`
- `use_cache` (bool): 是否使用缓存功能。默认: `True`
- `timeout` (int): 请求超时时间（秒）。默认: `2400`

#### 返回值

- `Optional[Dict]`: 成功时返回包含批量处理结果的字典，失败时返回 `None`

#### 响应格式

```json
{
    "message": "所有文件处理成功",
    "documents": [
      {
        "filename": "file1.pdf",
        "status": "success",
        "markdown": {
          "content": "# 文档标题1...",
          "metadata": {
            "header_level_1": ["标题1"],
            "header_level_2": ["副标题1"]
          }
        }
      },
      {
        "filename": "file2.pdf",
        "status": "success",
        "markdown": {
          "content": "# 文档标题2...",
          "metadata": {
            "header_level_1": ["标题2"],
            "header_level_2": ["副标题2"]
          }
        }
      }
    ],
    "failed_files": []
}
```

#### 示例

```python
from pathlib import Path
from utils.api_client import ApiClient

client = ApiClient()

# 批量处理 PDF 文件
pdf_files = [
    Path("assets/pdfs/document1.pdf"),
    Path("assets/pdfs/document2.pdf"),
    Path("assets/pdfs/document3.pdf")
]

result = client.upload_multiple_pdfs(
    pdf_paths=pdf_files,
    provider="zhipu",
    backend="pipeline",
    method="auto",
    parse_images=True,
    max_concurrent=3,
    use_cache=True           # 启用缓存
)

if result:
    results = result.get('results', [])
    print(f"批量处理完成: {len(results)} 个文件")
    
    # 保存所有成功处理的 Markdown 文件
    for idx, file_result in enumerate(results):
        markdown_content = file_result.get('markdown', {}).get('content')
        if markdown_content:
            original_name = file_result.get('document', {}).get('original_name', f"doc_{idx}")
            save_path = f"converted_{Path(original_name).stem}.md"
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            print(f"已保存: {save_path}")

# 第二次处理相同文件（会使用缓存，速度更快）
result_cached = client.upload_multiple_pdfs(
    pdf_paths=pdf_files,
    provider="zhipu",
    backend="pipeline", 
    method="auto",
    parse_images=True,
    use_cache=True           # 使用缓存
)

# 强制重新处理（不使用缓存）
result_fresh = client.upload_multiple_pdfs(
    pdf_paths=pdf_files,
    use_cache=False          # 禁用缓存
)
```

---

## 💾 缓存管理功能

### `get_cache_stats()`

获取PDF解析缓存的统计信息。

#### 方法签名

```python
def get_cache_stats(self) -> Optional[Dict]
```

#### 返回值

- `Optional[Dict]`: 成功时返回包含缓存统计信息的字典，失败时返回 `None`

#### 响应格式

```json
{
    "message": "缓存统计信息获取成功",
    "cache_stats": {
        "cache_size": 10,
        "cache_directory": "/home/user/.cache/remote_pdf_parse_serve",
        "disk_usage": 1073741824
    }
}
```

#### 示例

```python
from utils.api_client import ApiClient

client = ApiClient()

# 获取缓存统计信息
stats = client.get_cache_stats()

if stats:
    cache_info = stats.get('cache_stats', {})
    print(f"缓存项目数量: {cache_info.get('cache_size', 0)}")
    print(f"缓存目录: {cache_info.get('cache_directory', '')}")
    print(f"磁盘使用量: {cache_info.get('disk_usage', 0) / 1024 / 1024:.2f} MB")
else:
    print("获取缓存统计信息失败")
```

### `clear_cache()`

清理PDF解析缓存。

#### 方法签名

```python
def clear_cache(self) -> bool
```

#### 返回值

- `bool`: 如果成功清理缓存返回 `True`，否则返回 `False`

#### 示例

```python
from utils.api_client import ApiClient

client = ApiClient()

# 清理缓存
success = client.clear_cache()

if success:
    print("缓存清理成功")
else:
    print("缓存清理失败")
```

---

## 🔧 缓存功能说明

### 缓存机制

- **自动缓存**: 默认情况下，所有PDF解析结果都会被缓存，提高重复解析的速度
- **缓存容量**: 支持最大100GB的缓存空间
- **缓存过期**: 缓存项目默认7天后过期
- **缓存key**: 基于PDF文件前8KB内容和解析参数生成唯一标识

### 使用建议

1. **首次使用**: 第一次解析PDF会花费正常时间，并自动保存到缓存
2. **重复解析**: 相同PDF文件和参数的解析会从缓存中快速返回结果
3. **参数变化**: 不同的解析参数（backend、method等）会使用不同的缓存条目
4. **缓存管理**: 定期查看和清理缓存以释放磁盘空间

### 缓存控制

```python
# 启用缓存（默认）
result = client.upload_pdf(pdf_path, use_cache=True)

# 禁用缓存（强制重新解析）
result = client.upload_pdf(pdf_path, use_cache=False)

# 批量处理时也支持缓存控制
results = client.upload_multiple_pdfs(pdf_paths, use_cache=True)
```
