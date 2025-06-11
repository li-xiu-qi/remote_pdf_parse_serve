"""
多模态模型对图像进行分析，生成标题和描述的异步工具类
"""
import os
import asyncio
import time
import json
import logging
from typing import Dict, Any, List, Union, Optional
from PIL import Image
from openai import AsyncOpenAI
from dotenv import load_dotenv

from web_serves.config import app_config
from web_serves.image_utils.prompts import get_image_analysis_prompt
from web_serves.image_utils.image_analysis_utils import extract_json_content, image_to_base64_async
load_dotenv()


class AsyncImageAnalysis:
    """
    异步图像文本提取器类，用于将图像内容转换为文本描述和标题。

    该类使用OpenAI的多模态模型异步分析图像内容，生成描述性文本和标题。
    支持多种API提供商：GUIJI、ZHIPU、VOLCES等
    """

    # 预定义的配置
    PROVIDER_CONFIGS = {
        "guiji": {
            "api_key_env": "GUIJI_API_KEY",
            "base_url_env": "GUIJI_BASE_URL", 
            "model_env": "GUIJI_VISION_MODEL",
            "default_models": [ "Pro/Qwen/Qwen2.5-VL-7B-Instruct", "Qwen/Qwen2.5-VL-32B-Instruct",]
        },
        "zhipu": {
            "api_key_env": "ZHIPU_API_KEY",
            "base_url_env": "ZHIPU_BASE_URL",
            "model_env": "ZHIPU_VISION_MODEL", 
            "default_models": ["glm-4v-flash", "glm-4v"]
        },
        "volces": {
            "api_key_env": "VOLCES_API_KEY",
            "base_url_env": "VOLCES_BASE_URL",
            "model_env": "VOLCES_VISION_MODEL",
            "default_models": ["doubao-1.5-vision-lite-250315", "doubao-1.5-vision-pro-250328"]
        },
        "openai": {
            "api_key_env": "OPENAI_API_KEY",
            "base_url_env": "OPENAI_API_BASE",
            "model_env": "OPENAI_VISION_MODEL",
            "default_models": ["gpt-4-vision-preview", "gpt-4o"]
        }
    }

    def __init__(
        self,
        provider: str = "zhipu",  # 默认使用智谱
        api_key: str = None,
        base_url: str = None,
        vision_model: str = None,
        prompt: Optional[str] = None,
        max_concurrent: int = 5,
    ):
        """
        初始化图像分析器
        
        Args:
            provider: API提供商，支持 'guiji', 'zhipu', 'volces', 'openai'
            api_key: API密钥，如果不提供则从环境变量读取
            base_url: API基础URL，如果不提供则从环境变量读取
            vision_model: 视觉模型名称，如果不提供则从环境变量或默认值读取
            prompt: 自定义提示词
            max_concurrent: 最大并发数
        """
        self.provider = provider.lower()
        
        if self.provider not in self.PROVIDER_CONFIGS:
            raise ValueError(f"不支持的提供商: {provider}. 支持的提供商: {list(self.PROVIDER_CONFIGS.keys())}")
        
        config = self.PROVIDER_CONFIGS[self.provider]
        
        # 获取API密钥
        self.api_key = api_key or os.getenv(config["api_key_env"])
        if not self.api_key:
            raise ValueError(f"API密钥未提供，请设置 {config['api_key_env']} 环境变量，或传入api_key参数。")

        # 获取基础URL
        self.base_url = base_url or os.getenv(config["base_url_env"])
        if not self.base_url:
            raise ValueError(f"基础URL未提供，请设置 {config['base_url_env']} 环境变量，或传入base_url参数。")
        
        # 获取视觉模型
        self.vision_model = (vision_model or 
                           os.getenv(config["model_env"]) or 
                           config["default_models"][0])
        
        print(f"使用提供商: {self.provider}")
        print(f"API基础URL: {self.base_url}")
        print(f"视觉模型: {self.vision_model}")
        
        self.client = AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

        # 设置提示词
        if prompt:
            self._prompt = prompt
        else:
            self._prompt = get_image_analysis_prompt(
                title_max_length=app_config.ai_services.title_max_length,
                description_max_length=app_config.ai_services.description_max_length
            )
        
        # 设置并发限制
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def analyze_image(
        self,
        image_url: str = None,
        local_image_path: str = None,
        model: str = None,
        detail: str = "low",
        prompt: str = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """
        异步分析图像并返回描述信息。

        Args:
            image_url: 在线图片URL
            local_image_path: 本地图片路径
            model: 使用的视觉模型，默认使用实例的默认模型
            detail: 图像细节级别，'low'或'high'
            prompt: 自定义提示词
            temperature: 模型温度参数

        Returns:
            包含title和description的字典
        """
        async with self.semaphore:  # 限制并发
            # 基本参数检查
            if not image_url and not local_image_path:
                raise ValueError("必须提供一个图像来源：image_url或local_image_path")
            if image_url and local_image_path:
                raise ValueError("只能提供一个图像来源：image_url或local_image_path")

            # 处理图像来源
            final_image_url = image_url
            image_format = "jpeg"  # 默认格式
            
            if local_image_path:
                # 简化图片格式处理
                try:
                    # 在异步环境中处理PIL操作
                    loop = asyncio.get_event_loop()
                    def get_image_format():
                        with Image.open(local_image_path) as img:
                            return img.format.lower() if img.format else "jpeg"
                    
                    image_format = await loop.run_in_executor(None, get_image_format)
                except Exception as e:
                    logging.warning(f"无法打开或识别图片格式 {local_image_path}: {e}, 使用默认jpeg")

                base64_image = await image_to_base64_async(local_image_path)
                final_image_url = f"data:image/{image_format};base64,{base64_image}"

            model_to_use = model or self.vision_model
            prompt_text = prompt or self._prompt

            try:
                response = await self.client.chat.completions.create(
                    model=model_to_use,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": final_image_url, "detail": detail},
                                },
                                {"type": "text", "text": prompt_text},
                            ],
                        }
                    ],
                    temperature=temperature,
                    max_tokens=300,
                )

                # 解析结果
                result_content = response.choices[0].message.content
                analysis_result = extract_json_content(result_content)
                
                return analysis_result

            except Exception as e:
                # 错误处理
                logging.error(f"API调用失败: {e}")
                return {"error": f"API调用失败: {str(e)}", "title": "", "description": ""}

    async def analyze_multiple_images(
        self,
        image_sources: List[Dict[str, Any]],
        model: str = None,
        detail: str = "low",
        prompt: str = None,
        temperature: float = 0.1,
    ) -> List[Dict[str, Any]]:
        """
        批量异步分析多张图像。

        Args:
            image_sources: 图像源列表，每个元素为包含image_url或local_image_path的字典
            model: 使用的视觉模型
            detail: 图像细节级别
            prompt: 自定义提示词
            temperature: 模型温度参数

        Returns:
            包含所有图像分析结果的列表
        """
        tasks = []
        for source in image_sources:
            task = self.analyze_image(
                image_url=source.get("image_url"),
                local_image_path=source.get("local_image_path"),
                model=model,
                detail=detail,
                prompt=prompt,
                temperature=temperature,
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    "error": f"处理第{i+1}张图像时出错: {str(result)}",
                    "title": "图片处理出错",
                    "description": "图片处理出错"
                })
                print(f"处理第{i+1}张图像时出错: {str(result)}")
            else:
                processed_results.append(result)
        
        return processed_results

    async def close(self):
        """
        关闭异步客户端连接
        """
        await self.client.close()

    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()


