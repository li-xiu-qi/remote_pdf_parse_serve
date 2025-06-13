#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片上传API接口测试
测试 /upload/image 和 /upload/images 接口的可用性
"""
import requests
from pathlib import Path
import sys
import time

project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    from web_serves.config import SERVER_CONFIG
    host = SERVER_CONFIG['host']
    port = SERVER_CONFIG['port']
    if host == "0.0.0.0":
        host = "localhost"
    API_BASE_URL = f"http://{host}:{port}"
except (ImportError, KeyError):
    API_BASE_URL = "http://localhost:8000"

TEST_IMAGES_DIR = project_root / "assets" / "images"


def test_single_image_upload_api():
    """测试单个图片上传API"""
    images_dir = Path(TEST_IMAGES_DIR)
    image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg"))
    if not image_files:
        print("⚠️ 未找到测试图片，跳过单图上传测试")
        return False
    test_image = image_files[0]
    content_type = 'image/png' if test_image.suffix.lower() == '.png' else \
                   'image/jpeg' if test_image.suffix.lower() in ['.jpg', '.jpeg'] else \
                   'application/octet-stream'
    try:
        with open(test_image, 'rb') as f:
            files = {'file': (test_image.name, f, content_type)}
            response = requests.post(f"{API_BASE_URL}/upload/image", files=files, timeout=30)
            print(f"[单图上传] 状态码: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ 单图上传成功: {test_image.name}")
                return True
            else:
                print(f"❌ 单图上传失败: {response.text}")
                return False
    except Exception as e:
        print(f"❌ 单图上传异常: {e}")
        return False


def test_multiple_images_upload_api():
    """测试多个图片上传API"""
    images_dir = Path(TEST_IMAGES_DIR)
    image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg"))
    if not image_files:
        print("⚠️ 未找到测试图片，跳过多图上传测试")
        return False
    test_images = image_files[:3]
    try:
        files_to_send = []
        opened_files = []
        for img_path in test_images:
            content_type = 'image/png' if img_path.suffix.lower() == '.png' else \
                           'image/jpeg' if img_path.suffix.lower() in ['.jpg', '.jpeg'] else \
                           'application/octet-stream'
            file_obj = open(img_path, 'rb')
            opened_files.append(file_obj)
            files_to_send.append(('files', (img_path.name, file_obj, content_type)))
        response = requests.post(f"{API_BASE_URL}/upload/images", files=files_to_send, timeout=60)
        for file_obj in opened_files:
            file_obj.close()
        print(f"[多图上传] 状态码: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            uploaded_files = result.get('uploaded_files', [])
            failed_files = result.get('failed_files', [])
            print(f"✅ 多图上传成功: 成功{len(uploaded_files)}，失败{len(failed_files)}")
            if failed_files:
                print(f"   失败文件: {[f.get('original_filename') for f in failed_files]}")
            return len(uploaded_files) == len(test_images) and not failed_files
        else:
            print(f"❌ 多图上传失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 多图上传异常: {e}")
        return False


def test_image_upload_api():
    """测试图片上传API的完整流程"""
    images_dir = Path(TEST_IMAGES_DIR)
    image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg"))
    if not image_files:
        print("⚠️ 未找到任何测试图片，跳过全部图片上传测试")
        return False
    success_single = test_single_image_upload_api()
    success_multiple = test_multiple_images_upload_api()
    return success_single and success_multiple


if __name__ == "__main__":
    result = test_image_upload_api()
    if result:
        print("OK")
    else:
        print("FAIL")
