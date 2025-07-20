#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试PDF解析缓存功能
"""

import os
import time
import sys
sys.path.append('/home/xiaoke/projects/remote_pdf_parse_serve')

from web_serves.pdf_utils.mineru_parse import (
    mineru_pdf2md, 
    clear_pdf_cache, 
    get_cache_stats
)

def test_cache_functionality():
    """测试缓存功能"""
    
    # 清理之前的缓存
    print("清理之前的缓存...")
    clear_pdf_cache()
    
    # 检查缓存统计
    stats = get_cache_stats()
    print(f"缓存初始状态: {stats}")
    
    # 测试PDF文件路径
    pdf_path = "/home/xiaoke/projects/remote_pdf_parse_serve/assets/pdfs/simcse.pdf"
    output_path = "/home/xiaoke/projects/remote_pdf_parse_serve/output/cache_test"
    
    if not os.path.exists(pdf_path):
        print(f"测试PDF文件不存在: {pdf_path}")
        return
    
    # 确保输出目录存在
    os.makedirs(output_path, exist_ok=True)
    
    print("开始第一次解析（应该没有缓存）...")
    start_time = time.time()
    try:
        result1 = mineru_pdf2md(
            pdf_file_path=pdf_path,
            md_output_path=output_path,
            backend="pipeline",
            method="auto",
            use_cache=True
        )
        first_parse_time = time.time() - start_time
        print(f"第一次解析完成，耗时: {first_parse_time:.2f}秒")
        print(f"结果长度: {len(result1)} 字符")
        
        # 检查缓存统计
        stats = get_cache_stats()
        print(f"第一次解析后的缓存状态: {stats}")
        
        print("\n开始第二次解析（应该使用缓存）...")
        start_time = time.time()
        result2 = mineru_pdf2md(
            pdf_file_path=pdf_path,
            md_output_path=output_path,
            backend="pipeline", 
            method="auto",
            use_cache=True
        )
        second_parse_time = time.time() - start_time
        print(f"第二次解析完成，耗时: {second_parse_time:.2f}秒")
        print(f"结果长度: {len(result2)} 字符")
        
        # 比较结果
        if result1 == result2:
            print("✓ 两次解析结果一致")
        else:
            print("✗ 两次解析结果不一致")
        
        # 比较时间
        if second_parse_time < first_parse_time * 0.5:
            print(f"✓ 缓存有效，第二次解析时间减少了 {((first_parse_time - second_parse_time) / first_parse_time * 100):.1f}%")
        else:
            print("? 缓存可能没有生效，时间差异不明显")
            
        print("\n测试不使用缓存的情况...")
        start_time = time.time()
        result3 = mineru_pdf2md(
            pdf_file_path=pdf_path,
            md_output_path=output_path,
            backend="pipeline",
            method="auto", 
            use_cache=False
        )
        third_parse_time = time.time() - start_time
        print(f"不使用缓存的解析完成，耗时: {third_parse_time:.2f}秒")
        
        # 最终缓存统计
        stats = get_cache_stats()
        print(f"\n最终缓存状态: {stats}")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cache_functionality()
