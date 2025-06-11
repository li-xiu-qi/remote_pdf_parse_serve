#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
统一日志配置管理
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from web_serves.config import app_config


class LoggerManager:
    """日志管理器 - 提供统一的日志配置"""
    
    _initialized = False
    _loggers = {}
    
    @classmethod
    def setup_logging(
        cls,
        level: Optional[str] = None, # Changed default to None
        log_file: Optional[str] = None,
        console_output: bool = True
    ):
        """
        设置全局日志配置
        
        Args:
            level: 日志级别 (e.g., "INFO", "DEBUG"). Defaults to config.json.
            log_file: 日志文件路径（可选）
            console_output: 是否输出到控制台
        """
        if cls._initialized:
            return
            
        # Use level from config if not provided, otherwise use the provided level
        log_level_to_use = level if level else app_config.logging.level
        log_format_to_use = app_config.logging.format

        # 设置根日志器
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, log_level_to_use.upper()))
        
        # 清除已有的处理器
        root_logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(log_format_to_use) # Use format from config
        
        # 控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        
        cls._initialized = True
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        获取指定名称的日志器
        
        Args:
            name: 日志器名称
            
        Returns:
            logging.Logger: 日志器实例
        """
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def get_module_logger(cls, module_name: str) -> logging.Logger:
        """
        为模块获取日志器
        
        Args:
            module_name: 模块名称（通常使用 __name__）
            
        Returns:
            logging.Logger: 日志器实例
        """
        return cls.get_logger(module_name)


# 便捷函数
def get_logger(name: str = None) -> logging.Logger:
    """
    获取日志器的便捷函数
    
    Args:
        name: 日志器名称，如果为None则使用调用模块名称
        
    Returns:
        logging.Logger: 日志器实例
    """
    if name is None:
        # 获取调用方的模块名
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    
    return LoggerManager.get_module_logger(name)
