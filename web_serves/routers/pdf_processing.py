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
from typing import Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Body, Query # Added Query
from fastapi.responses import JSONResponse

from web_serves.pdf_utils.mineru_parse import mineru_pdf2md
from web_serves.markdown_utils.markdown_image_processor import MarkdownImageProcessor
from web_serves.config import (
    get_storage_paths, 
    get_api_base_url, 
    DEFAULT_IMAGE_PROVIDER,
    DEFAULT_MAX_CONCURRENT_AI # Added DEFAULT_MAX_CONCURRENT_AI
)
from web_serves.utils.file_handler import FileHandler
from web_serves.exceptions import UnsupportedFileTypeError, FileSaveError

router = APIRouter(prefix="/upload", tags=["PDF处理"])


@router.post("/pdf")
async def upload_and_process_pdf(
    file: UploadFile = File(...),
    provider: str = DEFAULT_IMAGE_PROVIDER, 
    max_concurrent: int = DEFAULT_MAX_CONCURRENT_AI,
    process_images: bool = True  
):
    """
    上传PDF文件，转换为Markdown，并可选择性处理图片
    
    Args:
        file: 要上传的PDF文件
        provider: AI视觉模型提供商 (guiji, zhipu, volces, openai)
        max_concurrent: 最大并发处理数
        process_images: 是否对Markdown中的图片进行AI分析和处理
        
    Returns:
        包含处理后的Markdown内容的JSON响应
    """
    print("上传的文件名:", file.filename)  # Debugging line to check uploaded file name
    print("provider:", provider)  # Debugging line to check provider value
    
    print("process_images目前设置的参数是:", process_images)  # Debugging line to check process_images value
    remote_base_url = f"{get_api_base_url()}/uploads/images/"
    storage_paths = get_storage_paths()
    processing_id = uuid.uuid4().hex
    temp_work_dir = storage_paths["temp_dir"] / processing_id
    pdf_path: Optional[Path] = None # Initialize pdf_path

    try:
  
        uploaded_file_info = await FileHandler.save_uploaded_pdf_file(
            file=file,
            save_directory=storage_paths["pdf_dir"],
            # custom_filename=pdf_filename # 如果希望外部控制完整文件名，则取消注释此行并预先生成pdf_filename
        )
        pdf_filename = uploaded_file_info["saved_filename"]
        pdf_path = Path(uploaded_file_info["file_path"])
        print(f"PDF文件已保存: {pdf_path}")

        temp_work_dir.mkdir(parents=True, exist_ok=True)
        temp_pdf_path = temp_work_dir / pdf_filename # Use the filename returned by FileHandler
        shutil.copy2(pdf_path, temp_pdf_path)
        
        # 使用mineru转换PDF为Markdown
        print(f"开始转换PDF: {temp_pdf_path}")
        markdown_content = mineru_pdf2md(
            pdf_file_path=str(temp_pdf_path),
            md_output_path=str(temp_work_dir),
            return_path=False  # 直接返回内容而不是路径
        )
        
        # 根据process_images参数决定是否处理图片
        if process_images:
            # 处理Markdown中的图片
            print("开始处理Markdown中的图片...")
            try:
                async with MarkdownImageProcessor(
                    provider=provider,
                    api_base_url=get_api_base_url(),
                    max_concurrent=max_concurrent
                ) as processor:
                    processed_markdown = await processor.process_markdown_content(
                        markdown_content,
                        str(temp_work_dir),
                    )
                print("图片处理完成")
            except Exception as img_error:
                print(f"图片处理警告: {img_error}")
                # 如果图片处理失败，仍然返回原始Markdown
                processed_markdown = markdown_content
        else:
            # 不处理图片，直接使用原始Markdown
            print("跳过图片处理")
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
                    "process_images": process_images  # 添加到响应中
                },
                "markdown_content": processed_markdown,
                "processing_info": {
                    "pdf_converted": True,
                    "images_processed": process_images and "images" in processed_markdown.lower(),  # 更准确的判断
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
        except Exception as cleanup_inner_error: 
            print(f"清理文件或目录时发生内部错误: {cleanup_inner_error}")
        
        print(f"PDF处理错误: {str(e)}")
        if isinstance(e, UnsupportedFileTypeError):
            raise HTTPException(status_code=400, detail=e.message)
        elif isinstance(e, FileSaveError):
            raise HTTPException(status_code=500, detail=e.message)
        else:
            raise HTTPException(status_code=500, detail=f"PDF处理失败: {str(e)}")
