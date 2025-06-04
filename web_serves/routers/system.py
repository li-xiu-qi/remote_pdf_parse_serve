#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
系统相关路由（健康检查、配置信息等）
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from web_serves.config import ALLOWED_EXTENSIONS, BASE_DIR, CONFIG, SERVER_CONFIG, get_api_base_url


router = APIRouter(tags=["系统"])


@router.get("/")
async def root():
    """根路径，返回 API 信息"""
    return {
        "message": "PDF解析和图片处理服务 API",
        "version": "1.0.0",
        "endpoints": {
            "upload_image": "/upload/image",
            "upload_images": "/upload/images",
            "upload_pdf": "/upload/pdf",
            "health": "/health"
        }
    }


@router.get("/health")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "service": "pdf-parse-service"}


@router.get("/config")
async def get_config():
    """获取前端配置"""
    return {
        "api_base_url": get_api_base_url(),
        "server": {
            "host": SERVER_CONFIG["host"],
            "port": SERVER_CONFIG["port"]
        },
        "upload": {
            "allowed_extensions": list(ALLOWED_EXTENSIONS),
            "max_file_size_mb": CONFIG["upload"]["max_file_size_mb"]
        }
    }


@router.get("/test.html", response_class=HTMLResponse)
async def serve_test_page():
    """提供测试页面"""
    test_html_path = BASE_DIR / "test.html"
    
    if not test_html_path.exists():
        raise HTTPException(status_code=404, detail="测试页面不存在")
    
    # 读取 HTML 文件并替换 API_BASE_URL
    with open(test_html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 动态替换 API 基础 URL
    api_base_url = get_api_base_url()
    html_content = html_content.replace(
        "const API_BASE_URL = 'http://localhost:8000';",
        f"const API_BASE_URL = '{api_base_url}';"
    )
    
    return HTMLResponse(content=html_content)
