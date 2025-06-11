#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 utils.api_client.ApiClient 的功能。
"""
from pathlib import Path
import sys
import json
import os # 用于获取环境变量

# 将项目根目录添加到sys.path，以便导入 utils.api_client
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    from utils.api_client import ApiClient
except ImportError:
    print("错误：无法从 utils.api_client 导入 ApiClient。请确保 __init__.py 存在于 utils 目录中，并且 utils 在PYTHONPATH中。")
    sys.exit(1)

# API基础URL的确定逻辑
# 优先从环境变量获取，然后尝试从项目配置（如果可用），最后使用默认值
API_HOST = os.environ.get("API_HOST", "localhost")
API_PORT = os.environ.get("API_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}"

# 尝试从项目配置中读取（如果测试环境需要）
# 注意：这会重新引入对项目内部结构的依赖，如果希望测试脚本更通用，则应避免
try:
    from web_serves.config import SERVER_CONFIG
    host_config = SERVER_CONFIG.get('host', 'localhost')
    port_config = SERVER_CONFIG.get('port', 8000)
    if host_config == "0.0.0.0": # 在服务器配置中，0.0.0.0 意味着监听所有接口，客户端应连接到 localhost
        host_config = "localhost"
    API_BASE_URL = f"http://{host_config}:{port_config}"
    print(f"使用来自 web_serves.config 的 API_BASE_URL: {API_BASE_URL}")
except (ImportError, KeyError):
    print(f"未找到 web_serves.config 或其配置不完整，将使用默认或环境变量定义的 API_BASE_URL: {API_BASE_URL}")


# 测试资源文件目录 (相对于项目根目录)
ASSETS_DIR = project_root / "assets"
TEST_IMAGES_DIR = ASSETS_DIR / "images"
TEST_PDFS_DIR = ASSETS_DIR / "pdfs"


if __name__ == "__main__":
    print(f"--- 开始测试 ApiClient (来自 utils.api_client) ---")
    print(f"目标 API 服务器: {API_BASE_URL}")
    print(f"测试资源图片目录: {TEST_IMAGES_DIR}")
    print(f"测试资源PDF目录: {TEST_PDFS_DIR}")

    client = ApiClient(base_url=API_BASE_URL)

    # --- 测试图片上传 ---
    print("\n--- 测试图片上传 ---")
    
    # 查找测试图片 (确保使用绝对路径)
    image_files_glob = list(TEST_IMAGES_DIR.glob("*.png")) + \
                       list(TEST_IMAGES_DIR.glob("*.jpg")) + \
                       list(TEST_IMAGES_DIR.glob("*.jpeg"))

    # 转换为绝对路径列表
    absolute_image_files = [img.resolve() for img in image_files_glob]

    if not absolute_image_files:
        print(f"⚠️ 未在 {TEST_IMAGES_DIR} 中找到测试图片，跳过图片上传测试。")
    else:
        # 1. 测试单个图片上传
        print("\n-- 测试单个图片上传 --")
        test_image_single = absolute_image_files[0]
        print(f"选定的单个测试图片: {test_image_single}")
        single_image_result = client.upload_single_image(test_image_single)
        if single_image_result:
            print(f"单个图片上传结果: {json.dumps(single_image_result, indent=2, ensure_ascii=False)}")
        else:
            print(f"单个图片上传 ({test_image_single.name}) 失败或无结果返回。")

        # 2. 测试多个图片上传
        print("\n-- 测试多个图片上传 --")
        # 最多上传3张，或所有找到的图片（如果少于3张）
        test_images_multiple = absolute_image_files[:min(3, len(absolute_image_files))]
        
        if len(test_images_multiple) < 1:
            print("⚠️ 测试多图片上传需要至少1张图片。")
        else:
            print(f"选定的多个测试图片: {[img.name for img in test_images_multiple]}")
            multiple_images_result = client.upload_multiple_images(test_images_multiple)
            if multiple_images_result:
                print(f"多个图片上传结果: {json.dumps(multiple_images_result, indent=2, ensure_ascii=False)}")
            else:
                print(f"多个图片上传失败或无结果返回。")
    print("--- 图片上传测试结束 ---")

    # --- 测试PDF上传 ---
    print("\n--- 测试PDF上传 ---")
    test_pdf_file = (TEST_PDFS_DIR / "simcse.pdf").resolve() 

    if not test_pdf_file.is_file():
        print(f"⚠️ 未在 {TEST_PDFS_DIR} 中找到测试PDF 'simcse.pdf' ({test_pdf_file})，跳过PDF上传测试。")
    else:
        print(f"选定的测试PDF: {test_pdf_file}")
        # 1. 测试PDF上传（不处理图片）
        print("\n-- 测试PDF上传 (不处理图片) --")
        pdf_result_no_images = client.upload_pdf(test_pdf_file, process_images=False)
        if pdf_result_no_images:
            print(f"PDF上传 (不处理图片) 结果: {json.dumps(pdf_result_no_images, indent=2, ensure_ascii=False)}")
        else:
            print(f"PDF上传 (不处理图片) ({test_pdf_file.name}) 失败或无结果返回。")

        # 2. 测试PDF上传（处理图片）
        # 注意：处理图片可能需要更长的时间，并且依赖于AI提供商的配置
        # print("\n-- 测试PDF上传 (处理图片) --")
        # pdf_result_with_images = client.upload_pdf(test_pdf_file, process_images=True)
        # if pdf_result_with_images:
        #     print(f"PDF上传 (处理图片) 结果: {json.dumps(pdf_result_with_images, indent=2, ensure_ascii=False)}")
        # else:
        #     print(f"PDF上传 (处理图片) ({test_pdf_file.name}) 失败或无结果返回。")

    print("--- PDF上传测试结束 ---")

    print("\n所有测试执行完毕。请检查上面的输出以确认结果。")
