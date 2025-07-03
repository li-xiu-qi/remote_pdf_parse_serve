# Copyright (c) Opendatalab. All rights reserved.
import copy
import json
import os
from pathlib import Path

from loguru import logger

from mineru.cli.common import convert_pdf_bytes_to_bytes_by_pypdfium2, prepare_env, read_fn
from mineru.data.data_reader_writer import FileBasedDataWriter
from mineru.utils.draw_bbox import draw_layout_bbox, draw_span_bbox
from mineru.utils.enum_class import MakeMode
from mineru.backend.vlm.vlm_analyze import doc_analyze as vlm_doc_analyze
from mineru.backend.pipeline.pipeline_analyze import doc_analyze as pipeline_doc_analyze
from mineru.backend.pipeline.pipeline_middle_json_mkcontent import union_make as pipeline_union_make
from mineru.backend.pipeline.model_json_to_middle_json import result_to_middle_json as pipeline_result_to_middle_json
from mineru.backend.vlm.vlm_middle_json_mkcontent import union_make as vlm_union_make
from mineru.utils.models_download_utils import auto_download_and_get_model_root_path


def do_parse(
    output_dir,  # 输出目录，用于存储解析结果
    pdf_file_names: list[str],  # 需要解析的PDF文件名列表
    pdf_bytes_list: list[bytes],  # 需要解析的PDF字节流列表
    p_lang_list: list[str],  # 每个PDF的语言列表，默认是'ch'（中文）
    backend="pipeline",  # 解析PDF所用的后端，默认是'pipeline'
    parse_method="auto",  # 解析PDF的方法，默认是'auto'
    p_formula_enable=True,  # 是否启用公式解析
    p_table_enable=True,  # 是否启用表格解析
    server_url=None,  # 用于vlm-sglang-client后端的服务器URL
    f_draw_layout_bbox=True,  # 是否绘制版面布局框
    f_draw_span_bbox=True,  # 是否绘制文本块框
    f_dump_md=True,  # 是否导出markdown文件
    f_dump_middle_json=True,  # 是否导出中间json文件
    f_dump_model_output=True,  # 是否导出模型输出文件
    f_dump_orig_pdf=True,  # 是否导出原始PDF文件
    f_dump_content_list=True,  # 是否导出内容列表文件
    f_make_md_mode=MakeMode.MM_MD,  # 生成markdown内容的模式，默认是MM_MD
    start_page_id=0,  # 解析起始页码，默认是0
    end_page_id=None,  # 解析结束页码，默认是None（解析到文档结尾）
):

    if backend == "pipeline":
        for idx, pdf_bytes in enumerate(pdf_bytes_list):
            new_pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, start_page_id, end_page_id)
            pdf_bytes_list[idx] = new_pdf_bytes

        infer_results, all_image_lists, all_pdf_docs, lang_list, ocr_enabled_list = pipeline_doc_analyze(pdf_bytes_list, p_lang_list, parse_method=parse_method, formula_enable=p_formula_enable,table_enable=p_table_enable)

        for idx, model_list in enumerate(infer_results):
            model_json = copy.deepcopy(model_list)
            pdf_file_name = pdf_file_names[idx]
            local_image_dir, local_md_dir = prepare_env(output_dir, pdf_file_name, parse_method)
            image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)

            images_list = all_image_lists[idx]
            pdf_doc = all_pdf_docs[idx]
            _lang = lang_list[idx]
            _ocr_enable = ocr_enabled_list[idx]
            middle_json = pipeline_result_to_middle_json(model_list, images_list, pdf_doc, image_writer, _lang, _ocr_enable, p_formula_enable)

            pdf_info = middle_json["pdf_info"]

            pdf_bytes = pdf_bytes_list[idx]
            if f_draw_layout_bbox:
                draw_layout_bbox(pdf_info, pdf_bytes, local_md_dir, f"{pdf_file_name}_layout.pdf")

            if f_draw_span_bbox:
                draw_span_bbox(pdf_info, pdf_bytes, local_md_dir, f"{pdf_file_name}_span.pdf")

            if f_dump_orig_pdf:
                md_writer.write(
                    f"{pdf_file_name}_origin.pdf",
                    pdf_bytes,
                )

            if f_dump_md:
                image_dir = str(os.path.basename(local_image_dir))
                md_content_str = pipeline_union_make(pdf_info, f_make_md_mode, image_dir)
                md_writer.write_string(
                    f"{pdf_file_name}.md",
                    md_content_str,
                )

            if f_dump_content_list:
                image_dir = str(os.path.basename(local_image_dir))
                content_list = pipeline_union_make(pdf_info, MakeMode.CONTENT_LIST, image_dir)
                md_writer.write_string(
                    f"{pdf_file_name}_content_list.json",
                    json.dumps(content_list, ensure_ascii=False, indent=4),
                )

            if f_dump_middle_json:
                md_writer.write_string(
                    f"{pdf_file_name}_middle.json",
                    json.dumps(middle_json, ensure_ascii=False, indent=4),
                )

            if f_dump_model_output:
                md_writer.write_string(
                    f"{pdf_file_name}_model.json",
                    json.dumps(model_json, ensure_ascii=False, indent=4),
                )

            logger.info(f"local output dir is {local_md_dir}")
    else:
        if backend.startswith("vlm-"):
            backend = backend[4:]

        f_draw_span_bbox = False
        parse_method = "vlm"
        for idx, pdf_bytes in enumerate(pdf_bytes_list):
            pdf_file_name = pdf_file_names[idx]
            pdf_bytes = convert_pdf_bytes_to_bytes_by_pypdfium2(pdf_bytes, start_page_id, end_page_id)
            local_image_dir, local_md_dir = prepare_env(output_dir, pdf_file_name, parse_method)
            image_writer, md_writer = FileBasedDataWriter(local_image_dir), FileBasedDataWriter(local_md_dir)
            middle_json, infer_result = vlm_doc_analyze(pdf_bytes, image_writer=image_writer, backend=backend, server_url=server_url)

            pdf_info = middle_json["pdf_info"]

            if f_draw_layout_bbox:
                draw_layout_bbox(pdf_info, pdf_bytes, local_md_dir, f"{pdf_file_name}_layout.pdf")

            if f_draw_span_bbox:
                draw_span_bbox(pdf_info, pdf_bytes, local_md_dir, f"{pdf_file_name}_span.pdf")

            if f_dump_orig_pdf:
                md_writer.write(
                    f"{pdf_file_name}_origin.pdf",
                    pdf_bytes,
                )

            if f_dump_md:
                image_dir = str(os.path.basename(local_image_dir))
                md_content_str = vlm_union_make(pdf_info, f_make_md_mode, image_dir)
                md_writer.write_string(
                    f"{pdf_file_name}.md",
                    md_content_str,
                )

            if f_dump_content_list:
                image_dir = str(os.path.basename(local_image_dir))
                content_list = vlm_union_make(pdf_info, MakeMode.CONTENT_LIST, image_dir)
                md_writer.write_string(
                    f"{pdf_file_name}_content_list.json",
                    json.dumps(content_list, ensure_ascii=False, indent=4),
                )

            if f_dump_middle_json:
                md_writer.write_string(
                    f"{pdf_file_name}_middle.json",
                    json.dumps(middle_json, ensure_ascii=False, indent=4),
                )

            if f_dump_model_output:
                model_output = ("\n" + "-" * 50 + "\n").join(infer_result)
                md_writer.write_string(
                    f"{pdf_file_name}_model_output.txt",
                    model_output,
                )

            logger.info(f"local output dir is {local_md_dir}")


