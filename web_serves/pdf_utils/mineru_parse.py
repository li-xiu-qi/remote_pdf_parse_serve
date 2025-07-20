#!/usr/bin/env python
# -*- coding: utf-8 -*-
# author：筱可
# 2025-07-04 (Updated)
"""
#### 使用说明：
将PDF文档转换为Markdown格式，使用mineru库进行PDF解析和转换。

#### 主要功能：
1. 将PDF文件转换为Markdown格式
2. 提取PDF中的图片并保存
3. 支持处理单个或多个PDF文件
4. 支持pipeline和vlm两种后端处理方式

#### 参数说明：
mineru_pdf2md函数：
    - pdf_file_path: PDF文件的绝对路径(单个文件)或PDF文件路径列表(多个文件)
    - md_output_path: 输出Markdown文件的目录绝对路径
    - return_path: 是否返回生成的Markdown文件路径，默认为False
    - backend: 解析PDF所用后端，默认为"pipeline"，可选["pipeline", "vlm-transformers", "vlm-sglang-engine", "vlm-sglang-client"]
    - method: 解析PDF的方法，默认为"auto"，可选["auto", "txt", "ocr"]
    - 返回值: 如果return_path=True，返回生成的Markdown文件路径；否则返回Markdown内容

mineru_multi_pdf2md函数：
    - pdf_file_paths: PDF文件路径列表
    - md_output_path: 输出Markdown文件的目录绝对路径
    - return_content: 是否返回Markdown内容，默认为True
    - 其他参数同mineru_pdf2md
    - 返回值: 包含每个PDF处理结果的字典列表

#### 注意事项：
- 依赖mineru库进行PDF解析和转换
- 输入的PDF文件路径和输出路径必须为绝对路径
- 自动创建输出目录和图片目录
"""

import os
import shutil
import json
import hashlib
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
import re
import diskcache as dc

# Set environment variable for model source if needed
os.environ.setdefault('MINERU_MODEL_SOURCE', "modelscope")


# 初始化缓存，最大空间100GB
CACHE_DIR = os.path.join(os.path.expanduser("."), ".cache", "remote_pdf_parse_serve")
cache = dc.Cache(CACHE_DIR, size_limit=100 * 1024 ** 3)


def convert_image_paths_to_absolute_urls(markdown_content: str, base_url: str) -> str:
    """
    将markdown中的相对图片路径转换为绝对URL路径
    
    参数:
        markdown_content: markdown内容
        base_url: 基础URL路径，如 "/uploads/images/"
        
    返回:
        转换后的markdown内容
    """
    # 匹配markdown图片语法: ![alt](images/filename)
    pattern = r'!\[([^\]]*)\]\(images/([^)]+)\)'
    
    def replace_image_path(match):
        alt_text = match.group(1)
        filename = match.group(2)
        # 构建绝对URL路径
        absolute_url = f"{base_url}{filename}"
        return f"![{alt_text}]({absolute_url})"
    
    # 替换所有匹配的图片路径
    converted_content = re.sub(pattern, replace_image_path, markdown_content)
    return converted_content


