"""
异步图像分析功能测试脚本
使用环境变量中的API密钥测试图片分析功能
"""

import asyncio
import os
import sys
import json
import time
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from web_serves.image_utils.async_image_analysis import AsyncImageAnalysis


async def test_provider(provider_name: str, image_path: str):
    """测试特定提供商的图像分析功能"""
    print(f"\n{'='*50}")
    print(f"测试提供商: {provider_name.upper()}")
    print(f"{'='*50}")
    
    try:
        async with AsyncImageAnalysis(provider=provider_name) as analyzer:
            print(f"✅ {provider_name} 初始化成功")
            
            # 测试单张图像分析
            start_time = time.time()
            result = await analyzer.analyze_image(
                local_image_path=image_path,
                detail="low",
                temperature=0.1
            )
            end_time = time.time()
            
            print(f"⏱️  分析耗时: {end_time - start_time:.2f}秒")
            print(f"📊 分析结果:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
            # 检查结果是否有效
            if "error" in result:
                print(f"❌ {provider_name} 分析失败: {result['error']}")
                return False
            elif result.get("title") and result.get("description"):
                print(f"✅ {provider_name} 分析成功!")
                return True
            else:
                print(f"⚠️  {provider_name} 返回结果不完整")
                return False
                
    except Exception as e:
        print(f"❌ {provider_name} 测试失败: {str(e)}")
        return False


async def test_multiple_images(provider_name: str, image_paths: list):
    """测试批量图像分析功能"""
    print(f"\n{'='*50}")
    print(f"测试 {provider_name.upper()} 批量图像分析")
    print(f"{'='*50}")
    
    try:
        async with AsyncImageAnalysis(provider=provider_name) as analyzer:
            # 准备图像源列表
            image_sources = [{"local_image_path": path} for path in image_paths if os.path.exists(path)]
            
            if not image_sources:
                print("❌ 没有找到有效的图像文件")
                return False
            
            print(f"📊 准备分析 {len(image_sources)} 张图像...")
            
            start_time = time.time()
            results = await analyzer.analyze_multiple_images(
                image_sources=image_sources,
                detail="low",
                temperature=0.1
            )
            end_time = time.time()
            
            print(f"⏱️  批量分析耗时: {end_time - start_time:.2f}秒")
            print(f"📊 批量分析结果:")
            
            success_count = 0
            for i, result in enumerate(results):
                print(f"\n图像 {i+1} ({os.path.basename(image_sources[i]['local_image_path'])}):")
                print(json.dumps(result, ensure_ascii=False, indent=2))
                
                if "error" not in result and result.get("title") and result.get("description"):
                    success_count += 1
            
            print(f"\n✅ 成功分析: {success_count}/{len(results)} 张图像")
            return success_count == len(results)
            
    except Exception as e:
        print(f"❌ 批量测试失败: {str(e)}")
        return False


async def check_environment_variables():
    """检查环境变量配置"""
    print("🔍 检查环境变量配置...")
    
    providers_status = {}
    
    # 检查GUIJI配置
    guiji_key = os.getenv("GUIJI_API_KEY")
    guiji_url = os.getenv("GUIJI_BASE_URL")
    if guiji_key and guiji_url:
        providers_status["guiji"] = True
        print(f"✅ GUIJI配置完整 (API Key: {guiji_key[:20]}...)")
    else:
        providers_status["guiji"] = False
        print(f"❌ GUIJI配置缺失 (API Key: {bool(guiji_key)}, Base URL: {bool(guiji_url)})")
    
    # 检查ZHIPU配置
    zhipu_key = os.getenv("ZHIPU_API_KEY")
    zhipu_url = os.getenv("ZHIPU_BASE_URL")
    if zhipu_key and zhipu_url:
        providers_status["zhipu"] = True
        print(f"✅ ZHIPU配置完整 (API Key: {zhipu_key[:20]}...)")
    else:
        providers_status["zhipu"] = False
        print(f"❌ ZHIPU配置缺失 (API Key: {bool(zhipu_key)}, Base URL: {bool(zhipu_url)})")
    
    # 检查VOLCES配置
    volces_key = os.getenv("VOLCES_API_KEY")
    volces_url = os.getenv("VOLCES_BASE_URL")
    if volces_key and volces_url:
        providers_status["volces"] = True
        print(f"✅ VOLCES配置完整 (API Key: {volces_key[:20]}...)")
    else:
        providers_status["volces"] = False
        print(f"❌ VOLCES配置缺失 (API Key: {bool(volces_key)}, Base URL: {bool(volces_url)})")
    
    return providers_status


async def main():
    """主测试函数"""
    print("🚀 开始异步图像分析功能测试")
    print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 检查测试图像文件
    test_image = os.path.join(project_root, "assets", "images", "image.png")
    if not os.path.exists(test_image):
        print(f"❌ 测试图像文件不存在: {test_image}")
        return
    
    print(f"📸 使用测试图像: {test_image}")
    
    # 检查环境变量
    providers_status = await check_environment_variables()
    available_providers = [name for name, status in providers_status.items() if status]
    
    if not available_providers:
        print("❌ 没有可用的API提供商配置")
        return
    
    print(f"\n🔧 可用的提供商: {', '.join(available_providers)}")
    
    # 测试结果统计
    test_results = {}
    
    # 逐个测试每个可用的提供商
    for provider in available_providers:
        try:
            success = await test_provider(provider, test_image)
            test_results[provider] = success
        except Exception as e:
            print(f"❌ {provider} 测试异常: {str(e)}")
            test_results[provider] = False
    
    # 测试批量分析功能（使用第一个成功的提供商）
    successful_providers = [name for name, success in test_results.items() if success]
    if successful_providers:
        # 准备多个测试图像（如果存在）
        additional_images = [
            os.path.join(project_root, "assets", "images", "image1.png"),
            os.path.join(project_root, "assets", "images", "image2.png"),
        ]
        test_images = [test_image] + [img for img in additional_images if os.path.exists(img)]
        
        if len(test_images) > 1:
            await test_multiple_images(successful_providers[0], test_images)
    
    # 输出测试总结
    print(f"\n{'='*50}")
    print("📋 测试总结")
    print(f"{'='*50}")
    
    success_count = sum(test_results.values())
    total_count = len(test_results)
    
    for provider, success in test_results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"{provider.upper()}: {status}")
    
    print(f"\n🎯 总体结果: {success_count}/{total_count} 个提供商测试成功")
    
    if success_count > 0:
        print("🎉 图像分析功能基本可用!")
    else:
        print("😞 所有提供商测试都失败了，请检查配置和网络连接")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())