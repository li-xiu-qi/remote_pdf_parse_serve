#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF解析API接口测试
测试 /upload/pdf 接口的可用性
"""
import requests
import json
from pathlib import Path
import time
import sys
import os

# 添加项目路径到系统路径，以便导入配置模块
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

try:
    from web_serves.config import get_api_base_url
    API_BASE_URL = get_api_base_url()
except ImportError:
    # 如果无法导入配置，使用默认值
    API_BASE_URL = "http://localhost:8000"

TEST_PDF_PATH = "../assets/pdfs/simcse.pdf"  # 使用现有的测试PDF


def test_pdf_upload_api():
    """测试PDF上传和解析API"""
    print("=" * 60)
    print("PDF解析API接口测试")
    print("=" * 60)
    
    # 检查测试文件是否存在
    pdf_path = Path(TEST_PDF_PATH)
    if not pdf_path.exists():
        print(f"❌ 测试PDF文件不存在: {pdf_path}")
        print("请确保测试文件存在或修改 TEST_PDF_PATH 变量")
        return False
    
    print(f"📄 使用测试文件: {pdf_path}")
    print(f"📄 文件大小: {pdf_path.stat().st_size / 1024:.2f} KB")
    
    # 1. 测试服务器健康检查
    print("\n1. 测试服务器连接...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器连接正常")
            print(f"   响应: {response.json()}")
        else:
            print(f"⚠️  服务器响应异常: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"❌ 无法连接服务器: {e}")
        print("请确保服务器正在运行 (python run_server.py)")
        return False
    
    # 2. 测试PDF上传接口
    print("\n2. 测试PDF上传接口...")
    
    try:
        # 准备文件
        with open(pdf_path, 'rb') as f:
            files = {'file': (pdf_path.name, f, 'application/pdf')}
              # 准备参数 - 不指定remote_base_url，让接口使用配置文件中的默认值
            data = {
                'provider': 'zhipu',  # 使用智谱AI
                'include_descriptions': True
                # 移除remote_base_url参数，让接口使用config.py中的配置
            }
            print(f"   📤 上传文件: {pdf_path.name}")
            print(f"   🤖 AI提供商: {data['provider']}")
            print(f"   📝 包含描述: {data['include_descriptions']}")
            print(f"   🌐 API地址: {API_BASE_URL}")
            print("   🔗 remote_base_url: 使用配置文件默认值")
              # 发送请求
            start_time = time.time()
            response = requests.post(
                f"{API_BASE_URL}/upload/pdf",
                files=files,
                data=data,
                timeout=2400  # 40分钟超时
            )
            end_time = time.time()
            
            print(f"   ⏱️  处理时间: {end_time - start_time:.2f} 秒")
            print(f"   📊 响应状态: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ PDF上传和解析成功!")
                
                # 解析响应
                result = response.json()
                print("\n📋 响应结果概览:")
                print(f"   消息: {result.get('message', 'N/A')}")
                
                if 'file_info' in result:
                    file_info = result['file_info']
                    print(f"   原始文件名: {file_info.get('original_filename', 'N/A')}")
                    print(f"   处理文件大小: {file_info.get('file_size', 0)} bytes")
                    print(f"   创建时间: {file_info.get('creation_time', 'N/A')}")
                
                if 'markdown_content' in result:
                    markdown_content = result['markdown_content']
                    print(f"   Markdown长度: {len(markdown_content)} 字符")
                    print(f"   前100字符预览: {markdown_content[:100]}...")
                    
                    # 保存结果到文件
                    output_file = Path("test_api_pdf_result.md")
                    with open(output_file, 'w', encoding='utf-8') as f:
                        f.write(markdown_content)
                    print(f"   💾 完整结果已保存到: {output_file}")
                
                return True
                
            else:
                print(f"❌ PDF处理失败: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   错误详情: {error_detail}")
                except:
                    print(f"   响应内容: {response.text}")
                return False
    except requests.exceptions.Timeout:
        print("❌ 请求超时 (超过40分钟)")
        print("   PDF处理可能需要较长时间，这是正常的")
        return False
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")
        return False
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return False


def test_api_endpoints():
    """测试相关API端点"""
    print("\n3. 测试其他相关端点...")
    
    endpoints = [
        ("/", "根路径"),
        ("/config", "配置信息"),
    ]
    
    for endpoint, description in endpoints:
        try:
            response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
            if response.status_code == 200:
                print(f"✅ {description} ({endpoint}): 正常")
            else:
                print(f"⚠️  {description} ({endpoint}): {response.status_code}")
        except Exception as e:
            print(f"❌ {description} ({endpoint}): {e}")


if __name__ == "__main__":
    print("🚀 开始PDF解析API接口测试...")
    print(f"🌐 测试地址: {API_BASE_URL}")
    print("📋 使用配置文件中的API地址和端口设置")
    
    # 执行测试
    success = test_pdf_upload_api()
    test_api_endpoints()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 PDF解析API测试完成!")
        print("✅ 接口工作正常，可以正常处理PDF文件")
    else:
        print("❌ PDF解析API测试失败!")
        print("请检查服务器状态和配置")
    print("=" * 60)
