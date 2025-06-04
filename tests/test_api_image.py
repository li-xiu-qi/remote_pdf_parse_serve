#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片分析API接口测试
测试 /upload/image 和 /upload/images 接口的可用性
"""
import requests
import json
from pathlib import Path
import time

# 配置
API_BASE_URL = "http://localhost:8000"
TEST_IMAGES_DIR = "../assets/images"  # 使用现有的测试图片目录


def test_single_image_upload_api():
    """测试单个图片上传API"""
    print("\n1. 测试单个图片上传接口...")
    
    # 找到第一个测试图片
    images_dir = Path(TEST_IMAGES_DIR)
    if not images_dir.exists():
        print(f"❌ 测试图片目录不存在: {images_dir}")
        return False
    
    # 获取第一个图片文件
    image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg"))
    if not image_files:
        print(f"❌ 在 {images_dir} 中未找到图片文件")
        return False
    
    test_image = image_files[0]
    print(f"   📸 使用测试图片: {test_image}")
    print(f"   📸 文件大小: {test_image.stat().st_size / 1024:.2f} KB")
    
    try:
        with open(test_image, 'rb') as f:
            files = {'file': (test_image.name, f, 'image/png')}
            
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/upload/image",
                files=files,
                timeout=30
            )
            end_time = time.time()
            
            print(f"   ⏱️  上传时间: {end_time - start_time:.2f} 秒")
            print(f"   📊 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ 单个图片上传成功!")
                
                result = response.json()
                print("   📋 响应结果:")
                print(f"   消息: {result.get('message', 'N/A')}")
                
                if 'file_info' in result:
                    file_info = result['file_info']
                    print(f"   原始文件名: {file_info.get('original_filename', 'N/A')}")
                    print(f"   保存文件名: {file_info.get('saved_filename', 'N/A')}")
                    print(f"   文件大小: {file_info.get('file_size', 0)} bytes")
                    print(f"   内容类型: {file_info.get('content_type', 'N/A')}")
                
                return True
            else:
                print(f"❌ 单个图片上传失败: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   错误详情: {error_detail}")
                except:
                    print(f"   响应内容: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 单个图片上传请求失败: {e}")
        return False


def test_multiple_images_upload_api():
    """测试多个图片上传API"""
    print("\n2. 测试多个图片上传接口...")
    
    images_dir = Path(TEST_IMAGES_DIR)
    if not images_dir.exists():
        print(f"❌ 测试图片目录不存在: {images_dir}")
        return False
    
    # 获取所有图片文件（最多3个用于测试）
    image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg"))
    if not image_files:
        print(f"❌ 在 {images_dir} 中未找到图片文件")
        return False
    
    # 限制测试图片数量
    test_images = image_files[:3]
    print(f"   📸 准备上传 {len(test_images)} 个图片:")
    for img in test_images:
        print(f"      - {img.name} ({img.stat().st_size / 1024:.2f} KB)")
    
    try:
        files = []
        for img in test_images:
            files.append(('files', (img.name, open(img, 'rb'), 'image/png')))
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/upload/images",
            files=files,
            timeout=60
        )
        end_time = time.time()
        
        # 关闭文件
        for _, (_, file_obj, _) in files:
            file_obj.close()
        
        print(f"   ⏱️  上传时间: {end_time - start_time:.2f} 秒")
        print(f"   📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ 多个图片上传成功!")
            
            result = response.json()
            print("   📋 响应结果:")
            print(f"   消息: {result.get('message', 'N/A')}")
            
            uploaded_files = result.get('uploaded_files', [])
            failed_files = result.get('failed_files', [])
            
            print(f"   成功上传: {len(uploaded_files)} 个文件")
            print(f"   失败文件: {len(failed_files)} 个文件")
            
            if uploaded_files:
                print("   成功的文件:")
                for file_info in uploaded_files[:3]:  # 只显示前3个
                    print(f"      - {file_info.get('original_filename', 'N/A')}")
            
            if failed_files:
                print("   失败的文件:")
                for error_info in failed_files:
                    print(f"      - {error_info.get('filename', 'N/A')}: {error_info.get('error', 'N/A')}")
            
            return True
        else:
            print(f"❌ 多个图片上传失败: {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   错误详情: {error_detail}")
            except:
                print(f"   响应内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 多个图片上传请求失败: {e}")
        return False


def test_image_api_error_handling():
    """测试图片API错误处理"""
    print("\n3. 测试错误处理...")
    
    # 测试无文件上传
    print("   测试无文件上传...")
    try:
        response = requests.post(f"{API_BASE_URL}/upload/image", timeout=10)
        print(f"   无文件响应: {response.status_code}")
        if response.status_code == 422:  # FastAPI的验证错误
            print("   ✅ 正确处理无文件错误")
        else:
            print(f"   ⚠️  意外的响应码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 无文件测试失败: {e}")
    
    # 测试不支持的文件类型
    print("   测试不支持的文件类型...")
    try:
        # 创建一个假的txt文件
        fake_file = ('test.txt', b'this is a text file', 'text/plain')
        files = {'file': fake_file}
        
        response = requests.post(
            f"{API_BASE_URL}/upload/image",
            files=files,
            timeout=10
        )
        print(f"   不支持文件类型响应: {response.status_code}")
        if response.status_code == 400:
            print("   ✅ 正确处理不支持的文件类型")
            try:
                error_detail = response.json()
                print(f"   错误信息: {error_detail.get('detail', 'N/A')}")
            except:
                pass
        else:
            print(f"   ⚠️  意外的响应码: {response.status_code}")
    except Exception as e:
        print(f"   ❌ 文件类型测试失败: {e}")


def test_image_upload_api():
    """测试图片上传API的完整流程"""
    print("=" * 60)
    print("图片上传API接口测试")
    print("=" * 60)
    
    # 检查测试目录
    images_dir = Path(TEST_IMAGES_DIR)
    if not images_dir.exists():
        print(f"❌ 测试图片目录不存在: {images_dir}")
        print("请确保测试图片目录存在")
        return False
    
    print(f"📸 使用测试目录: {images_dir}")
    
    # 检查可用的图片文件
    image_files = list(images_dir.glob("*.png")) + list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg"))
    print(f"📸 找到 {len(image_files)} 个图片文件")
    
    if not image_files:
        print("❌ 未找到测试图片文件")
        return False
    
    # 测试服务器连接
    print("\n0. 测试服务器连接...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
        else:
            print(f"⚠️  服务器响应异常: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接服务器: {e}")
        print("请确保服务器正在运行 (python run_server.py)")
        return False
    
    # 执行各项测试
    success1 = test_single_image_upload_api()
    success2 = test_multiple_images_upload_api()
    test_image_api_error_handling()
    
    return success1 and success2


if __name__ == "__main__":
    print("🚀 开始图片上传API接口测试...")
    print(f"🌐 测试地址: {API_BASE_URL}")
    
    # 执行测试
    success = test_image_upload_api()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 图片上传API测试完成!")
        print("✅ 接口工作正常，可以正常处理图片上传")
    else:
        print("❌ 图片上传API测试失败!")
        print("请检查服务器状态和测试文件")
    print("=" * 60)
