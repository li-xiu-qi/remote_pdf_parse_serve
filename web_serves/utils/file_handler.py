#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
文件处理工具类 - 统一文件上传逻辑
"""
import os
import uuid
import shutil
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import UploadFile

from web_serves.exceptions import UnsupportedFileTypeError, FileSaveError
from web_serves.utils.logger import get_logger
from web_serves.config import app_config # Import app_config

logger = get_logger(__name__)


class FileHandler:
    """文件处理工具类"""
    
    @staticmethod
    def _get_file_extension(filename: str) -> str:
        """获取文件扩展名（小写）"""
        return Path(filename).suffix.lower()

    @staticmethod
    def _ensure_directory(path: Path) -> None:
        """确保目录存在，如果不存在则创建"""
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _is_image_file(filename: str) -> bool:
        """检查是否为支持的图片格式"""
        if not filename:
            return False
        ext = FileHandler._get_file_extension(filename)
        return ext in app_config.upload.supported_image_extensions # Use app_config

    @staticmethod
    def _is_pdf_file(filename: str) -> bool:
        """检查是否为支持的PDF格式"""
        if not filename:
            return False
        ext = FileHandler._get_file_extension(filename)
        return ext in app_config.upload.supported_pdf_extensions # Use app_config
    
    @staticmethod
    def generate_unique_filename(original_filename: str) -> str:
        """生成唯一文件名"""
        file_extension = FileHandler._get_file_extension(original_filename)
        return f"{uuid.uuid4().hex}{file_extension}"
    
    @staticmethod
    async def save_uploaded_file(
        file: UploadFile, 
        save_directory: Path,
        custom_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        保存上传的文件
        
        Args:
            file: 上传的文件
            save_directory: 保存目录
            custom_filename: 自定义文件名，如果为None则自动生成
            
        Returns:
            包含文件信息的字典
            
        Raises:
            UnsupportedFileTypeError: 文件类型不支持
            FileSaveError: 文件保存失败
        """
        # 检查文件是否存在
        if not file.filename:
            # 保持和之前一致，如果文件名不存在，则认为是类型不支持
            raise UnsupportedFileTypeError("文件名为空", []) 
        
        # 检查文件类型，调用 path_manager 中的 is_image_file
        if not FileHandler._is_image_file(file.filename): 
            raise UnsupportedFileTypeError(
                file.filename, 
                list(app_config.upload.supported_image_extensions) # Use app_config
            )
        
        try:
            # 确保保存目录存在
            FileHandler._ensure_directory(save_directory)
            
            # 生成文件名
            filename = custom_filename or FileHandler.generate_unique_filename(file.filename)
            file_path = save_directory / filename
            
            # 保存文件
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # 获取文件大小
            file_size = os.path.getsize(file_path)
            
            logger.info(f"文件保存成功: {file.filename} -> {file_path}")
            
            return {
                "original_filename": file.filename,
                "saved_filename": filename,
                "file_path": str(file_path),
                "file_size": file_size,
                "content_type": file.content_type
            }
            
        except Exception as e:
            logger.error(f"文件保存失败: {file.filename}, 错误: {e}")
            # 确保 FileSaveError 的参数正确
            # 使用 file.filename 作为回退，如果 custom_filename 和 original_filename 都不可用
            actual_filename_for_error = custom_filename or file.filename or "unknown_file"
            raise FileSaveError(str(save_directory / actual_filename_for_error), str(e))

    @staticmethod
    async def save_uploaded_pdf_file(
        file: UploadFile, 
        save_directory: Path,
        custom_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        保存上传的PDF文件
        
        Args:
            file: 上传的文件
            save_directory: 保存目录
            custom_filename: 自定义文件名，如果为None则自动生成
            
        Returns:
            包含文件信息的字典
            
        Raises:
            UnsupportedFileTypeError: 文件类型不支持或文件名为空
            FileSaveError: 文件保存失败
        """
        if not file.filename:
            raise UnsupportedFileTypeError("文件名为空", list(app_config.upload.supported_pdf_extensions)) # Use app_config
        
        if not FileHandler._is_pdf_file(file.filename): 
            raise UnsupportedFileTypeError(
                file.filename, 
                list(app_config.upload.supported_pdf_extensions) # Use app_config
            )
        
        try:
            FileHandler._ensure_directory(save_directory)
            
            # Use custom_filename if provided, otherwise generate a unique one
            filename_to_save = custom_filename or FileHandler.generate_unique_filename(file.filename)
            file_path = save_directory / filename_to_save
            
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            file_size = os.path.getsize(file_path)
            
            logger.info(f"PDF文件保存成功: {file.filename} -> {file_path}")
            
            return {
                "original_filename": file.filename,
                "saved_filename": filename_to_save, # Return the actual saved name
                "file_path": str(file_path),
                "file_size": file_size,
                "content_type": file.content_type or "application/pdf" # Fallback content type
            }
            
        except Exception as e:
            logger.error(f"PDF文件保存失败: {file.filename}, 错误: {e}")
            actual_filename_for_error = custom_filename or file.filename or "unknown_file"
            raise FileSaveError(str(save_directory / actual_filename_for_error), str(e))
