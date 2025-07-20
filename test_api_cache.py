#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试更新后的API客户端缓存功能
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append('/home/xiaoke/projects/remote_pdf_parse_serve')

from utils.remote_pdf_api_client import ApiClient


def test_cache_functionality():
    """测试缓存功能"""
    
    client = ApiClient()
    
    # 检查服务器健康状态
    print("🔍 检查服务器状态...")
    if not client.health_check():
        print("❌ 服务器未启动或无法访问")
        return
    
    print("✅ 服务器状态正常")
    
    # 获取初始缓存状态
    print("\n📊 获取初始缓存状态...")
    initial_stats = client.get_cache_stats()
    if initial_stats:
        cache_info = initial_stats.get('cache_stats', {})
        print(f"缓存项目数量: {cache_info.get('cache_size', 0)}")
        print(f"缓存目录: {cache_info.get('cache_directory', '')}")
        print(f"磁盘使用量: {cache_info.get('disk_usage', 0) / 1024 / 1024:.2f} MB")
    else:
        print("❌ 获取缓存状态失败")
    
    # 测试PDF文件路径
    pdf_path = Path("/home/xiaoke/projects/remote_pdf_parse_serve/assets/pdfs/simcse.pdf")
    
    if not pdf_path.exists():
        print(f"❌ 测试PDF文件不存在: {pdf_path}")
        return
    
    print(f"\n📄 使用测试文件: {pdf_path}")
    
    # 第一次处理（应该没有缓存）
    print("\n🔄 第一次处理PDF（建立缓存）...")
    start_time = time.time()
    result1 = client.upload_pdf(
        pdf_path=pdf_path,
        provider="zhipu",
        backend="pipeline",
        method="auto",
        parse_images=False,  # 关闭图片处理以加快测试
        use_cache=True
    )
    first_time = time.time() - start_time
    
    if result1:
        print(f"✅ 第一次处理成功，耗时: {first_time:.2f}秒")
        markdown_content = result1.get('markdown', {}).get('content', '')
        print(f"Markdown内容长度: {len(markdown_content)} 字符")
    else:
        print("❌ 第一次处理失败")
        return
    
    # 获取缓存状态
    print("\n📊 第一次处理后的缓存状态...")
    stats_after_first = client.get_cache_stats()
    if stats_after_first:
        cache_info = stats_after_first.get('cache_stats', {})
        print(f"缓存项目数量: {cache_info.get('cache_size', 0)}")
        print(f"磁盘使用量: {cache_info.get('disk_usage', 0) / 1024 / 1024:.2f} MB")
    
    # 第二次处理（应该使用缓存）
    print("\n🚀 第二次处理PDF（使用缓存）...")
    start_time = time.time()
    result2 = client.upload_pdf(
        pdf_path=pdf_path,
        provider="zhipu",
        backend="pipeline",
        method="auto",
        parse_images=False,
        use_cache=True
    )
    second_time = time.time() - start_time
    
    if result2:
        print(f"✅ 第二次处理成功，耗时: {second_time:.2f}秒")
        markdown_content2 = result2.get('markdown', {}).get('content', '')
        print(f"Markdown内容长度: {len(markdown_content2)} 字符")
        
        # 比较结果
        if markdown_content == markdown_content2:
            print("✅ 两次处理结果一致")
        else:
            print("⚠️ 两次处理结果不一致")
        
        # 比较时间
        if second_time < first_time * 0.8:
            speedup = ((first_time - second_time) / first_time) * 100
            print(f"🚀 缓存生效！第二次处理速度提升了 {speedup:.1f}%")
        else:
            print("⚠️ 缓存可能没有生效，时间差异不明显")
    else:
        print("❌ 第二次处理失败")
    
    # 测试禁用缓存
    print("\n🔄 测试禁用缓存...")
    start_time = time.time()
    result3 = client.upload_pdf(
        pdf_path=pdf_path,
        provider="zhipu",
        backend="pipeline",
        method="auto",
        parse_images=False,
        use_cache=False  # 禁用缓存
    )
    third_time = time.time() - start_time
    
    if result3:
        print(f"✅ 禁用缓存处理成功，耗时: {third_time:.2f}秒")
        print(f"与第一次处理时间对比: {abs(third_time - first_time):.2f}秒差异")
    else:
        print("❌ 禁用缓存处理失败")
    
    # 获取最终缓存状态
    print("\n📊 最终缓存状态...")
    final_stats = client.get_cache_stats()
    if final_stats:
        cache_info = final_stats.get('cache_stats', {})
        print(f"缓存项目数量: {cache_info.get('cache_size', 0)}")
        print(f"磁盘使用量: {cache_info.get('disk_usage', 0) / 1024 / 1024:.2f} MB")
    
    # 测试缓存清理
    print("\n🧹 测试缓存清理...")
    success = client.clear_cache()
    if success:
        print("✅ 缓存清理成功")
        
        # 验证缓存已清理
        cleared_stats = client.get_cache_stats()
        if cleared_stats:
            cache_info = cleared_stats.get('cache_stats', {})
            print(f"清理后缓存项目数量: {cache_info.get('cache_size', 0)}")
    else:
        print("❌ 缓存清理失败")


if __name__ == "__main__":
    test_cache_functionality()
