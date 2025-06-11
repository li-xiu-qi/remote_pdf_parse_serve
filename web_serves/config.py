# -*- coding: utf-8 -*-
"""
配置文件 - 用于同步前后端配置
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any

# 读取JSON配置文件
BASE_DIR = Path(__file__).parent.absolute()
CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    """加载JSON配置文件"""

    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


# 加载配置
CONFIG = load_config()

# 提取各部分配置
SERVER_CONFIG = CONFIG["server"]

# 文件路径配置
BASE_DIR = Path(__file__).parent.absolute()
UPLOAD_DIR = BASE_DIR / "uploads"
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# 存储配置
STORAGE_CONFIG = CONFIG["storage"]
PDF_DIR = BASE_DIR / STORAGE_CONFIG["pdf_dir"]
MARKDOWN_DIR = BASE_DIR / STORAGE_CONFIG["markdown_dir"]
IMAGES_DIR = BASE_DIR / STORAGE_CONFIG["images_dir"]
TEMP_DIR = BASE_DIR / STORAGE_CONFIG["temp_dir"]

# 确保目录存在
UPLOAD_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)
TEMPLATES_DIR.mkdir(exist_ok=True)
PDF_DIR.mkdir(parents=True, exist_ok=True)
MARKDOWN_DIR.mkdir(parents=True, exist_ok=True)
IMAGES_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)

# 允许的图片格式
ALLOWED_EXTENSIONS = set(CONFIG["upload"]["allowed_extensions"])
SUPPORTED_IMAGE_EXTENSIONS = set(CONFIG["upload"].get("supported_image_extensions", [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"])) # 新增
SUPPORTED_PDF_EXTENSIONS = set(CONFIG["upload"].get("supported_pdf_extensions", [".pdf"])) # 新增

# API 配置
API_CONFIG = CONFIG["api"]

# CORS 配置
CORS_CONFIG = CONFIG["cors"]

# AI 服务配置（新增）
AI_SERVICES_CONFIG = CONFIG.get("ai_services", {})
DEFAULT_IMAGE_PROVIDER = AI_SERVICES_CONFIG.get("default_image_provider", "zhipu")
DEFAULT_MAX_CONCURRENT_AI = AI_SERVICES_CONFIG.get("default_max_concurrent_ai", 3)
TITLE_MAX_LENGTH = AI_SERVICES_CONFIG.get("title_max_length", 20)
DESCRIPTION_MAX_LENGTH = AI_SERVICES_CONFIG.get("description_max_length", 100)

# 文件设置（新增）
FILE_SETTINGS_CONFIG = CONFIG.get("file_settings", {})
MAX_FILENAME_LENGTH = FILE_SETTINGS_CONFIG.get("max_filename_length", 50)
FILENAME_CLEAN_PATTERN = FILE_SETTINGS_CONFIG.get("filename_clean_pattern", "[^\\w\\u4e00-\\u9fff-]")
FILENAME_REPLACEMENT = FILE_SETTINGS_CONFIG.get("filename_replacement", "_")

# 日志配置
LOGGING_CONFIG = CONFIG.get("logging", {})
LOGGING_LEVEL = LOGGING_CONFIG.get("level", "INFO")
LOGGING_FORMAT = LOGGING_CONFIG.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

def get_api_base_url():
    """获取 API 基础 URL"""
    host = SERVER_CONFIG["host"]
    port = SERVER_CONFIG["port"]
    # 如果 host 是 0.0.0.0，在客户端应该使用 localhost
    if host == "0.0.0.0":
        host = "localhost"
    return f"http://{host}:{port}"

def get_storage_paths():
    """获取存储路径配置"""
    return {
        "pdf_dir": PDF_DIR,
        "markdown_dir": MARKDOWN_DIR,
        "images_dir": IMAGES_DIR,
        "temp_dir": TEMP_DIR,
        "keep_original_files": STORAGE_CONFIG.get("keep_original_files", True),
        "keep_markdown_files": STORAGE_CONFIG.get("keep_markdown_files", True)
    }

def get_unique_filename(original_filename: str, directory: Path) -> str:
    """生成唯一的文件名"""
    import uuid
    from pathlib import Path
    file_ext = Path(original_filename).suffix
    base_name = Path(original_filename).stem
    unique_name = f"{base_name}_{uuid.uuid4().hex[:8]}{file_ext}"
    # 确保文件名唯一
    counter = 0
    while (directory / unique_name).exists():
        counter += 1
        unique_name = f"{base_name}_{uuid.uuid4().hex[:8]}_{counter}{file_ext}"
    return unique_name

class LoggingConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.level: str = config_data.get("level", "INFO")
        self.format: str = config_data.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

class FileSettingsConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.max_filename_length: int = config_data.get("max_filename_length", 50)
        self.filename_clean_pattern: str = config_data.get("filename_clean_pattern", "[^\\w\\u4e00-\\u9fff-]")
        self.filename_replacement: str = config_data.get("filename_replacement", "_")

class UploadConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.allowed_extensions: List[str] = config_data.get("allowed_extensions", [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".pdf"])
        self.max_file_size_mb: int = config_data.get("max_file_size_mb", 50)
        self.supported_image_extensions: list = config_data.get("supported_image_extensions", [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"])
        self.supported_pdf_extensions: list = config_data.get("supported_pdf_extensions", [".pdf"])

class AIServiceConfig:
    def __init__(self, config_data: Dict[str, Any]):
        self.default_provider: str = config_data.get("default_provider", "local_mock")
        self.default_max_concurrent_ai: int = config_data.get("default_max_concurrent_ai", 10)
        self.title_max_length: int = config_data.get("title_max_length", 20)
        self.description_max_length: int = config_data.get("description_max_length", 100)

class AppConfig:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppConfig, cls).__new__(cls)
        return cls._instance

    def __init__(self, config_path: str = None):
        if hasattr(self, '_initialized') and self._initialized:
            return

        if config_path is None:
            # 默认路径为当前 config.py 文件所在目录
            base_dir = os.path.dirname(os.path.abspath(__file__))
            config_path = os.path.join(base_dir, "config.json")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
        except FileNotFoundError:
            # 如果 config.json 缺失或路径错误，使用默认配置
            config_data = {
                "app_name": "Remote PDF Parse Service",
                "app_version": "0.1.0",
                "logging": {"level": "INFO", "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"},
                "file_settings": {"max_filename_length": 50, "filename_clean_pattern": "[^\\\\w\\\\u4e00-\\\\u9fff-]", "filename_replacement": "_"},
                "upload": {"supported_image_extensions": [".jpg", ".jpeg", ".png"], "supported_pdf_extensions": [".pdf"]},
                "ai_services": {"default_provider": "local_mock", "default_max_concurrent_ai": 10, "title_max_length": 10, "description_max_length": 50}
            }
            # 可选：打印警告信息，提示使用了默认配置
            # print(f"Warning: Config file not found at {config_path}. Using default configuration.")

        self.app_name: str = config_data.get("app_name", "Default App")
        self.app_version: str = config_data.get("app_version", "0.0.1")
        
        self.logging = LoggingConfig(config_data.get("logging", {})) # 日志配置
        self.file_settings = FileSettingsConfig(config_data.get("file_settings", {})) # 文件设置
        self.upload = UploadConfig(config_data.get("upload", {})) # 上传配置
        self.ai_services = AIServiceConfig(config_data.get("ai_services", {})) # AI服务配置
        
        self._initialized = True

# 全局应用配置实例
app_config = AppConfig()
