#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Markdown图片处理器 - 结合图片分析和API上传

主要功能：
1. 从Markdown文件中提取本地图片路径
2. 使用多模态模型分析图片生成标题和描述
3. 通过API上传图片到远程服务器
4. 更新Markdown内容，替换为远程地址并添加描述

使用示例：
    processor = MarkdownImageProcessor()
    await processor.process_markdown_file("./assets/test.md", "./output/updated_test.md")
"""

import os
import re
import asyncio
import logging
import aiofiles
import aiohttp
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from web_serves.image_utils.async_image_analysis import AsyncImageAnalysis
from web_serves.markdown_utils.update_markdown_with_analysis import update_markdown_with_analysis
from web_serves.config import get_api_base_url


class MarkdownImageProcessor:
    """Markdown图片处理器类 - 使用API上传"""
    
    def __init__(
        self,
        provider: str = "zhipu",  # 默认使用智谱
        api_key: str = None,
        base_url: str = None,
        vision_model: str = None,
        api_base_url: str = None,  # 后端API地址
        max_concurrent: int = 3
    ):
        """
        初始化处理器
        
        Args:
            provider: API提供商，支持 'guiji', 'zhipu', 'volces', 'openai'
            api_key: API密钥
            base_url: API基础URL
            vision_model: 视觉模型名称
            api_base_url: 后端API地址（用于上传图片）
            max_concurrent: 最大并发数
        """
        self.api_base_url = api_base_url or get_api_base_url()
        
        self.image_analyzer = AsyncImageAnalysis(
            provider=provider,
            api_key=api_key,
            base_url=base_url,
            vision_model=vision_model,
            max_concurrent=max_concurrent
        )
        
        # 配置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def extract_local_images(self, markdown_content: str, markdown_file_dir: str) -> List[Tuple[str, str]]:
        """
        从Markdown内容中提取本地图片路径
        
        Args:
            markdown_content: Markdown内容
            markdown_file_dir: Markdown文件所在目录
            
        Returns:
            包含(相对路径, 绝对路径)的元组列表
        """
        # 匹配本地图片的正则表达式
        image_pattern = r'!\[.*?\]\(([^)]+)\)'
        matches = re.findall(image_pattern, markdown_content)
        
        local_images = []
        for match in matches:
            # 跳过已经是URL的图片
            if match.startswith(('http://', 'https://', 'data:')):
                continue
                
            rel_path = match.strip()
            # 构建绝对路径
            if os.path.isabs(rel_path):
                abs_path = rel_path
            else:
                abs_path = os.path.abspath(os.path.join(markdown_file_dir, rel_path))
            
            # 检查文件是否存在
            if os.path.exists(abs_path):
                local_images.append((rel_path, abs_path))
            else:
                self.logger.warning(f"图片文件不存在: {abs_path}")
        
        return local_images

    async def upload_image_via_api(self, local_path: str, analysis_result: Dict[str, Any]) -> Tuple[str, str]:
        """
        通过API上传图片到远程服务器
        
        Args:
            local_path: 本地图片路径
            analysis_result: 图片分析结果
            
        Returns:
            (远程URL, 上传后的文件名)
        """
        upload_url = f"{self.api_base_url}/upload/image"
        
        try:
            async with aiohttp.ClientSession() as session:
                # 准备文件数据
                async with aiofiles.open(local_path, 'rb') as f:
                    file_data = await f.read()
                
                # 获取文件信息
                filename = os.path.basename(local_path)
                
                # 使用分析结果中的标题作为文件名前缀（如果有的话）
                title = analysis_result.get('title', '').strip()
                if title:
                    # 清理标题，移除不适合文件名的字符
                    clean_title = re.sub(r'[^\w\u4e00-\u9fff-]', '_', title)[:50]
                    name, ext = os.path.splitext(filename)
                    filename = f"{clean_title}_{name}{ext}"
                
                # 准备表单数据
                data = aiohttp.FormData()
                data.add_field('file', file_data, filename=filename, content_type='image/*')
                
                # 发送上传请求
                async with session.post(upload_url, data=data) as response:
                    if response.status == 200:
                        result = await response.json()
                        file_info = result.get('file_info', {})
                        saved_filename = file_info.get('saved_filename', filename)
                          # 构造远程URL - 图片保存在 uploads/images/ 目录下
                        remote_url = f"{self.api_base_url}/uploads/images/{saved_filename}"
                        
                        self.logger.info(f"图片上传成功: {local_path} -> {remote_url}")
                        return remote_url, saved_filename
                    else:
                        error_text = await response.text()
                        raise Exception(f"上传失败: HTTP {response.status}, {error_text}")
                        
        except Exception as e:
            self.logger.error(f"上传图片失败: {local_path}, 错误: {e}")
            raise

    async def process_images(self, local_images: List[Tuple[str, str]]) -> Dict[str, Dict[str, Any]]:
        """
        批量处理图片：分析 + 上传
        
        Args:
            local_images: (相对路径, 绝对路径)的元组列表
            
        Returns:
            图片处理结果字典，键为相对路径，值为包含分析结果和远程URL的字典
        """
        if not local_images:
            self.logger.info("没有发现本地图片需要处理")
            return {}
        
        self.logger.info(f"开始处理 {len(local_images)} 张图片...")
        
        # 准备分析任务
        image_sources = [
            {"local_image_path": abs_path} 
            for _, abs_path in local_images
        ]
        
        # 批量分析图片
        analysis_results = await self.image_analyzer.analyze_multiple_images(image_sources)
        
        # 组合结果并上传图片
        processed_results = {}
        for i, (rel_path, abs_path) in enumerate(local_images):
            analysis_result = analysis_results[i]
            
            try:
                remote_url, saved_filename = await self.upload_image_via_api(abs_path, analysis_result)
                
                processed_results[rel_path] = {
                    "title": analysis_result.get("title", ""),
                    "description": analysis_result.get("description", ""),
                    "url": remote_url,
                    "error": analysis_result.get("error"),
                    "original_path": abs_path,
                    "saved_filename": saved_filename
                }
                
                self.logger.info(f"处理完成: {rel_path} -> {remote_url}")
                
            except Exception as e:
                self.logger.error(f"处理图片失败: {rel_path}, 错误: {e}")
                processed_results[rel_path] = {
                    "title": analysis_result.get("title", ""),
                    "description": analysis_result.get("description", ""),
                    "url": "",
                    "error": f"上传失败: {str(e)}",
                    "original_path": abs_path,
                    "saved_filename": ""
                }
        
        return processed_results
    
    async def process_markdown_content(
        self, 
        markdown_content: str, 
        markdown_file_dir: str,
        include_descriptions: bool = True
    ) -> str:
        """
        处理Markdown内容，替换图片为远程地址
        
        Args:
            markdown_content: 原始Markdown内容
            markdown_file_dir: Markdown文件所在目录
            include_descriptions: 是否包含图片描述
            
        Returns:
            更新后的Markdown内容
        """
        # 提取本地图片
        local_images = self.extract_local_images(markdown_content, markdown_file_dir)
        
        if not local_images:
            self.logger.info("没有发现本地图片，返回原始内容")
            return markdown_content
        
        # 处理图片（分析 + 上传）
        image_results = await self.process_images(local_images)
        
        # 更新Markdown内容
        updated_content = update_markdown_with_analysis(
            markdown_content, 
            image_results, 
            include_descriptions
        )
        
        return updated_content
    
    async def process_markdown_file(
        self, 
        input_file_path: str, 
        output_file_path: str = None,
        include_descriptions: bool = True
    ) -> str:
        """
        处理Markdown文件
        
        Args:
            input_file_path: 输入Markdown文件路径
            output_file_path: 输出文件路径，如果为None则覆盖原文件
            include_descriptions: 是否包含图片描述
            
        Returns:
            处理后的Markdown内容
        """
        # 读取原始文件
        try:
            with open(input_file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"输入文件不存在: {input_file_path}")
        
        # 获取文件目录
        markdown_dir = os.path.dirname(os.path.abspath(input_file_path))
        
        # 处理内容
        updated_content = await self.process_markdown_content(
            original_content, 
            markdown_dir, 
            include_descriptions
        )
        
        # 写入输出文件
        if output_file_path is None:
            output_file_path = input_file_path
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_file_path)
        os.makedirs(output_dir, exist_ok=True)
        
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        
        self.logger.info(f"处理完成，输出文件: {output_file_path}")
        return updated_content
    
    async def close(self):
        """关闭处理器"""
        await self.image_analyzer.close()
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()


async def main():
    """示例使用"""
    processor = MarkdownImageProcessor()
    await processor.process_markdown_file(
        "./assets/test.md",
        "./assets/test_updated.md"
    )


if __name__ == "__main__":
    asyncio.run(main())
