# -*- coding: utf-8 -*-
"""
配置文件 - 用于同步前后端配置
"""
import os
import json
from pathlib import Path

# 读取JSON配置文件
BASE_DIR = Path(__file__).parent.absolute()
CONFIG_FILE = BASE_DIR / "config.json"

def load_config():
    """加载JSON配置文件"""
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"配置文件 {CONFIG_FILE} 不存在，使用默认配置")
        return get_default_config()
    except json.JSONDecodeError as e:
        print(f"配置文件格式错误: {e}，使用默认配置")
        return get_default_config()

def get_default_config():
    """获取默认配置"""
    return {
        "server": {
            "host": "0.0.0.0",
            "port": 8000,
            "debug": True
        },
        "api": {
            "title": "PDF解析服务",
            "description": "PDF上传和Markdown转换服务，支持AI图片描述",
            "version": "1.0.0"
        },
        "upload": {
            "allowed_extensions": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".pdf"],
            "max_file_size_mb": 50
        },
        "storage": {
            "pdf_dir": "uploads/pdfs",
            "markdown_dir": "uploads/markdown",
            "images_dir": "uploads/images",
            "temp_dir": "temp",
            "keep_original_files": True,
            "keep_markdown_files": True
        },
        "cors": {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"]
        }
    }

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

# API 配置
API_CONFIG = CONFIG["api"]

# CORS 配置
CORS_CONFIG = CONFIG["cors"]

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