def parse_doc(
        path_list: list[Path],
        output_dir,
        lang="ch",
        backend="pipeline",
        method="auto",
        server_url=None,
        start_page_id=0,  # 解析起始页码，默认是0
        end_page_id=None  # 解析结束页码，默认是None（解析到文档结尾）
):
    """
        参数说明：
        path_list: 需要解析的文档路径列表，可以是PDF或图片文件。
        output_dir: 解析结果输出目录。
        lang: 语言选项，默认'ch'，可选['ch', 'ch_server', 'ch_lite', 'en', 'korean', 'japan', 'chinese_cht', 'ta', 'te', 'ka']。
            如果已知PDF中的语言可填写此项以提升OCR准确率，选填。
            仅当backend为"pipeline"时生效。
        backend: 解析pdf所用后端：
            pipeline: 通用。
            vlm-transformers: 通用。
            vlm-sglang-engine: 更快（engine）。
            vlm-sglang-client: 更快（client）。
            未指定method时默认使用pipeline。
        method: 解析pdf的方法：
            auto: 根据文件类型自动判断。
            txt: 使用文本提取方法。
            ocr: 针对图片型PDF使用OCR方法。
            未指定时默认'auto'。仅当backend为"pipeline"时生效。
        server_url: 当backend为`sglang-client`时需指定server_url，例如：`http://127.0.0.1:30000`
    """
    try:
        file_name_list = []
        pdf_bytes_list = []
        lang_list = []
        for path in path_list:
            file_name = str(Path(path).stem)
            pdf_bytes = read_fn(path)
            file_name_list.append(file_name)
            pdf_bytes_list.append(pdf_bytes)
            lang_list.append(lang)
        do_parse(
            output_dir=output_dir,
            pdf_file_names=file_name_list,
            pdf_bytes_list=pdf_bytes_list,
            p_lang_list=lang_list,
            backend=backend,
            parse_method=method,
            server_url=server_url,
            start_page_id=start_page_id,
            end_page_id=end_page_id
        )
    except Exception as e:
        logger.exception(e)


