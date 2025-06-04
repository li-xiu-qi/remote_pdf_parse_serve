#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF处理相关路由
"""
import os
import uuid
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from web_serves.pdf_utils.mineru_parse import mineru_pdf2md
from web_serves.markdown_utils.markdown_image_processor import MarkdownImageProcessor
from web_serves.config import get_storage_paths, get_unique_filename, get_api_base_url


router = APIRouter(prefix="/upload", tags=["PDF处理"])


@router.post("/pdf")
async def upload_and_process_pdf(
    file: UploadFile = File(...),
    provider: str = "zhipu",
    include_descriptions: bool = True,
):
    """
    上传PDF文件，转换为Markdown，并处理图片为远程地址
    
    Args:
        file: 要上传的PDF文件
        provider: AI视觉模型提供商 (guiji, zhipu, volces, openai)
        include_descriptions: 是否在Markdown中包含图片描述
        remote_base_url: 远程图片服务器基础URL，如果为None则使用配置文件中的API地址
        
    Returns:
        包含处理后的Markdown内容的JSON响应
    """

    remote_base_url = f"{get_api_base_url()}/uploads/images/"
    
    # 检查文件是否存在
    if not file.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")
    
    # 检查文件类型
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="只支持PDF文件")
    
    # 获取存储路径配置
    storage_paths = get_storage_paths()
    
    try:
        # 生成唯一的文件名和处理ID
        processing_id = uuid.uuid4().hex
        pdf_filename = get_unique_filename(file.filename, storage_paths["pdf_dir"])
        pdf_path = storage_paths["pdf_dir"] / pdf_filename
        
        # 创建临时工作目录
        temp_work_dir = storage_paths["temp_dir"] / processing_id
        temp_work_dir.mkdir(parents=True, exist_ok=True)
        
        # 保存上传的PDF文件到持久化存储
        print(f"保存PDF文件到: {pdf_path}")
        with open(pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 复制PDF到临时工作目录用于处理
        temp_pdf_path = temp_work_dir / pdf_filename
        shutil.copy2(pdf_path, temp_pdf_path)
        
        # 使用mineru转换PDF为Markdown
        print(f"开始转换PDF: {temp_pdf_path}")
        markdown_content = mineru_pdf2md(
            pdf_file_path=str(temp_pdf_path),
            md_output_path=str(temp_work_dir),
            return_path=False  # 直接返回内容而不是路径
        )        # 处理Markdown中的图片
        print("开始处理Markdown中的图片...")
        try:
            async with MarkdownImageProcessor(
                provider=provider,
                api_base_url=get_api_base_url(),  # 传递API基础URL
                max_concurrent=3
            ) as processor:
                processed_markdown = await processor.process_markdown_content(
                    markdown_content,
                    str(temp_work_dir),
                    include_descriptions=include_descriptions
                )
            print("图片处理完成")
        except Exception as img_error:
            print(f"图片处理警告: {img_error}")
            # 如果图片处理失败，仍然返回原始Markdown
            processed_markdown = markdown_content
          
        # 保存处理后的Markdown文件到持久化存储
        markdown_path = None
        if storage_paths["keep_markdown_files"]:
            markdown_filename = f"{Path(pdf_filename).stem}_{processing_id}.md"
            markdown_path = storage_paths["markdown_dir"] / markdown_filename
            
            with open(markdown_path, "w", encoding="utf-8") as md_file:
                md_file.write(processed_markdown)
            print(f"Markdown文件保存到: {markdown_path}")
        
        # 获取文件信息
        file_size = pdf_path.stat().st_size
        creation_time = datetime.now().isoformat()
        
        # 清理临时工作目录
        try:
            shutil.rmtree(temp_work_dir)
            print(f"清理临时目录: {temp_work_dir}")
        except Exception as cleanup_error:
            print(f"清理临时目录失败: {cleanup_error}")
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "PDF处理成功",
                "processing_id": processing_id,
                "file_info": {
                    "original_filename": file.filename,
                    "stored_filename": pdf_filename,
                    "file_size": file_size,
                    "content_type": file.content_type,
                    "pdf_path": str(pdf_path.relative_to(storage_paths["pdf_dir"].parent)),
                    "markdown_path": str(markdown_path.relative_to(storage_paths["markdown_dir"].parent)) if storage_paths["keep_markdown_files"] else None,
                    "creation_time": creation_time,
                    "provider": provider,
                    "include_descriptions": include_descriptions
                },
                "markdown_content": processed_markdown,
                "processing_info": {
                    "pdf_converted": True,
                    "images_processed": "images" in processed_markdown.lower(),
                    "remote_base_url": remote_base_url,
                    "temp_directory_cleaned": True
                }
            }
        )
        
    except Exception as e:
        # 清理可能创建的文件
        try:
            if 'pdf_path' in locals() and pdf_path.exists():
                pdf_path.unlink()
            if 'temp_work_dir' in locals() and temp_work_dir.exists():
                shutil.rmtree(temp_work_dir)
        except:
            pass
        
        print(f"PDF处理错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"PDF处理失败: {str(e)}")
