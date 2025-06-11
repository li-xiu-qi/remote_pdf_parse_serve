#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
自定义异常类 - 统一项目异常处理
"""


class BaseAppException(Exception):
    """应用基础异常类"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class FileProcessingError(BaseAppException):
    """文件处理相关异常"""
    pass


class FileNotFoundError(FileProcessingError):
    """文件未找到异常"""
    def __init__(self, file_path: str):
        super().__init__(
            message=f"文件未找到: {file_path}",
            error_code="FILE_NOT_FOUND",
            details={"file_path": file_path}
        )


class UnsupportedFileTypeError(FileProcessingError):
    """不支持的文件类型异常"""
    def __init__(self, filename: str, supported_types: list = None):
        supported_msg = f"支持的格式: {', '.join(supported_types)}" if supported_types else ""
        super().__init__(
            message=f"不支持的文件类型. {supported_msg}",
            error_code="UNSUPPORTED_FILE_TYPE",
            details={
                "filename": filename,
                "supported_types": supported_types or []
            }
        )


class FileSaveError(FileProcessingError):
    """文件保存异常"""
    def __init__(self, file_path: str, original_error: str = None):
        message = f"文件保存失败: {file_path}"
        if original_error:
            message += f" - {original_error}"
        super().__init__(
            message=message,
            error_code="FILE_SAVE_ERROR",
            details={
                "file_path": file_path,
                "original_error": original_error
            }
        )


class InvalidPathError(FileProcessingError):
    """无效路径异常"""
    def __init__(self, path: str, reason: str = "路径无效"):
        super().__init__(
            message=f"{reason}: {path}",
            error_code="INVALID_PATH",
            details={"path": path, "reason": reason}
        )


class ConfigurationError(BaseAppException):
    """配置相关异常"""
    pass


class APIError(BaseAppException):
    """API相关异常"""
    def __init__(self, message: str, status_code: int = 500, **kwargs):
        self.status_code = status_code
        super().__init__(message, **kwargs)


class ProcessingError(BaseAppException):
    """处理相关异常"""
    pass


class PDFProcessingError(ProcessingError):
    """PDF处理异常"""
    def __init__(self, pdf_path: str, error_detail: str):
        super().__init__(
            message=f"PDF处理失败: {pdf_path} - {error_detail}",
            error_code="PDF_PROCESSING_ERROR",
            details={
                "pdf_path": pdf_path,
                "error_detail": error_detail
            }
        )


class ImageAnalysisError(ProcessingError):
    """图片分析异常"""
    def __init__(self, image_path: str, error_detail: str):
        super().__init__(
            message=f"图片分析失败: {image_path} - {error_detail}",
            error_code="IMAGE_ANALYSIS_ERROR",
            details={
                "image_path": image_path,
                "error_detail": error_detail
            }
        )
