#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
独立的API客户端，用于与图片和PDF上传服务交互。
该客户端设计为可轻松复制并用于其他项目，仅依赖 'requests' 库。
"""
import requests
from pathlib import Path # 用于类型提示和调用者进行路径操作
import time
import json

class ApiClient:
    """
    用于与后端API交互的客户端，支持图片和PDF上传。
    """
    DEFAULT_TIMEOUT_IMAGE = 60  # 秒
    DEFAULT_TIMEOUT_PDF = 2400  # 秒 (PDF处理可能需要更长时间)
    DEFAULT_PROVIDER = 'zhipu'    # 默认AI提供商

    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        初始化ApiClient。

        Args:
            base_url (str): API的基础URL (例如 "http://localhost:8000")。
        """
        self.base_url = base_url.rstrip('/') # 确保没有末尾的斜杠

    def _get_content_type(self, file_path: Path) -> str:
        """根据文件扩展名获取Content-Type。"""
        suffix = file_path.suffix.lower()
        if suffix == '.png':
            return 'image/png'
        elif suffix in ['.jpg', '.jpeg']:
            return 'image/jpeg'
        elif suffix == '.pdf':
            return 'application/pdf'
        else:
            return 'application/octet-stream'  # 通用二进制类型

    def upload_single_image(self, image_path: Path, timeout: int = DEFAULT_TIMEOUT_IMAGE) -> dict | None:
        """
        上传单个图片到 /upload/image 接口。

        Args:
            image_path (Path): 要上传的图片的绝对路径。
            timeout (int): 请求超时时间（秒）。

        Returns:
            dict | None: 如果成功，返回API的JSON响应，否则返回None。
        """
        if not image_path.is_file(): # 检查是否为文件
            print(f"❌ 图片文件不存在或不是一个文件: {image_path}")
            return None

        content_type = self._get_content_type(image_path)
        try:
            with open(image_path, 'rb') as f:
                files = {'file': (image_path.name, f, content_type)}
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
                        print(f"   错误详情: {response.json()}")
                    except json.JSONDecodeError:
                        print(f"   响应内容: {response.text}")
                    return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败 (网络或服务器错误): {e}")
            return None
        except Exception as e:
            print(f"❌ 上传过程中发生意外错误: {e}")
            return None

    def upload_multiple_images(self, image_paths: list[Path], timeout: int = DEFAULT_TIMEOUT_IMAGE) -> dict | None:
        """
        上传多个图片到 /upload/images 接口。

        Args:
            image_paths (list[Path]): 要上传的图片绝对路径列表。
            timeout (int): 请求超时时间（秒）。

        Returns:
            dict | None: 如果成功，返回API的JSON响应，否则返回None。
        """
        if not image_paths:
            print("ℹ️ 没有提供图片进行上传。")
            return None

        opened_files = []
        files_to_send = []
        try:
            for img_path in image_paths:
                if not img_path.is_file(): # 检查是否为文件
                    print(f"⚠️ 图片文件不存在或不是一个文件，已跳过: {img_path}")
                    continue
                content_type = self._get_content_type(img_path)
                file_obj = open(img_path, 'rb')
                opened_files.append(file_obj)
                files_to_send.append(('files', (img_path.name, file_obj, content_type)))

            if not files_to_send:
                print("ℹ️ 没有有效的图片进行上传（可能所有提供的路径都有问题）。")
                return None

            upload_url = f"{self.base_url}/upload/images"
            print(f"📤 正在上传 {len(files_to_send)} 张图片到 {upload_url}")
            response = requests.post(upload_url, files=files_to_send, timeout=timeout)
            print(f"   📊 响应状态: {response.status_code}")
            if response.status_code == 200:
                print(f"✅ {len(files_to_send)} 张图片上传请求成功。")
                return response.json()
            else:
                print(f"❌ 多个图片上传失败: {response.status_code}")
                try:
                    print(f"   错误详情: {response.json()}")
                except json.JSONDecodeError:
                    print(f"   响应内容: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败 (网络或服务器错误): {e}")
            return None
        except Exception as e:
            print(f"❌ 上传过程中发生意外错误: {e}")
            return None
        finally:
            for file_obj in opened_files:
                file_obj.close()

    def upload_pdf(self, pdf_path: Path, provider: str = DEFAULT_PROVIDER,
                     process_images: bool = False, timeout: int = DEFAULT_TIMEOUT_PDF) -> dict | None:
        """
        上传PDF文件到 /upload/pdf 接口进行处理。

        Args:
            pdf_path (Path): 要上传的PDF文件的绝对路径。
            provider (str): 使用的AI提供商 (例如 'zhipu', 'mineru')。
            process_images (bool): 是否处理PDF中的图片。
            timeout (int): 请求超时时间（秒）。

        Returns:
            dict | None: 如果成功，返回API的JSON响应，否则返回None。
        """
        if not pdf_path.is_file(): # 检查是否为文件
            print(f"❌ PDF文件不存在或不是一个文件: {pdf_path}")
            return None

        print(f"📄 使用PDF文件: {pdf_path}")
        try:
            print(f"   📄 文件大小: {pdf_path.stat().st_size / 1024:.2f} KB")
        except Exception as e:
            print(f"   ⚠️无法获取文件大小: {e}")

        try:
            with open(pdf_path, 'rb') as f:
                files = {'file': (pdf_path.name, f, 'application/pdf')}
                params = {
                    'provider': provider,
                    'process_images': 'true' if process_images else 'false'
                }
                upload_url = f"{self.base_url}/upload/pdf"
                print(f"   📤 上传文件: {pdf_path.name} 到 {upload_url}")
                print(f"   🤖 AI提供商: {params['provider']}")
                print(f"   🖼️  处理图片: {params['process_images']}")

                start_time = time.time()
                response = requests.post(
                    upload_url,
                    files=files,
                    params=params,
                    timeout=timeout
                )
                end_time = time.time()

                print(f"   ⏱️  处理时间: {end_time - start_time:.2f} 秒")
                print(f"   📊 响应状态: {response.status_code}")

                if response.status_code == 200:
                    print(f"✅ PDF上传和解析成功 (Provider: {provider}, 处理图片: {process_images})!")
                    return response.json()
                else:
                    print(f"❌ PDF处理失败: {response.status_code}")
                    try:
                        print(f"   错误详情: {response.json()}")
                    except json.JSONDecodeError:
                        print(f"   响应内容: {response.text}")
                    return None
        except requests.exceptions.RequestException as e:
            print(f"❌ 请求失败 (网络或服务器错误): {e}")
            return None
        except Exception as e:
            print(f"❌ 上传过程中发生意外错误: {e}")
   