async def main():
    """示例使用方法"""
    async with AsyncImageAnalysis() as image_analyzer: # Removed provider, will use default
        local_image = "./image.png" # Assuming this exists in the context where main is run
        if not os.path.exists(local_image):
            print(f"Warning: Test image {local_image} not found, creating a dummy file for main example.")
            try:
                with open(local_image, "w") as f:
                    f.write("dummy content")
            except IOError as e:
                print(f"Could not create dummy file: {e}")
                # If dummy file can't be created, skip parts of main that need it.
                return


        # 单张图像分析
        print("分析单张图像...")
        start_time = time.time()
        result = await image_analyzer.analyze_image(
            local_image_path=local_image,
            # model="Qwen/Qwen2.5-VL-32B-Instruct", # Model can be specified or use default
            detail="low",
            # prompt=MULTIMODAL_PROMPT, # Removed, will use default prompt from app_config
            temperature=0.1,
        )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print(f"单张图像分析耗时: {time.time() - start_time:.2f}秒\\n")

        # 批量图像分析示例
        print("批量分析图像...")
        # Ensure dummy files exist if needed for batch example, or adjust example
        another_image_path = "./another_image.png"
        if not os.path.exists(another_image_path):
            print(f"Warning: Test image {another_image_path} not found, creating a dummy file for main example.")
            try:
                with open(another_image_path, "w") as f:
                    f.write("dummy content another")
            except IOError as e:
                print(f"Could not create dummy file: {e}")
        
        image_sources = [
            {"local_image_path": local_image},
            # {"image_url": "https://example.com/image1.jpg"}, # Example URL, might not be live
            # {"local_image_path": another_image_path}, # Use if exists
        ]
        if os.path.exists(another_image_path):
            image_sources.append({"local_image_path": another_image_path})


        start_time = time.time()
        batch_results = await image_analyzer.analyze_multiple_images(
            image_sources=image_sources, 
            # model="Qwen/Qwen2.5-VL-32B-Instruct", # Model can be specified or use default
            detail="low",
            temperature=0.1,
        )

        for i, res in enumerate(batch_results): # Changed result to res to avoid conflict
            print(f"图像 {i+1} 分析结果:")
            print(json.dumps(res, ensure_ascii=False, indent=2))

        print(f"批量分析耗时: {time.time() - start_time:.2f}秒")


if __name__ == "__main__":
    asyncio.run(main())
