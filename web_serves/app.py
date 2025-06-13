#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
主应用入口文件
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from web_serves.config import API_CONFIG, BASE_DIR, CORS_CONFIG, SERVER_CONFIG
from web_serves.routers import image_upload, pdf_processing


# 创建FastAPI应用实例
app = FastAPI(**API_CONFIG)

# 添加 CORS 中间件
app.add_middleware(CORSMiddleware, **CORS_CONFIG)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
# 挂载上传文件目录，使其可以通过HTTP访问
app.mount("/uploads", StaticFiles(directory=str(BASE_DIR / "uploads")), name="uploads")

# 配置模板
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 页面路由
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页 - 完整功能页面"""
    from web_serves.config import get_api_base_url, CONFIG
    return templates.TemplateResponse("simple_index_antd.html", {
        "request": request,
        "api_base_url": get_api_base_url(),
        "config": CONFIG
    })

@app.get("/image", response_class=HTMLResponse)
async def image_upload_page(request: Request):
    """图片上传页面"""
    from web_serves.config import get_api_base_url, CONFIG
    return templates.TemplateResponse("simple_image_upload_antd.html", {
        "request": request,
        "api_base_url": get_api_base_url(),
        "config": CONFIG
    })

@app.get("/pdf", response_class=HTMLResponse)
async def pdf_upload_page(request: Request):
    """PDF上传页面"""
    from web_serves.config import get_api_base_url, CONFIG
    return templates.TemplateResponse("simple_pdf_upload_antd.html", {
        "request": request,
        "api_base_url": get_api_base_url(),
        "config": CONFIG
    })

# API 配置端点
@app.get("/api/config")
async def get_frontend_config():
    """获取前端配置信息"""
    from web_serves.config import CONFIG, get_api_base_url
    
    frontend_config = CONFIG.get("frontend", {})
    upload_config = CONFIG.get("upload", {})
    
    return {
        "api_base_url": get_api_base_url(),
        "max_file_size": frontend_config.get("max_file_size", 52428800),  # 50MB
        "supported_image_formats": frontend_config.get("supported_image_formats", ["jpg", "jpeg", "png", "gif", "bmp", "webp"]),
        "supported_pdf_formats": frontend_config.get("supported_pdf_formats", ["pdf"]),
        "upload_timeout": frontend_config.get("upload_timeout", 300000),  # 5分钟
        "concurrent_uploads": frontend_config.get("concurrent_uploads", 3),
        "auto_save_interval": frontend_config.get("auto_save_interval", 30000),
        "preview_max_height": frontend_config.get("preview_max_height", 400),
        "notification_duration": frontend_config.get("notification_duration", {
            "success": 5000,
            "error": 8000,
            "warning": 6000,
            "info": 5000
        }),
        "max_file_size_mb": upload_config.get("max_file_size_mb", 50),
        "allowed_extensions": upload_config.get("allowed_extensions", [])
    }

# 调试端点
@app.get("/debug/config")
async def debug_config():
    """调试配置信息"""
    from web_serves.config import get_api_base_url, SERVER_CONFIG
    return {
        "api_base_url": get_api_base_url(),
        "server_config": SERVER_CONFIG,
        "template_vars": {
            "api_base_url": get_api_base_url()
        }
    }

# 注册路由
app.include_router(image_upload.router)
app.include_router(pdf_processing.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web_serves.app:app",
        host=SERVER_CONFIG.get("host"),
        port=SERVER_CONFIG.get("port"),
        reload=SERVER_CONFIG.get("debug")
    )
