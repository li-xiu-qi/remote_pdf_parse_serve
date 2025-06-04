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
from web_serves.routers import system, image_upload, pdf_processing


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
    return templates.TemplateResponse("index.html", {
        "request": request,
        "api_base_url": get_api_base_url(),
        "config": CONFIG
    })

@app.get("/image", response_class=HTMLResponse)
async def image_upload_page(request: Request):
    """图片上传页面"""
    from web_serves.config import get_api_base_url, CONFIG
    return templates.TemplateResponse("image_upload.html", {
        "request": request,
        "api_base_url": get_api_base_url(),
        "config": CONFIG
    })

@app.get("/pdf", response_class=HTMLResponse)
async def pdf_upload_page(request: Request):
    """PDF上传页面"""
    from web_serves.config import get_api_base_url, CONFIG
    return templates.TemplateResponse("pdf_upload.html", {
        "request": request,
        "api_base_url": get_api_base_url(),
        "config": CONFIG
    })

# 注册路由
app.include_router(system.router)
app.include_router(image_upload.router)
app.include_router(pdf_processing.router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "web_serves.app:app", 
        host=SERVER_CONFIG["host"], 
        port=SERVER_CONFIG["port"], 
        reload=SERVER_CONFIG["debug"]
    )
