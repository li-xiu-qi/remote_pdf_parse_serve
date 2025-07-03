#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立的API客户端，用于与图片和PDF上传服务交互。
该客户端设计为可轻松复制并用于其他项目，仅依赖 'requests' 库。
"""
import requests
from pathlib import Path
import time
import json
from typing import Dict, List, Optional, Union


class ApiClient:
    """
    用于与后端API交互的客户端，支持图片和PDF上传。
    """

    DEFAULT_TIMEOUT_IMAGE = 60  # 秒
    DEFAULT_TIMEOUT_PDF = 2400  # 秒 (PDF处理可能需要更长时间)
    DEFAULT_PROVIDER = "zhipu"  # 默认AI提供商

    def __init__(self, base_url: str = "http://localhost:10001"):
        """
        初始化ApiClient。

        Args:
            base_url (str): API的基础URL (例如 "http://localhost:10001")。
        """
        self.base_url = base_url.rstrip("/")  # 确保没有末尾的斜杠

    def _get_content_type(self, file_path: Path) -> str:
        """根据文件扩展名获取Content-Type。"""
        suffix = file_path.suffix.lower()
        content_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".bmp": "image/bmp",
            ".webp": "image/webp",
            ".pdf": "application/pdf",
        }
        return content_type_map.get(suffix, "application/octet-stream")

    def upload_single_image(
        self, image_path: Path, timeout: int = DEFAULT_TIMEOUT_IMAGE
    ) -> Optional[Dict]:
        """
        上传单个图片到 /upload/image 接口。

        Args:
            image_path (Path): 要上传的图片的绝对路径。
            timeout (int): 请求超时时间（秒）。

        Returns:
            Optional[Dict]: 如果成功，返回API的JSON响应，否则返回None。
        """
        if not image_path.is_file():
            print(f"❌ 图片文件不存在或不是一个文件: {image_path}")
            return None

        content_type = self._get_content_type(image_path)
        try:
            with open(image_path, "rb") as f:
                files = {"file": (image_path.name, f, content_type)}
                upload_url = f"{self.base_url}/upload/image"
                print(f"📤 正在上传单个图片: {image_path.name} 到 {upload_url}")
                response = requests.post(upload_url, files=files, timeout=timeout)
                print(f"   📊 响应状态: {response.status_code}")

                if response.status_code == 200:
                    print(f"✅ 单个图片上传成功: {image_path.name}")
                    return response.json()
                else:
                    print(f"❌ 单个图片上传失败: {response.status_code}")
                    try:
                        error_detail = response.json()
                        print(f"   错误详情: {error_detail}")
                    except json.JSONDecodeError:
                        print(f"   响应内容: {response.text}")
                    return None

        except requests.exceptions.Timeout:
            print(f"❌ 请求超时 (超过 {timeout} 秒)")
            return None
        except requests.exceptions.ConnectionError:
            print(f"❌ 连接错误，请检查服务器是否运行: {self.base_url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            return None
        except Exception as e:
            print(f"❌ 上传过程中发生意外错误: {e}")
            return None

    def upload_multiple_images(
        self,
        image_paths: List[Path],
        provider: str = DEFAULT_PROVIDER,
        max_concurrent: int = 5,
        timeout: int = DEFAULT_TIMEOUT_IMAGE,
    ) -> Optional[Dict]:
        """
        上传多个图片到 /upload/images 接口。

        Args:
            image_paths (List[Path]): 要上传的图片绝对路径列表。
            provider (str): AI提供商 (guiji, zhipu, volces, openai)。
            max_concurrent (int): 最大并发处理数。
            timeout (int): 请求超时时间（秒）。

        Returns:
            Optional[Dict]: 如果成功，返回API的JSON响应，否则返回None。
        """
        if not image_paths:
            print("ℹ️ 没有提供图片进行上传。")
            return None

        opened_files = []
        files_to_send = []

        try:
            # 准备文件
            for img_path in image_paths:
                if not img_path.is_file():
                    print(f"⚠️ 图片文件不存在或不是一个文件，已跳过: {img_path}")
                    continue

                content_type = self._get_content_type(img_path)
                file_obj = open(img_path, "rb")
                opened_files.append(file_obj)
                files_to_send.append(("files", (img_path.name, file_obj, content_type)))

            if not files_to_send:
                print("ℹ️ 没有有效的图片进行上传（可能所有提供的路径都有问题）。")
                return None

            # 准备参数
            data = {"provider": provider, "max_concurrent": str(max_concurrent)}

            upload_url = f"{self.base_url}/upload/images"
            print(f"📤 正在上传 {len(files_to_send)} 张图片到 {upload_url}")
            print(f"   🤖 AI提供商: {provider}")
            print(f"   🔄 最大并发数: {max_concurrent}")

            response = requests.post(
                upload_url, files=files_to_send, data=data, timeout=timeout
            )
            print(f"   📊 响应状态: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                uploaded_count = len(result.get("uploaded_files", []))
                failed_count = len(result.get("failed_files", []))
                print(
                    f"✅ 批量图片上传完成: 成功 {uploaded_count} 张，失败 {failed_count} 张"
                )
                return result
            else:
                print(f"❌ 多个图片上传失败: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   错误详情: {error_detail}")
                except json.JSONDecodeError:
                    print(f"   响应内容: {response.text}")
                return None

        except requests.exceptions.Timeout:
            print(f"❌ 请求超时 (超过 {timeout} 秒)")
            return None
        except requests.exceptions.ConnectionError:
            print(f"❌ 连接错误，请检查服务器是否运行: {self.base_url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            return None
        except Exception as e:
            print(f"❌ 上传过程中发生意外错误: {e}")
            return None
        finally:
            # 确保所有文件都被关闭
            for file_obj in opened_files:
                try:
                    file_obj.close()
                except Exception:
                    pass

    def upload_pdf(
        self,
        pdf_path: Path,
        provider: str = DEFAULT_PROVIDER,
        backend: str = "pipeline",
        method: str = "auto",
        parse_images: bool = True,
        max_concurrent: int = 5,
        timeout: int = DEFAULT_TIMEOUT_PDF,
    ) -> Optional[Dict]:
        """
        上传PDF文件到 /upload/pdf 接口进行处理。

        Args:
            pdf_path (Path): 要上传的PDF文件的绝对路径。
            provider (str): 使用的AI提供商 (guiji, zhipu, volces, openai)。
            backend (str): PDF解析后端 (pipeline, vlm-transformers, vlm-sglang-engine, vlm-sglang-client)。
            method (str): PDF解析方法 (auto, txt, ocr)。
            parse_images (bool): 是否处理PDF中的图片。
            max_concurrent (int): AI并发处理数。
            timeout (int): 请求超时时间（秒）。

        Returns:
            Optional[Dict]: 如果成功，返回API的JSON响应，否则返回None。
        """
        if not pdf_path.is_file():
            print(f"❌ PDF文件不存在或不是一个文件: {pdf_path}")
            return None

        print(f"📄 使用PDF文件: {pdf_path}")
        try:
            file_size = pdf_path.stat().st_size
            print(f"   📄 文件大小: {file_size / 1024:.2f} KB")
        except Exception as e:
            print(f"   ⚠️ 无法获取文件大小: {e}")

        try:
            with open(pdf_path, "rb") as f:
                files = {"file": (pdf_path.name, f, "application/pdf")}
                data = {
                    "provider": provider,
                    "backend": backend,
                    "method": method,
                    "parse_images": parse_images,
                    "max_concurrent": max_concurrent,
                }

                upload_url = f"{self.base_url}/upload/pdf"
                print(f"   📤 上传文件: {pdf_path.name} 到 {upload_url}")
                print(f"   🤖 AI提供商: {provider}")
                print(f"   🔧 解析后端: {backend}")
                print(f"   🔍 解析方法: {method}")
                print(f"   🖼️ 处理图片: {parse_images}")
                print(f"   🔄 最大并发数: {max_concurrent}")

                start_time = time.time()
                response = requests.post(
                    upload_url, files=files, data=data, timeout=timeout
                )
                end_time = time.time()

                print(f"   ⏱️ 处理时间: {end_time - start_time:.2f} 秒")
                print(f"   📊 响应状态: {response.status_code}")

                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ PDF上传和解析成功!")
                    return result
                else:
                    print(f"❌ PDF处理失败: {response.status_code}")
                    try:
                        error_detail = response.json()
                        print(f"   错误详情: {error_detail}")
                    except json.JSONDecodeError:
                        print(f"   响应内容: {response.text}")
                    return None

        except requests.exceptions.Timeout:
            print(f"❌ 请求超时 (超过 {timeout} 秒)")
            return None
        except requests.exceptions.ConnectionError:
            print(f"❌ 连接错误，请检查服务器是否运行: {self.base_url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            return None
        except Exception as e:
            print(f"❌ 上传过程中发生意外错误: {e}")
            return None

    def upload_multiple_pdfs(
        self,
        pdf_paths: List[Path],
        provider: str = DEFAULT_PROVIDER,
        backend: str = "pipeline",
        method: str = "auto",
        parse_images: bool = True,
        max_concurrent: int = 5,
        timeout: int = DEFAULT_TIMEOUT_PDF,
    ) -> Optional[Dict]:
        """
        批量上传PDF文件到 /upload/pdfs 接口进行处理。

        Args:
            pdf_paths (List[Path]): 要上传的PDF文件绝对路径列表。
            provider (str): 使用的AI提供商 (guiji, zhipu, volces, openai)。
            backend (str): PDF解析后端 (pipeline, vlm-transformers, vlm-sglang-engine, vlm-sglang-client)。
            method (str): PDF解析方法 (auto, txt, ocr)。
            parse_images (bool): 是否处理PDF中的图片。
            max_concurrent (int): AI并发处理数。
            timeout (int): 请求超时时间（秒）。

        Returns:
            Optional[Dict]: 如果成功，返回API的JSON响应，否则返回None。
        """
        if not pdf_paths:
            print("ℹ️ 没有提供PDF文件进行上传。")
            return None

        opened_files = []
        files_to_send = []

        try:
            # 准备文件
            for pdf_path in pdf_paths:
                if not pdf_path.is_file():
                    print(f"⚠️ PDF文件不存在或不是一个文件，已跳过: {pdf_path}")
                    continue

                content_type = self._get_content_type(pdf_path)
                file_obj = open(pdf_path, "rb")
                opened_files.append(file_obj)
                files_to_send.append(
                    ("files", (pdf_path.name, file_obj, "application/pdf"))
                )

            if not files_to_send:
                print("ℹ️ 没有有效的PDF进行上传（可能所有提供的路径都有问题）。")
                return None

            # 准备参数
            data = {
                "provider": provider,
                "backend": backend,
                "method": method,
                "parse_images": parse_images,
                "max_concurrent": max_concurrent,
            }

            upload_url = f"{self.base_url}/upload/pdfs"
            print(f"📤 正在上传 {len(files_to_send)} 个PDF到 {upload_url}")
            print(f"   🤖 AI提供商: {provider}")
            print(f"   🔧 解析后端: {backend}")
            print(f"   🔍 解析方法: {method}")
            print(f"   🖼️ 处理图片: {parse_images}")
            print(f"   🔄 最大并发数: {max_concurrent}")

            start_time = time.time()
            response = requests.post(
                upload_url, files=files_to_send, data=data, timeout=timeout
            )
            end_time = time.time()

            print(f"   ⏱️ 处理时间: {end_time - start_time:.2f} 秒")
            print(f"   📊 响应状态: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print("✅ 批量PDF上传和解析完成!")
                return result
            else:
                print(f"❌ 批量PDF处理失败: {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   错误详情: {error_detail}")
                except json.JSONDecodeError:
                    print(f"   响应内容: {response.text}")
                return None

        except requests.exceptions.Timeout:
            print(f"❌ 请求超时 (超过 {timeout} 秒)")
            return None
        except requests.exceptions.ConnectionError:
            print(f"❌ 连接错误，请检查服务器是否运行: {self.base_url}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败: {e}")
            return None
        except Exception as e:
            print(f"❌ 上传过程中发生意外错误: {e}")
            return None
        finally:
            # 确保所有文件都被关闭
            for file_obj in opened_files:
                try:
                    file_obj.close()
                except Exception:
                    pass

    def health_check(self) -> bool:
        """
        检查API服务器健康状态。

        Returns:
            bool: 如果服务器正常运行返回True，否则返回False。
        """
        try:
            response = requests.get(f"{self.base_url}/", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 健康检查失败: {e}")
            return False
