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
from pathlib import Path
from typing import List, Union, Dict, Any, Optional
import re

# Set environment variable for model source if needed
os.environ.setdefault('MINERU_MODEL_SOURCE', "modelscope")


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
        web_images_dir=None  # 新增参数：web服务的图片目录
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
    
    if backend == "pipeline":
        for idx, pdf_bytes in enumerate(pdf_bytes_list):
            new_pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, start_page_id, end_page_id)
            pdf_bytes_list[idx] = new_pdf_bytes

        infer_results, all_image_lists, all_pdf_docs, lang_list, ocr_enabled_list = pipeline_doc_analyze(pdf_bytes_list, lang_list, parse_method=method, formula_enable=True, table_enable=True)

        for idx, model_list in enumerate(infer_results):
            pdf_file_name = file_name_list[idx]
            local_image_dir, local_md_dir = prepare_env(output_dir, pdf_file_name, method)
            image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)
            
            # Store model output for future use if needed
            model_output_json = model_list.copy()
            # Save model output to file
            md_writer.write_string(
                f"{pdf_file_name}_model.json",
                json.dumps(model_output_json, ensure_ascii=False, indent=4),
            )

            images_list = all_image_lists[idx]
            pdf_doc = all_pdf_docs[idx]
            _lang = lang_list[idx]
            _ocr_enable = ocr_enabled_list[idx]
            middle_json = pipeline_result_to_middle_json(model_list, images_list, pdf_doc, image_writer, _lang, _ocr_enable, True)

            pdf_info = middle_json["pdf_info"]

            # 生成MD文件 - 使用绝对URL路径
            # 先生成临时的markdown内容
            image_dir = "images"  # 临时使用相对路径生成
            md_content_str = pipeline_union_make(pdf_info, MakeMode.MM_MD, image_dir)
            
            # 将markdown中的相对图片路径转换为绝对URL路径
            if web_images_dir:
                # 使用绝对URL路径
                md_content_str = convert_image_paths_to_absolute_urls(md_content_str, "/uploads/images/")
            
            md_path = os.path.join(local_md_dir, f"{pdf_file_name}.md")
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_content_str)
            
            # 保存原始PDF
            pdf_bytes = pdf_bytes_list[idx]
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
            
            results.append({
                'file_path': str(path_list[idx]),
                'md_path': md_path,
                'md_content': md_content_str
            })
            
    else:
        # VLM backend
        backend_name = backend[4:] if backend.startswith("vlm-") else backend
        parse_method = "vlm"
        
        for idx, pdf_bytes in enumerate(pdf_bytes_list):
            pdf_file_name = file_name_list[idx]
            pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, start_page_id, end_page_id)
            local_image_dir, local_md_dir = prepare_env(output_dir, pdf_file_name, parse_method)
            image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)
            middle_json, _ = vlm_doc_analyze(pdf_bytes, image_writer=image_writer, backend=backend_name, server_url=server_url)

            pdf_info = middle_json["pdf_info"]

            # 生成MD文件 - 使用绝对URL路径
            # 先生成临时的markdown内容
            image_dir = "images"  # 临时使用相对路径生成
            md_content_str = vlm_union_make(pdf_info, MakeMode.MM_MD, image_dir)
            
            # 将markdown中的相对图片路径转换为绝对URL路径
            if web_images_dir:
                # 使用绝对URL路径
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

            results.append({
                'file_path': str(path_list[idx]),
                'md_path': md_path,
                'md_content': md_content_str
            })
    
    return results


def mineru_pdf2md(pdf_file_path, md_output_path, return_path=False, backend="pipeline", method="auto", lang="ch", web_images_dir=None):
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
        
    返回:
        如果return_path=True，返回生成的Markdown文件路径；否则返回Markdown内容
        
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
        web_images_dir=web_images_dir
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
                        backend="pipeline", method="auto", lang="ch", web_images_dir=None) -> List[Dict[str, Any]]:
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
        web_images_dir=web_images_dir
    )
    
    # 如果不需要返回内容，则删除md_content字段
    if not return_content:
        for result in results:
            if 'md_content' in result:
                del result['md_content']
    
    return results
