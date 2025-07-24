#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF解析API接口测试 - 布尔参数修复版
测试 /upload/pdf 接口的可用性，正确处理布尔参数
"""
import requests
import json
from pathlib import Path
import time
import sys

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

TEST_PDF_PATH = project_root / "assets" / "pdfs" / "simcse.pdf"


def test_pdf_upload_with_params(process_images_value, test_name):
    """通用测试函数"""
    print("=" * 60)
    print(f"PDF解析API接口测试 - {test_name}")
    print("=" * 60)
    
    pdf_path = Path(TEST_PDF_PATH)
    if not pdf_path.exists():
        print(f"❌ 测试PDF文件不存在: {pdf_path}")
        return False
    
    print(f"📄 使用测试文件: {pdf_path}")
    print(f"📄 文件大小: {pdf_path.stat().st_size / 1024:.2f} KB")
    
    try:
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
              # 使用URL参数而不是form data，确保布尔值正确传递
            params = {
                'provider': 'zhipu',
                'process_images': 'true' if process_images_value else 'false'
            }
            
            print(f"   📤 上传文件: {pdf_path.name}")
            print(f"   🤖 AI提供商: {params['provider']}")
            print(f"   🖼️  处理图片: {params['process_images']}")
            print(f"   🌐 API地址: {API_BASE_URL}/upload/pdf")
            
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/upload/pdf",
                files=files,
                params=params,  # 使用params而不是data
                timeout=2400
            )
            end_time = time.time()
            
            print(f"   ⏱️  处理时间: {end_time - start_time:.2f} 秒")
            print(f"   📊 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ PDF上传和解析成功({test_name})!")
                result = response.json()
                
                # 保存结果到文件
                suffix = "with_images" if process_images_value else "without_images"
                output_file = Path(f"test_api_pdf_{suffix}.md")
                if 'markdown_content' in result:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(result['markdown_content'])
                    print(f"   💾 结果已保存到: {output_file}")
                
                # 检查处理状态
                if 'file_info' in result:
                    file_info = result['file_info']
                    print(f"   🖼️  图片处理状态: {file_info.get('process_images', 'N/A')}")
                
                if 'processing_info' in result:
                    proc_info = result['processing_info']
                    print(f"   📊 图片已处理: {proc_info.get('images_processed', 'N/A')}")
                
                return True
            else:
                print(f"❌ PDF处理失败: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   错误详情: {error_detail}")
                except:
                    print(f"   响应内容: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False


def test_pdf_upload_api():
    """执行完整的PDF测试，增加健康检查"""
    print("🚀 开始PDF解析API接口测试...")
    print(f"🌐 测试地址: {API_BASE_URL}")

    # 健康检查
    try:
        health_url = f"{API_BASE_URL}/health"
        print(f"🔎 正在检查API健康状态: {health_url}")
        resp = requests.get(health_url, timeout=5)
        if resp.status_code == 200:
            print("✅ API健康检查通过！")
        else:
            print(f"❌ API健康检查失败，状态码: {resp.status_code}")
            print(f"   响应内容: {resp.text}")
            print("⏹️  跳过后续测试。")
            return False
    except Exception as e:
        print(f"❌ API健康检查请求失败: {e}")
        print("⏹️  跳过后续测试。")
        return False

    # 测试开启图片处理
    success1 = test_pdf_upload_with_params(True, "开启图片处理")
    # 测试不开启图片处理
    success2 = test_pdf_upload_with_params(False, "不开启图片处理")

    print("\n" + "=" * 60)
    print("PDF解析API接口测试结果:")
    print(f"开启图片处理: {'成功' if success1 else '失败'}")
    print(f"不开启图片处理: {'成功' if success2 else '失败'}")
    print("🚀 PDF解析API接口测试完成!")
    return success1 and success2


if __name__ == "__main__":
    result = test_pdf_upload_api()
    if result:
        print("OK")
    else:
        print("FAIL")
