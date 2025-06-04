#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片上传相关路由
"""
import os
import uuid
import shutil
from typing import List
from pathlib import Path

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse

from web_serves.config import ALLOWED_EXTENSIONS, UPLOAD_DIR, IMAGES_DIR


router = APIRouter(prefix="/upload", tags=["图片上传"])


def is_allowed_file(filename: str) -> bool:
    """检查文件扩展名是否被允许"""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """
    上传单个图片文件
    
    Args:
        file: 要上传的图片文件
        
    Returns:
        包含文件信息的 JSON 响应
    """
    # 检查文件是否存在
    if not file.filename:
        raise HTTPException(status_code=400, detail="没有选择文件")
    
    # 检查文件类型
    if not is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件类型。支持的格式: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    try:
        # 生成唯一文件名（使用十六进制UUID）
        file_extension = Path(file.filename).suffix.lower()
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = IMAGES_DIR / unique_filename
        
        # 保存文件
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 获取文件大小
        file_size = os.path.getsize(file_path)
        
        return JSONResponse(
            status_code=200,
            content={
                "message": "文件上传成功",
                "file_info": {
                    "original_filename": file.filename,
                    "saved_filename": unique_filename,
                    "file_path": str(file_path),
                    "file_size": file_size,
                    "content_type": file.content_type
                }
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件上传失败: {str(e)}")


@router.post("/images")
async def upload_images(files: List[UploadFile] = File(...)):
    """
    上传多个图片文件
    
    Args:
        files: 要上传的图片文件列表
        
    Returns:
        包含所有文件信息的 JSON 响应
    """
    if not files:
        raise HTTPException(status_code=400, detail="没有选择文件")
    
    uploaded_files = []
    failed_files = []
    
    for file in files:
        try:
            # 检查文件是否存在
            if not file.filename:
                failed_files.append({
                    "filename": "未知文件",
                    "error": "没有文件名"
                })
                continue
            
            # 检查文件类型
            if not is_allowed_file(file.filename):
                failed_files.append({
                    "filename": file.filename,          
                    "error": f"不支持的文件类型。支持的格式: {', '.join(ALLOWED_EXTENSIONS)}"
                })
                continue
              # 生成唯一文件名（使用十六进制UUID）
            file_extension = Path(file.filename).suffix.lower()
            unique_filename = f"{uuid.uuid4().hex}{file_extension}"
            file_path = IMAGES_DIR / unique_filename
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            uploaded_files.append({
                "original_filename": file.filename,
                "saved_filename": unique_filename,
                "file_path": str(file_path),
                "file_size": file_size,
                "content_type": file.content_type
            })
            
        except Exception as e:
            failed_files.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return JSONResponse(
        status_code=200,
        content={
            "message": f"处理完成。成功: {len(uploaded_files)}, 失败: {len(failed_files)}",
            "uploaded_files": uploaded_files,
            "failed_files": failed_files
        }
    )