def get_parsed_pdf_results(
        path_list: list[Path],
        output_dir,
        lang="ch",
        backend="pipeline",
        method="auto",
        server_url=None,
        start_page_id=0,
        end_page_id=None
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
        
    返回:
        包含字典的列表，每个字典包含文件路径和Markdown内容：
        [
            {
                'file_path': '文件路径',
                'md_path': 'Markdown文件路径',
                'md_content': 'Markdown内容'
            },
            ...
        ]
    """
    # 先执行解析
    parse_doc(
        path_list=path_list,
        output_dir=output_dir,
        lang=lang,
        backend=backend,
        method=method,
        server_url=server_url,
        start_page_id=start_page_id,
        end_page_id=end_page_id
    )
    
    # 收集结果
    results = []
    
    for path in path_list:
        pdf_file_name = str(Path(path).stem)
        file_path = str(path)
        
        # 根据backend判断输出目录
        if backend.startswith("vlm-"):
            local_md_dir = os.path.join(output_dir, pdf_file_name, "vlm")
        else:
            local_md_dir = os.path.join(output_dir, pdf_file_name, "auto")
            
        md_path = os.path.join(local_md_dir, f"{pdf_file_name}.md")
        
        # 读取Markdown内容
        md_content = ""
        if os.path.exists(md_path):
            with open(md_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
        
        results.append({
            'file_path': file_path,
            'md_path': md_path,
            'md_content': md_content
        })
    
    return results


if __name__ == '__main__':
    # 参数设置
    __dir__ = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(__dir__, "output")   # 输出结果文件夹路径
    
    # 文档路径列表
    doc_path_list = ["/home/xiaoke/projects/remote_pdf_parse_serve/assets/pdfs/simcse.pdf"]
    
    """如果您由于网络问题无法下载模型，可以设置环境变量MINERU_MODEL_SOURCE为modelscope，使用免代理仓库下载模型"""
    os.environ['MINERU_MODEL_SOURCE'] = "modelscope"

    # 使用新函数获取解析结果
    results = get_parsed_pdf_results(
        path_list=doc_path_list,
        output_dir=output_dir,
        backend="vlm-sglang-engine"  # 更快(engine)
    )
    
    # 打印结果
    for idx, result in enumerate(results):
        print(f"\n--- 文档 {idx+1} ---")
        print(f"原始文件路径: {result['file_path']}")
        print(f"Markdown文件路径: {result['md_path']}")
        print(f"Markdown内容前200字符: {result['md_content'][:200]}...")
    
    print(f"\n共解析了 {len(results)} 个文档")
