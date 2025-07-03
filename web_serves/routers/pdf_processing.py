#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PDF处理相关路由
"""
import os
import uuid
import tempfile
import shutil
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import APIRouter, File, UploadFile, HTTPException, Body, Query, Form
from fastapi.responses import JSONResponse

from web_serves.pdf_utils.mineru_parse import mineru_pdf2md, mineru_multi_pdf2md
from web_serves.markdown_utils.markdown_image_processor import MarkdownImageProcessor
from web_serves.config import (
    get_storage_paths, 
    get_api_base_url, 
    DEFAULT_IMAGE_PROVIDER,
    DEFAULT_MAX_CONCURRENT_AI
)
from web_serves.utils.file_handler import FileHandler
from web_serves.exceptions import UnsupportedFileTypeError, FileSaveError

router = APIRouter(prefix="/upload", tags=["PDF处理"])


async def process_markdown_with_images(
    markdown_content: str,
    temp_work_dir: str,
    provider: str,
    max_concurrent: int
) -> str:
    """处理Markdown中的图片并返回处理后的内容"""
    if not markdown_content:
        return markdown_content
        
    try:
        print("开始处理Markdown中的图片...")
        async with MarkdownImageProcessor(
            provider=provider,
            api_base_url=get_api_base_url(),
            max_concurrent=max_concurrent
        ) as processor:
            processed_markdown = await processor.process_markdown_content(
                markdown_content,
                temp_work_dir,
            )
        print("图片处理完成")
        return processed_markdown
    except Exception as img_error:
        print(f"图片处理警告: {img_error}")
        # 如果图片处理失败，仍然返回原始Markdown
        return markdown_content


async def save_markdown_file(content: str, file_path: Path) -> None:
    """异步保存Markdown文件"""
    async with aiofiles.open(file_path, "w", encoding="utf-8") as md_file:
        await md_file.write(content)
    print(f"Markdown文件保存到: {file_path}")


def cleanup_temp_directory(temp_dir: Path) -> bool:
    """清理临时目录并返回是否成功"""
    try:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
            print(f"清理临时目录: {temp_dir}")
        return True
    except Exception as cleanup_error:
        print(f"清理临时目录失败: {cleanup_error}")
        return False


@router.post("/pdf")
async def upload_and_process_pdf(
    file: UploadFile = File(...),
    provider: str = Form(default=DEFAULT_IMAGE_PROVIDER), 
    max_concurrent: int = Form(default=DEFAULT_MAX_CONCURRENT_AI),
    parse_images: bool = Form(default=True),
    backend: str = Form(default="pipeline"),
    method: str = Form(default="auto")
):
    """
    上传PDF文件，转换为Markdown，并可选择性处理图片
    
    Args:
        file: 要上传的PDF文件
        provider: AI视觉模型提供商 (guiji, zhipu, volces, openai)
        max_concurrent: 最大并发处理数
        parse_images: 是否对Markdown中的图片进行AI分析和处理
        backend: 解析PDF所用后端 (pipeline, vlm-transformers, vlm-sglang-engine)
        method: 解析PDF的方法 (auto, txt, ocr)
        
    Returns:
        包含处理后的Markdown内容的JSON响应
    """
    print("上传的文件名:", file.filename)  
    print("provider:", provider)
    print("backend:", backend)
    print("method:", method)
    print("parse_images目前设置的参数是:", parse_images)
    
    remote_base_url = f"{get_api_base_url()}/uploads/images/"
    storage_paths = get_storage_paths()
    processing_id = uuid.uuid4().hex
    temp_work_dir = storage_paths["temp_dir"] / processing_id
    pdf_path = None
    markdown_path = None

    try:
        # 1. 保存上传的PDF文件
        uploaded_file_info = await FileHandler.save_uploaded_pdf_file(
            file=file,
            save_directory=storage_paths["pdf_dir"]
        )
        pdf_filename = uploaded_file_info["saved_filename"]
        pdf_path = Path(uploaded_file_info["file_path"])
        print(f"PDF文件已保存: {pdf_path}")

        # 2. 创建临时工作目录并复制PDF
        temp_work_dir.mkdir(parents=True, exist_ok=True)
        temp_pdf_path = temp_work_dir / pdf_filename
        shutil.copy2(pdf_path, temp_pdf_path)
        
        # 3. 使用mineru转换PDF为Markdown
        print(f"开始转换PDF: {temp_pdf_path}")
        markdown_content = mineru_pdf2md(
            pdf_file_path=str(temp_pdf_path),
            md_output_path=str(temp_work_dir),
            return_path=False,
            backend=backend,
            method=method,
            web_images_dir=str(storage_paths["images_dir"])  # 传入web图片目录
        )
        
        # 4. 处理Markdown中的图片（如果需要）
        processed_markdown = markdown_content
        if parse_images:
            processed_markdown = await process_markdown_with_images(
                markdown_content, 
                str(temp_work_dir),
                provider,
                max_concurrent
            )
        
        # 5. 保存处理后的Markdown文件（如果需要）
        if storage_paths["keep_markdown_files"]:
            markdown_filename = f"{Path(pdf_filename).stem}_{processing_id}.md"
            markdown_path = storage_paths["markdown_dir"] / markdown_filename
            await save_markdown_file(processed_markdown, markdown_path)
        
        # 6. 获取文件信息
        file_size = pdf_path.stat().st_size
        creation_time = datetime.now().isoformat()
        
        # 7. 清理临时工作目录
        directory_cleaned = cleanup_temp_directory(temp_work_dir)
        
        # 8. 返回处理结果
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "task_id": processing_id,
                "document": {
                    "original_name": file.filename,
                    "stored_name": pdf_filename,
                    "size_bytes": file_size,
                    "mime_type": file.content_type,
                    "storage_path": str(pdf_path.relative_to(storage_paths["pdf_dir"].parent)),
                    "creation_timestamp": creation_time,
                },
                "markdown": {
                    "content": processed_markdown,
                    "path": str(markdown_path.relative_to(storage_paths["markdown_dir"].parent)) if storage_paths["keep_markdown_files"] and markdown_path else None,
                    "has_images": "![](" in processed_markdown or "![" in processed_markdown,
                    "images_processed": parse_images and "images" in processed_markdown.lower()
                },
                "processing": {
                    "provider": provider,
                    "backend": backend,
                    "method": method,
                    "image_analysis_enabled": parse_images,
                    "remote_base_url": remote_base_url,
                    "temp_directory_cleaned": directory_cleaned
                }
            }
        )
        
    except Exception as e:
        # 清理可能创建的文件
        try:
            if pdf_path and pdf_path.exists():
                pdf_path.unlink()
            cleanup_temp_directory(temp_work_dir)
        except Exception as cleanup_inner_error: 
            print(f"清理文件或目录时发生内部错误: {cleanup_inner_error}")
        
        print(f"PDF处理错误: {str(e)}")
        if isinstance(e, UnsupportedFileTypeError):
            raise HTTPException(status_code=400, detail=e.message)
        elif isinstance(e, FileSaveError):
            raise HTTPException(status_code=500, detail=e.message)
        else:
            raise HTTPException(status_code=500, detail=f"PDF处理失败: {str(e)}")


async def save_uploaded_pdfs(
    files: List[UploadFile], 
    save_directory: Path,
    temp_work_dir: Path
) -> tuple[List[Path], List[str]]:
    """保存上传的PDF文件并返回路径列表"""
    pdf_paths = []
    temp_pdf_paths = []
    
    for file in files:
        uploaded_file_info = await FileHandler.save_uploaded_pdf_file(
            file=file,
            save_directory=save_directory
        )
        pdf_filename = uploaded_file_info["saved_filename"]
        pdf_path = Path(uploaded_file_info["file_path"])
        pdf_paths.append(pdf_path)
        
        # 复制到临时目录
        temp_pdf_path = temp_work_dir / pdf_filename
        shutil.copy2(pdf_path, temp_pdf_path)
        temp_pdf_paths.append(str(temp_pdf_path))
    
    print(f"已保存 {len(pdf_paths)} 个PDF文件")
    return pdf_paths, temp_pdf_paths


async def process_single_pdf_result(
    result: Dict[str, Any],
    original_file: UploadFile,
    pdf_path: Path,
    temp_work_dir: str,
    storage_paths: Dict[str, Path],
    processing_id: str,
    idx: int,
    provider: str,
    max_concurrent: int,
    parse_images: bool
) -> Dict[str, Any]:
    """处理单个PDF结果，包括图片处理和保存Markdown"""
    markdown_content = result.get('md_content', '')
    
    # 处理图片（如果需要）
    processed_markdown = markdown_content
    if parse_images and markdown_content:
        processed_markdown = await process_markdown_with_images(
            markdown_content,
            temp_work_dir,
            provider,
            max_concurrent
        )
    
    # 保存Markdown文件
    markdown_path = None
    if storage_paths["keep_markdown_files"] and processed_markdown:
        pdf_filename = pdf_path.name
        markdown_filename = f"{Path(pdf_filename).stem}_{processing_id}_{idx}.md"
        markdown_path = storage_paths["markdown_dir"] / markdown_filename
        await save_markdown_file(processed_markdown, markdown_path)
    
    # 获取文件信息
    file_size = pdf_path.stat().st_size
    creation_time = datetime.now().isoformat()
    
    # 返回处理结果
    return {
        "document": {
            "original_name": original_file.filename,
            "stored_name": pdf_path.name,
            "size_bytes": file_size,
            "mime_type": original_file.content_type,
            "storage_path": str(pdf_path.relative_to(storage_paths["pdf_dir"].parent)),
            "creation_timestamp": creation_time
        },
        "markdown": {
            "content": processed_markdown,
            "path": str(markdown_path.relative_to(storage_paths["markdown_dir"].parent)) if storage_paths["keep_markdown_files"] and markdown_path else None,
            "has_images": "![](" in processed_markdown or "![" in processed_markdown,
            "images_processed": parse_images and "images" in processed_markdown.lower()
        }
    }


@router.post("/pdfs")
async def upload_and_process_multiple_pdfs(
    files: List[UploadFile] = File(...),
    provider: str = Form(default=DEFAULT_IMAGE_PROVIDER), 
    max_concurrent: int = Form(default=DEFAULT_MAX_CONCURRENT_AI),
    parse_images: bool = Form(default=True),
    backend: str = Form(default="pipeline"),
    method: str = Form(default="auto")
):
    """
    上传多个PDF文件，批量转换为Markdown，并可选择性处理图片
    
    Args:
        files: 要上传的PDF文件列表
        provider: AI视觉模型提供商 (guiji, zhipu, volces, openai)
        max_concurrent: 最大并发处理数
        parse_images: 是否对Markdown中的图片进行AI分析和处理
        backend: 解析PDF所用后端 (pipeline, vlm-transformers, vlm-sglang-engine)
        method: 解析PDF的方法 (auto, txt, ocr)
        
    Returns:
        包含处理后的Markdown内容列表的JSON响应
    """
    if not files:
        raise HTTPException(status_code=400, detail="未提供PDF文件")
    
    print(f"上传的文件数量: {len(files)}")
    print(f"provider: {provider}, backend: {backend}, method: {method}")
    
    remote_base_url = f"{get_api_base_url()}/uploads/images/"
    storage_paths = get_storage_paths()
    processing_id = uuid.uuid4().hex
    temp_work_dir = storage_paths["temp_dir"] / processing_id
    pdf_paths = []
    
    try:
        # 1. 创建临时工作目录
        temp_work_dir.mkdir(parents=True, exist_ok=True)
        
        # 2. 保存上传的PDF文件
        pdf_paths, temp_pdf_paths = await save_uploaded_pdfs(files, storage_paths["pdf_dir"], temp_work_dir)
        
        # 3. 使用mineru批量转换PDF为Markdown
        print("开始批量转换PDF...")
        pdf_results = mineru_multi_pdf2md(
            pdf_file_paths=temp_pdf_paths,
            md_output_path=str(temp_work_dir),
            return_content=True,
            backend=backend,
            method=method,
            web_images_dir=str(storage_paths["images_dir"])  # 传入web图片目录
        )
        
        # 4. 处理每个PDF结果
        processed_results = []
        for idx, result in enumerate(pdf_results):
            processed_result = await process_single_pdf_result(
                result=result,
                original_file=files[idx],
                pdf_path=pdf_paths[idx],
                temp_work_dir=str(temp_work_dir),
                storage_paths=storage_paths,
                processing_id=processing_id,
                idx=idx,
                provider=provider,
                max_concurrent=max_concurrent,
                parse_images=parse_images
            )
            processed_results.append(processed_result)
        
        # 5. 清理临时工作目录
        directory_cleaned = cleanup_temp_directory(temp_work_dir)
        
        # 6. 返回处理结果
        return JSONResponse(
            status_code=200,
            content={
                "success": True,
                "task_id": processing_id,
                "summary": {
                    "total_documents": len(files),
                    "processed_count": len(processed_results),
                    "message": f"成功处理 {len(processed_results)} 个PDF文件"
                },
                "documents": processed_results,
                "processing": {
                    "provider": provider,
                    "backend": backend,
                    "method": method,
                    "image_analysis_enabled": parse_images,
                    "remote_base_url": remote_base_url,
                    "temp_directory_cleaned": directory_cleaned
                }
            }
        )
        
    except Exception as e:
        # 清理可能创建的文件
        try:
            for pdf_path in pdf_paths:
                if pdf_path.exists():
                    pdf_path.unlink()
            cleanup_temp_directory(temp_work_dir)
        except Exception as cleanup_inner_error: 
            print(f"清理文件或目录时发生内部错误: {cleanup_inner_error}")
        
        print(f"批量PDF处理错误: {str(e)}")
        if isinstance(e, UnsupportedFileTypeError):
            raise HTTPException(status_code=400, detail=e.message)
        elif isinstance(e, FileSaveError):
            raise HTTPException(status_code=500, detail=e.message)
        else:
            raise HTTPException(status_code=500, detail=f"批量PDF处理失败: {str(e)}")