def get_parsed_pdf_results(
        path_list: list[Path],
        output_dir,
        lang="ch",
        backend="pipeline",
        method="auto",
        server_url=None,
        start_page_id=0,
        end_page_id=None,
        web_images_dir=None,  # web服务的图片目录
        use_cache=True  # 是否使用缓存
):
    """
    解析PDF文件并返回结果列表，每个结果包含文件路径和Markdown内容
    
    参数:
        path_list: 需要解析的文档路径列表
        output_dir: 解析结果输出目录
        lang: 语言选项
        backend: 解析pdf所用后端
        method: 解析pdf的方法
        server_url: 服务器URL
        start_page_id: 解析起始页码
        end_page_id: 解析结束页码
        web_images_dir: web服务的图片目录路径，如果提供则图片会额外复制到此目录
        use_cache: 是否使用缓存
        
    返回:
        包含字典的列表，每个字典包含文件路径和Markdown内容
    """
    from mineru.cli.common import prepare_env, convert_pdf_bytes_to_bytes_by_pypdfium2, read_fn
    from mineru.data.data_reader_writer import FileBasedDataWriter
    from mineru.utils.draw_bbox import draw_layout_bbox, draw_span_bbox
    from mineru.utils.enum_class import MakeMode
    
    if backend == "pipeline":
        from mineru.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
        from mineru.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
        from mineru.backend.pipeline.model_json_to_middle_json import result_to_middle_json as pipeline_result_to_middle_json
    else:
        from mineru.backend.vlm.vlm_analyze import doc_analyze as vlm_doc_analyze
        from mineru.backend.vlm.vlm_middle_json_mkcontent import union_make as vlm_union_make
    
    file_name_list = []
    pdf_bytes_list = []
    lang_list = []
    for path in path_list:
        file_name = str(Path(path).stem)
        pdf_bytes = read_fn(path)
        file_name_list.append(file_name)
        pdf_bytes_list.append(pdf_bytes)
        lang_list.append(lang)
    
    results = []
    
    # 处理每个PDF文件
    for idx, pdf_bytes in enumerate(pdf_bytes_list):
        pdf_file_name = file_name_list[idx]
        
        # 生成缓存key
        cache_key = None
        if use_cache:
            cache_key = generate_pdf_cache_key(
                pdf_bytes, backend, method, lang, start_page_id, end_page_id
            )
            
            # 尝试从缓存获取结果
            cached_result = get_cached_result(cache_key)
            if cached_result:
                try:
                    # 从缓存恢复文件
                    restore_result = restore_cached_files(
                        cached_result, output_dir, pdf_file_name, method, web_images_dir
                    )
                    results.append({
                        'file_path': str(path_list[idx]),
                        'md_path': restore_result['md_path'],
                        'md_content': restore_result['md_content']
                    })
                    continue  # 跳过实际解析，使用缓存结果
                except Exception as e:
                    print(f"缓存结果恢复失败: {e}，将重新解析")
        
        # 如果缓存未命中或不使用缓存，进行实际解析
        if backend == "pipeline":
            # Pipeline backend 处理
            new_pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, start_page_id, end_page_id)
            
            # 单个文件解析
            infer_results, all_image_lists, all_pdf_docs, processed_lang_list, ocr_enabled_list = pipeline_doc_analyze(
                [new_pdf_bytes], [lang], parse_method=method, formula_enable=True, table_enable=True
            )
            
            model_list = infer_results[0]
            images_list = all_image_lists[0]
            pdf_doc = all_pdf_docs[0]
            _lang = processed_lang_list[0]
            _ocr_enable = ocr_enabled_list[0]
            
            local_image_dir, local_md_dir = prepare_env(output_dir, pdf_file_name, method)
            image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)
            
            # Store model output for future use if needed
            model_output_json = model_list.copy()
            # Save model output to file
            md_writer.write_string(
                f"{pdf_file_name}_model.json",
                json.dumps(model_output_json, ensure_ascii=False, indent=4),
            )

            middle_json = pipeline_result_to_middle_json(model_list, images_list, pdf_doc, image_writer, _lang, _ocr_enable, True)
            pdf_info = middle_json["pdf_info"]

            # 先生成临时的markdown内容
            image_dir = "images"  # 临时使用相对路径生成
            md_content_str = pipeline_union_make(pdf_info, MakeMode.MM_MD, image_dir)
            
            # 将markdown中的相对图片路径转换为绝对URL路径
            if web_images_dir:
                md_content_str = convert_image_paths_to_absolute_urls(md_content_str, "/uploads/images/")
            
            md_path = os.path.join(local_md_dir, f"{pdf_file_name}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content_str)
            
            # 保存原始PDF
            md_writer.write(f"{pdf_file_name}_origin.pdf", new_pdf_bytes)
            
            # 绘制布局框
            draw_layout_bbox(pdf_info, new_pdf_bytes, local_md_dir, f"{pdf_file_name}_layout.pdf")
            
            # 如果指定了web图片目录，将图片复制到该目录
            if web_images_dir:
                os.makedirs(web_images_dir, exist_ok=True)
                if os.path.exists(local_image_dir):
                    for img_file in os.listdir(local_image_dir):
                        if img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                            src_path = os.path.join(local_image_dir, img_file)
                            dst_path = os.path.join(web_images_dir, img_file)
                            shutil.copy2(src_path, dst_path)
            
            # 保存到缓存
            if use_cache and cache_key:
                try:
                    cached_data = cache_result_from_files(local_image_dir, local_md_dir, pdf_file_name, md_content_str)
                    save_to_cache(cache_key, cached_data)
                except Exception as e:
                    print(f"缓存保存失败: {e}")
            
            results.append({
                'file_path': str(path_list[idx]),
                'md_path': md_path,
                'md_content': md_content_str
            })
            
        else:
            # VLM backend 处理
            backend_name = backend[4:] if backend.startswith("vlm-") else backend
            parse_method = "vlm"
            
            pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, start_page_id, end_page_id)
            local_image_dir, local_md_dir = prepare_env(output_dir, pdf_file_name, parse_method)
            image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)
            middle_json, _ = vlm_doc_analyze(pdf_bytes, image_writer=image_writer, backend=backend_name, server_url=server_url)

            pdf_info = middle_json["pdf_info"]

            # 先生成临时的markdown内容
            image_dir = "images"  # 临时使用相对路径生成
            md_content_str = vlm_union_make(pdf_info, MakeMode.MM_MD, image_dir)
            
            # 将markdown中的相对图片路径转换为绝对URL路径
            if web_images_dir:
                md_content_str = convert_image_paths_to_absolute_urls(md_content_str, "/uploads/images/")
            
            md_path = os.path.join(local_md_dir, f"{pdf_file_name}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content_str)
            
            # 保存原始PDF
            md_writer.write(f"{pdf_file_name}_origin.pdf", pdf_bytes)
            
            # 绘制布局框
            draw_layout_bbox(pdf_info, pdf_bytes, local_md_dir, f"{pdf_file_name}_layout.pdf")

            # 如果指定了web图片目录，将图片复制到该目录
            if web_images_dir:
                os.makedirs(web_images_dir, exist_ok=True)
                if os.path.exists(local_image_dir):
                    for img_file in os.listdir(local_image_dir):
                        if img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                            src_path = os.path.join(local_image_dir, img_file)
                            dst_path = os.path.join(web_images_dir, img_file)
                            shutil.copy2(src_path, dst_path)

            # 保存到缓存
            if use_cache and cache_key:
                try:
                    cached_data = cache_result_from_files(local_image_dir, local_md_dir, pdf_file_name, md_content_str)
                    save_to_cache(cache_key, cached_data)
                except Exception as e:
                    print(f"缓存保存失败: {e}")

            results.append({
                'file_path': str(path_list[idx]),
                'md_path': md_path,
                'md_content': md_content_str
            })
    
    return results


def mineru_pdf2md(pdf_file_path, md_output_path, return_path=False, backend="pipeline", method="auto", lang="ch", web_images_dir=None, use_cache=True):
    """
    将PDF文件转换为Markdown格式
    
    参数:
        pdf_file_path: PDF文件的绝对路径
        md_output_path: 输出Markdown文件的目录绝对路径
        return_path: 是否返回生成的Markdown文件路径，默认为False
        backend: 解析PDF所用后端，默认为"pipeline"，可选["pipeline", "vlm-transformers", "vlm-sglang-engine", "vlm-sglang-client"]
        method: 解析PDF的方法，默认为"auto"，可选["auto", "txt", "ocr"]
        lang: 语言选项，默认为"ch"
        web_images_dir: web服务的图片目录路径，图片会额外复制到此目录
        use_cache: 是否使用缓存，默认为True
        
    返回:
        如果return_path=True，返回生成的Markdown文件路径；否则返回生成的Markdown内容
        
    异常:
        ValueError: 当路径不是绝对路径时
        FileNotFoundError: 当PDF文件不存在时
    """
    # 检查是否为绝对路径
    if not os.path.isabs(pdf_file_path):
        raise ValueError(f"PDF文件路径必须是绝对路径: {pdf_file_path}")
    if not os.path.isabs(md_output_path):
        raise ValueError(f"Markdown输出路径必须是绝对路径: {md_output_path}")

    # 检查PDF文件是否存在
    if not os.path.isfile(pdf_file_path):
        raise FileNotFoundError(f"PDF文件未找到: {pdf_file_path}")
    
    # 调用多文件解析函数处理单个文件
    results = get_parsed_pdf_results(
        path_list=[Path(pdf_file_path)],
        output_dir=md_output_path,
        lang=lang,
        backend=backend,
        method=method,
        web_images_dir=web_images_dir,
        use_cache=use_cache
    )
    
    # 确保结果不为空
    if not results:
        raise RuntimeError("PDF解析失败，未返回结果")
    
    result = results[0]
    
    if return_path:
        return result['md_path']
    else:
        return result['md_content']


def mineru_multi_pdf2md(pdf_file_paths: List[str], md_output_path: str, return_content=True, 
                        backend="pipeline", method="auto", lang="ch", web_images_dir=None, use_cache=True) -> List[Dict[str, Any]]:
    """
    批量处理多个PDF文件，转换为Markdown格式
    
    参数:
        pdf_file_paths: PDF文件的绝对路径列表
        md_output_path: 输出Markdown文件的目录绝对路径
        return_content: 是否返回Markdown内容，默认为True
        backend: 解析PDF所用后端
        method: 解析PDF的方法
        lang: 语言选项
        web_images_dir: web服务的图片目录路径，图片会额外复制到此目录
        use_cache: 是否使用缓存，默认为True
        
    返回:
        包含每个PDF处理结果的字典列表
    """
    # 检查路径有效性
    for pdf_path in pdf_file_paths:
        if not os.path.isabs(pdf_path):
            raise ValueError(f"PDF文件路径必须是绝对路径: {pdf_path}")
        if not os.path.isfile(pdf_path):
            raise FileNotFoundError(f"PDF文件未找到: {pdf_path}")
    
    if not os.path.isabs(md_output_path):
        raise ValueError(f"Markdown输出路径必须是绝对路径: {md_output_path}")
    
    # 确保输出目录存在
    os.makedirs(md_output_path, exist_ok=True)
    
    # 调用多文件解析函数
    results = get_parsed_pdf_results(
        path_list=[Path(path) for path in pdf_file_paths],
        output_dir=md_output_path,
        lang=lang,
        backend=backend,
        method=method,
        web_images_dir=web_images_dir,
        use_cache=use_cache
    )
    
    # 如果不需要返回内容，则删除md_content字段
    if not return_content:
        for result in results:
            if 'md_content' in result:
                del result['md_content']
    
    return results


def generate_pdf_cache_key(pdf_bytes: bytes, backend: str, method: str, lang: str, 
                          start_page_id: int, end_page_id: Optional[int]) -> str:
    """
    生成PDF缓存key，基于文件前8k内容和解析参数
    
    参数:
        pdf_bytes: PDF文件二进制内容
        backend: 解析后端
        method: 解析方法
        lang: 语言
        start_page_id: 开始页码
        end_page_id: 结束页码
        
    返回:
        缓存key字符串
    """
    # 取前8k内容作为文件标识
    file_content = pdf_bytes[:8192]
    
    # 生成文件内容的哈希值
    file_hash = hashlib.sha256(file_content).hexdigest()
    
    # 结合解析参数生成完整的缓存key
    params = f"{backend}_{method}_{lang}_{start_page_id}_{end_page_id}"
    cache_key = f"pdf_parse_{file_hash}_{hashlib.md5(params.encode()).hexdigest()}"
    
    return cache_key


def get_cached_result(cache_key: str):
    """
    从缓存获取解析结果
    
    参数:
        cache_key: 缓存key
        
    返回:
        缓存的解析结果，如果不存在则返回None
    """
    try:
        return cache.get(cache_key)
    except Exception as e:
        print(f"缓存读取失败: {e}")
        return None


def save_to_cache(cache_key: str, result: Dict[str, Any], expire_time: int = 7 * 24 * 3600):
    """
    保存解析结果到缓存
    
    参数:
        cache_key: 缓存key
        result: 解析结果
        expire_time: 过期时间（秒），默认7天
    """
    try:
        cache.set(cache_key, result, expire=expire_time)
    except Exception as e:
        print(f"缓存保存失败: {e}")


def restore_cached_files(cached_result: Dict[str, Any], output_dir: str, 
                        pdf_file_name: str, method: str, web_images_dir: Optional[str] = None):
    """
    从缓存结果恢复文件到指定目录
    
    参数:
        cached_result: 缓存的解析结果
        output_dir: 输出目录
        pdf_file_name: PDF文件名
        method: 解析方法
        web_images_dir: web服务的图片目录路径
        
    返回:
        包含文件路径和内容的字典
    """
    from mineru.cli.common import prepare_env
    
    # 准备输出目录
    local_image_dir, local_md_dir = prepare_env(output_dir, pdf_file_name, method)
    
    # 恢复markdown文件
    md_content = cached_result.get('md_content', '')
    md_path = os.path.join(local_md_dir, f"{pdf_file_name}.md")
    
    # 如果有web图片目录，更新markdown中的图片路径
    if web_images_dir:
        md_content = convert_image_paths_to_absolute_urls(md_content, "/uploads/images/")
    
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    
    # 恢复图片文件
    cached_images = cached_result.get('images', {})
    for img_name, img_data in cached_images.items():
        img_path = os.path.join(local_image_dir, img_name)
        with open(img_path, "wb") as f:
            f.write(img_data)
        
        # 如果指定了web图片目录，也复制到那里
        if web_images_dir:
            os.makedirs(web_images_dir, exist_ok=True)
            web_img_path = os.path.join(web_images_dir, img_name)
            shutil.copy2(img_path, web_img_path)
    
    # 恢复其他文件
    cached_files = cached_result.get('files', {})
    for file_name, file_data in cached_files.items():
        file_path = os.path.join(local_md_dir, file_name)
        if isinstance(file_data, str):
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(file_data)
        else:
            with open(file_path, "wb") as f:
                f.write(file_data)
    
    return {
        'md_path': md_path,
        'md_content': md_content
    }


def cache_result_from_files(local_image_dir: str, local_md_dir: str, 
                           pdf_file_name: str, md_content: str) -> Dict[str, Any]:
    """
    从文件系统中收集需要缓存的结果
    
    参数:
        local_image_dir: 图片目录
        local_md_dir: markdown目录
        pdf_file_name: PDF文件名
        md_content: markdown内容
        
    返回:
        包含缓存数据的字典
    """
    cached_result = {
        'md_content': md_content,
        'images': {},
        'files': {}
    }
    
    # 收集图片文件
    if os.path.exists(local_image_dir):
        for img_file in os.listdir(local_image_dir):
            if img_file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                img_path = os.path.join(local_image_dir, img_file)
                with open(img_path, "rb") as f:
                    cached_result['images'][img_file] = f.read()
    
    # 收集其他文件（如JSON、PDF等）
    if os.path.exists(local_md_dir):
        for file_name in os.listdir(local_md_dir):
            if file_name != f"{pdf_file_name}.md":  # 排除主要的markdown文件
                file_path = os.path.join(local_md_dir, file_name)
                if os.path.isfile(file_path):
                    if file_name.endswith('.json'):
                        with open(file_path, "r", encoding="utf-8") as f:
                            cached_result['files'][file_name] = f.read()
                    else:
                        with open(file_path, "rb") as f:
                            cached_result['files'][file_name] = f.read()
    
    return cached_result


def clear_pdf_cache():
    """
    清理PDF解析缓存
    
    返回:
        清理是否成功
    """
    try:
        cache.clear()
        return True
    except Exception as e:
        print(f"缓存清理失败: {e}")
        return False


def get_cache_stats():
    """
    获取缓存统计信息
    
    返回:
        包含缓存统计信息的字典
    """
    try:
        return {
            'cache_size': len(cache),
            'cache_directory': CACHE_DIR,
            'disk_usage': cache.volume(),
        }
    except Exception as e:
        print(f"获取缓存统计信息失败: {e}")
        return {}
