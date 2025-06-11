# API Client Documentation

<!-- filepath: c:\Users\k\Documents\project\programming_project\python_project\importance\remote_pdf_parse_serve\docs\api_client.md -->

本文档介绍了 `utils/api_client.py` 中 `ApiClient` 类的使用方法。
该客户端用于与后端 API 交互，支持图片和 PDF 文件的上传。

## `ApiClient` 类

用于与后端API交互的客户端，支持图片和PDF上传。

### 类常量

- `DEFAULT_TIMEOUT_IMAGE` (int): 单个图片上传的默认超时时间（秒）。默认值: `60`。
- `DEFAULT_TIMEOUT_PDF` (int): PDF 上传和处理的默认超时时间（秒）。默认值: `2400`。
- `DEFAULT_PROVIDER` (str): 默认的 AI 提供商。默认值: `'zhipu'`。

### `__init__(self, base_url: str = "http://localhost:8000")`

初始化 ApiClient。

- **参数**:
  - `base_url` (str): API 的基础 URL (例如 `"http://localhost:8000"`)。默认为 `"http://localhost:8000"`。

### `_get_content_type(self, file_path: Path) -> str`

根据文件扩展名获取 Content-Type。这是一个内部辅助方法。

- **参数**:
  - `file_path` (Path): 文件的路径。
- **返回**:
  - `str`: 文件的 Content-Type 字符串。例如 `'image/png'`, `'application/pdf'`。

### `upload_single_image(self, image_path: Path, timeout: int = DEFAULT_TIMEOUT_IMAGE) -> dict | None`

上传单个图片到 `/upload/image` 接口。

- **参数**:
  - `image_path` (Path): 要上传的图片的绝对路径。
  - `timeout` (int): 请求超时时间（秒）。默认为 `ApiClient.DEFAULT_TIMEOUT_IMAGE`。
- **返回**:
  - `dict | None`: 如果成功，返回 API 的 JSON 响应，否则返回 `None`。

### `upload_multiple_images(self, image_paths: list[Path], timeout: int = DEFAULT_TIMEOUT_IMAGE) -> dict | None`

上传多个图片到 `/upload/images` 接口。

- **参数**:
  - `image_paths` (list[Path]): 要上传的图片绝对路径列表。
  - `timeout` (int): 请求超时时间（秒）。默认为 `ApiClient.DEFAULT_TIMEOUT_IMAGE`。
- **返回**:
  - `dict | None`: 如果成功，返回 API 的 JSON 响应，否则返回 `None`。

### `upload_pdf(self, pdf_path: Path, provider: str = DEFAULT_PROVIDER, process_images: bool = False, timeout: int = DEFAULT_TIMEOUT_PDF) -> dict | None`

上传 PDF 文件到 `/upload/pdf` 接口进行处理。

- **参数**:
  - `pdf_path` (Path): 要上传的 PDF 文件的绝对路径。
  - `provider` (str): 使用的 AI 提供商 (例如 `'zhipu'`, `'mineru'`)。默认为 `ApiClient.DEFAULT_PROVIDER`。
  - `process_images` (bool): 是否处理 PDF 中的图片。默认为 `False`。
  - `timeout` (int): 请求超时时间（秒）。默认为 `ApiClient.DEFAULT_TIMEOUT_PDF`。
- **返回**:
  - `dict | None`: 如果成功，返回 API 的 JSON 响应，否则返回 `None`。

## 使用示例

```python
from pathlib import Path
from utils.api_client import ApiClient

# 初始化客户端
client = ApiClient(base_url="http://localhost:8000")

# 上传单个图片
image_file = Path("path/to/your/image.png")
response_single_image = client.upload_single_image(image_file)
if response_single_image:
    print("单个图片上传成功:", response_single_image)

# 上传多个图片
image_files = [Path("path/to/image1.jpg"), Path("path/to/image2.png")]
response_multiple_images = client.upload_multiple_images(image_files)
if response_multiple_images:
    print("多个图片上传成功:", response_multiple_images)

# 上传 PDF
pdf_file = Path("path/to/your/document.pdf")
response_pdf = client.upload_pdf(pdf_file, provider="zhipu", process_images=True)
if response_pdf:
    print("PDF 上传成功:", response_pdf)
```
