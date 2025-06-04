#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动服务器脚本
"""
import uvicorn
import time

from web_serves.config import SERVER_CONFIG, get_api_base_url
from web_serves.app import app



def main():
    """启动服务器"""
    print(f"🚀 启动图片上传服务...")
    print(f"📡 服务地址: {get_api_base_url()}")
    print(f"🧪 测试页面: {get_api_base_url()}/test.html")
    print(f"📖 API 文档: {get_api_base_url()}/docs")
    print(f"📊 ReDoc 文档: {get_api_base_url()}/redoc")
    print(f"💻 服务配置: {SERVER_CONFIG}")
    print("-" * 50)
    
      # 启动服务器
    uvicorn.run(
        "web_serves.app:app",
        host=SERVER_CONFIG["host"],
        port=SERVER_CONFIG["port"],
        reload=SERVER_CONFIG["debug"],
        access_log=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
