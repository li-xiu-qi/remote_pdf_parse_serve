#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试 utils.api_client.ApiClient 的功能。
"""
from pathlib import Path
import sys
import json
import os
from typing import List, Optional

# 将项目根目录添加到sys.path，以便导入 utils.api_client
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

try:
    from utils.api_client import ApiClient
except ImportError:
    print("错误：无法从 utils.api_client 导入 ApiClient。请确保 __init__.py 存在于 utils 目录中，并且 utils 在PYTHONPATH中。")
    sys.exit(1)

# API基础URL的确定逻辑
def get_api_base_url() -> str:
    """获取API基础URL，优先级：环境变量 > 项目配置 > 默认值"""
    # 优先从环境变量获取
    api_host = os.environ.get("API_HOST", "localhost")
    api_port = os.environ.get("API_PORT", "8000")
    api_base_url = f"http://{api_host}:{api_port}"
    
    # 尝试从项目配置中读取
    try:
        from web_serves.config import SERVER_CONFIG
        host_config = SERVER_CONFIG.get('host', 'localhost')
        port_config = SERVER_CONFIG.get('port', 8000)
        if host_config == "0.0.0.0":  # 在服务器配置中，0.0.0.0 意味着监听所有接口，客户端应连接到 localhost
            host_config = "localhost"
        api_base_url = f"http://{host_config}:{port_config}"
        print(f"✅ 使用来自 web_serves.config 的 API_BASE_URL: {api_base_url}")
    except (ImportError, KeyError) as e:
        print(f"⚠️ 未找到 web_serves.config 或其配置不完整，使用默认/环境变量 API_BASE_URL: {api_base_url}")
    
    return api_base_url

def find_test_files() -> tuple[List[Path], Optional[Path]]:
    """查找测试文件，返回图片文件列表和PDF文件路径"""
    assets_dir = project_root / "assets"
    test_images_dir = assets_dir / "images"
    test_pdfs_dir = assets_dir / "pdfs"
    
    # 查找测试图片
    image_extensions = ["*.png", "*.jpg", "*.jpeg", "*.gif", "*.bmp", "*.webp"]
    image_files = []
    for ext in image_extensions:
        image_files.extend(list(test_images_dir.glob(ext)))
    
    # 转换为绝对路径
    absolute_image_files = [img.resolve() for img in image_files]
    
    # 查找测试PDF
    test_pdf_file = (test_pdfs_dir / "simcse.pdf").resolve()
    pdf_file = test_pdf_file if test_pdf_file.is_file() else None
    
    return absolute_image_files, pdf_file

def test_single_image_upload(client: ApiClient, image_files: List[Path]) -> bool:
    """测试单个图片上传"""
    if not image_files:
        print("⚠️ 没有找到测试图片文件，跳过单个图片上传测试")
        return False
    
    print("\n-- 测试单个图片上传 --")
    test_image = image_files[0]
    print(f"📤 选定的测试图片: {test_image.name}")
    
    result = client.upload_single_image(test_image)
    if result:
        print("✅ 单个图片上传测试通过")
        print(f"   📄 响应摘要: {result.get('message', 'N/A')}")
        if 'file_info' in result:
            file_info = result['file_info']
            print(f"   🔗 文件URL: {file_info.get('url', 'N/A')}")
        return True
    else:
        print("❌ 单个图片上传测试失败")
        return False

def test_multiple_images_upload(client: ApiClient, image_files: List[Path]) -> bool:
    """测试多个图片上传（仅文件存储，无AI分析）"""
    if len(image_files) < 1:
        print("⚠️ 需要至少1张图片进行多图片上传测试")
        return False
    
    print("\n-- 测试多个图片上传（文件存储模式）--")
    # 最多上传3张图片进行测试
    test_images = image_files[:min(3, len(image_files))]
    print(f"📤 选定的测试图片: {[img.name for img in test_images]}")
    print("ℹ️ 注意: 当前版本的批量图片上传仅进行文件存储，不包含AI分析")
    
    result = client.upload_multiple_images(test_images)
    if result:
        uploaded_count = len(result.get('uploaded_files', []))
        failed_count = len(result.get('failed_files', []))
        print(f"✅ 多个图片上传测试通过: 成功 {uploaded_count} 张，失败 {failed_count} 张")
        
        # 显示上传成功的文件信息
        for uploaded_file in result.get('uploaded_files', [])[:2]:  # 只显示前2个
            print(f"   📄 {uploaded_file.get('original_filename', 'N/A')} -> {uploaded_file.get('url', 'N/A')}")
        
        # 显示失败文件信息（如果有）
        for failed_file in result.get('failed_files', []):
            print(f"   ❌ 失败: {failed_file.get('filename', 'N/A')} - {failed_file.get('error', 'N/A')}")
        
        return uploaded_count > 0
    else:
        print("❌ 多个图片上传测试失败")
        return False

def test_pdf_upload(client: ApiClient, pdf_file: Optional[Path]) -> bool:
    """测试PDF上传和处理（包含两种模式）"""
    if not pdf_file:
        print("⚠️ 没有找到测试PDF文件，跳过PDF上传测试")
        return False
    
    print("\n-- 测试PDF上传与处理 --")
    print(f"📄 选定的测试PDF: {pdf_file.name}")
    
    # 测试1: 不处理图片（仅PDF转Markdown）
    print("\n🔍 测试模式1: 仅PDF转Markdown（process_images=False）")
    result_no_ai = client.upload_pdf(pdf_file, process_images=False)
    
    success_count = 0
    
    if result_no_ai:
        print("✅ PDF转换测试通过（无AI分析）")
        print(f"   📄 响应摘要: {result_no_ai.get('message', 'N/A')}")
        if 'file_info' in result_no_ai:
            file_info = result_no_ai['file_info']
            print(f"   📄 PDF路径: {file_info.get('pdf_path', 'N/A')}")
            print(f"   📝 Markdown路径: {file_info.get('markdown_path', 'N/A')}")
            print(f"   🔄 处理模式: {file_info.get('process_images', 'N/A')}")
          # 显示处理统计
        if 'processing_info' in result_no_ai:
            proc_info = result_no_ai['processing_info']
            print(f"   📊 PDF转换: {'成功' if proc_info.get('pdf_converted') else '失败'}")
            # 对于不处理图片的模式，显示"跳过"而不是"失败"
            if result_no_ai.get('file_info', {}).get('process_images', False):
                print(f"   🖼️ 图片处理: {'成功' if proc_info.get('images_processed') else '失败'}")
            else:
                print(f"   🖼️ 图片处理: 跳过（process_images=False）")
        
        success_count += 1
    else:
        print("❌ PDF转换测试失败（无AI分析）")
    
    # 测试2: 处理图片（PDF转Markdown + AI图片分析）
    print("\n🔍 测试模式2: PDF转Markdown + AI图片分析（process_images=True）")
    result_with_ai = client.upload_pdf(
        pdf_file, 
        provider="zhipu",  # 使用智谱AI
        process_images=True,
        max_concurrent=3
    )
    
    if result_with_ai:
        print("✅ PDF处理测试通过（含AI分析）")
        print(f"   📄 响应摘要: {result_with_ai.get('message', 'N/A')}")
        if 'file_info' in result_with_ai:
            file_info = result_with_ai['file_info']
            print(f"   🤖 AI提供商: {file_info.get('provider', 'N/A')}")
            print(f"   🔄 处理模式: {file_info.get('process_images', 'N/A')}")
        
        # 显示处理统计
        if 'processing_info' in result_with_ai:
            proc_info = result_with_ai['processing_info']
            print(f"   📊 PDF转换: {'成功' if proc_info.get('pdf_converted') else '失败'}")
            print(f"   🖼️ 图片AI分析: {'成功' if proc_info.get('images_processed') else '失败'}")
        
        success_count += 1
    else:
        print("❌ PDF处理测试失败（含AI分析）")
    
    print(f"\n📊 PDF测试结果: {success_count}/2 种模式成功")
    return success_count > 0

def main():
    """主测试函数"""
    print("=" * 60)
    print("🧪 ApiClient 完整功能测试 (来自 utils.api_client)")
    print("=" * 60)
    
    # 获取API URL
    api_base_url = get_api_base_url()
    print(f"🌐 目标 API 服务器: {api_base_url}")
    
    # 创建客户端
    client = ApiClient(base_url=api_base_url)
    
    # 检查服务器健康状态
    print(f"\n🔍 检查服务器健康状态...")
    if not client.health_check():
        print(f"❌ 服务器不可访问: {api_base_url}")
        print("   请确保服务器正在运行，然后重试")
        print("   启动命令: python run_server.py")
        return False
    else:
        print(f"✅ 服务器正常运行")
    
    # 查找测试文件
    image_files, pdf_file = find_test_files()
    print(f"\n📁 测试资源统计:")
    print(f"   🖼️ 找到图片文件: {len(image_files)} 个")
    print(f"   📄 找到PDF文件: {'是' if pdf_file else '否'}")
    
    if image_files:
        print(f"   📋 图片列表: {[img.name for img in image_files[:3]]}{'...' if len(image_files) > 3 else ''}")
    if pdf_file:
        print(f"   📋 PDF文件: {pdf_file.name}")
    
    # 执行测试
    test_results = []
      # 测试图片上传
    if image_files:
        print("\n" + "=" * 40)
        print("🖼️ 图片上传测试")
        print("=" * 40)
        
        single_result = test_single_image_upload(client, image_files)
        multiple_result = test_multiple_images_upload(client, image_files)
        
        test_results.extend([single_result, multiple_result])
    else:
        print("\n⚠️ 未找到测试图片，跳过图片上传测试")
        print(f"   请在 {project_root / 'assets' / 'images'} 目录中添加测试图片")
        print("   支持格式: PNG, JPG, JPEG, GIF, BMP, WebP")
    
    # 测试PDF上传
    if pdf_file:
        print("\n" + "=" * 40)
        print("📄 PDF处理测试")
        print("=" * 40)
        
        pdf_result = test_pdf_upload(client, pdf_file)
        test_results.append(pdf_result)
    else:
        print("\n⚠️ 未找到测试PDF，跳过PDF处理测试")
        print(f"   请在 {project_root / 'assets' / 'pdfs'} 目录中添加 'simcse.pdf' 文件")
      # 测试结果汇总
    print("\n" + "=" * 60)
    print("📊 测试结果汇总")
    print("=" * 60)
    
    if not test_results:
        print("⚠️ 没有执行任何测试，请检查测试文件是否存在")
        print("   需要的测试文件:")
        print("   - 图片文件: assets/images/ 目录下的 PNG/JPG 等格式文件")
        print("   - PDF文件: assets/pdfs/simcse.pdf")
        return False
    
    passed_tests = sum(test_results)
    total_tests = len(test_results)
    
    print(f"✅ 通过测试: {passed_tests}/{total_tests}")
    print(f"❌ 失败测试: {total_tests - passed_tests}/{total_tests}")
    
    # 测试分类统计
    test_categories = []
    if image_files:
        test_categories.extend(["单图上传", "批量图片上传"])
    if pdf_file:
        test_categories.append("PDF处理")
    
    print(f"📋 测试覆盖范围: {', '.join(test_categories)}")
    
    if passed_tests == total_tests:
        print("🎉 所有测试通过！API客户端功能正常")
        return True
    else:
        print("⚠️ 部分测试失败，请检查上述错误信息")
        print("💡 常见解决方案:")
        print("   - 确保服务器正在运行")
        print("   - 检查测试文件是否存在")
        print("   - 验证API密钥配置（PDF AI分析功能）")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
