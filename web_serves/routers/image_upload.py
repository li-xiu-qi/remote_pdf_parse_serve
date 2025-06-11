#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
图片上传相关路由
"""
from typing import List

from fastapi import APIRouter, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse

from web_serves.config import IMAGES_DIR
from web_serves.utils.file_handler import FileHandler
from web_serves.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/upload", tags=["图片上传"])


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    """
    上传单个图片文件
    
    Args:
        file: 要上传的图片文件
        
    Returns:
        包含文件信息的 JSON 响应
    """
    try:
        file_info = await FileHandler.save_uploaded_file(file, IMAGES_DIR)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "文件上传成功",
                "file_info": file_info
            }
        )
        
    except Exception as e:
        return JSONResponse(
            status_code=e.status_code if hasattr(e, 'status_code') else 500,
            content={"detail": str(e)}
        )


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
            file_info = await FileHandler.save_uploaded_file(file, IMAGES_DIR)
            uploaded_files.append(file_info)
            
        except HTTPException as e:
            failed_files.append({
                "filename": file.filename or "未知文件",
                "error": e.detail
            })
        except Exception as e:
            failed_files.append({
                "filename": file.filename or "未知文件", 
                "error": str(e)
            })
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message": f"处理完成。成功: {len(uploaded_files)}, 失败: {len(failed_files)}",
            "uploaded_files": uploaded_files,
            "failed_files": failed_files
        }
    )
