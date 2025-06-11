import re
from typing import Dict, Any, Match, Optional


def update_markdown_with_analysis(
    markdown_content: str,
    image_analysis_results: Dict[str, Dict[str, Any]],
) -> str:
    """
    更新Markdown内容，替换图片链接并添加描述
    
    该函数会扫描Markdown内容中的所有图片引用（格式为 ![alt](path)），
    根据提供的图片分析结果，将本地图片路径替换为远程URL，
    并可选择性地添加图片描述。
    
    Args:
        markdown_content (str): 原始Markdown内容
        image_analysis_results (Dict[str, Dict[str, Any]]): 图片分析结果字典
            键为图片的原始路径，值为包含以下字段的字典：
            - title (str): 图片标题
            - url (str): 图片的远程URL
            - description (str): 图片描述
    
    Returns:
        str: 更新后的Markdown内容
        
    Example:
        >>> results = {
        ...     "images/cat.jpg": {
        ...         "title": "可爱的猫咪",
        ...         "url": "https://example.com/cat.jpg",
        ...         "description": "一只橘色的猫正在睡觉"
        ...     }
        ... }
        >>> markdown = "![cat](images/cat.jpg)"
        >>> update_markdown_with_analysis(markdown, results, True)
        '![可爱的猫咪](https://example.com/cat.jpg)\\n> 一只橘色的猫正在睡觉'
    """
    print("开始更新Markdown内容...")
    print(f"原始Markdown内容长度: {len(markdown_content)}")
    print(f"图片分析结果数量: {len(image_analysis_results)}")
    # 打印下分析结果是否有问题：
    for key, value in image_analysis_results.items():
        print(f"分析结果 - 路径: {key}, 标题: {value.get('title', '无标题')}, URL: {value.get('url', '无URL')}")
        
    def replace_image(match: Match[str]) -> str:
        """
        替换单个图片引用的内部函数
        
        该函数处理正则表达式匹配到的每个图片引用，尝试在分析结果中
        找到对应的图片信息，并生成新的图片标记。
        
        Args:
            match (Match[str]): 正则表达式匹配对象，包含图片路径
            
        Returns:
            str: 替换后的图片标记，可能包含描述
        """
        # 提取原始路径，可能是 ./images/xxx.jpg 或 images/xxx.jpg
        original_path: str = match.group(1)
        
        # 标准化路径以便匹配
        # 将反斜杠统一为正斜杠，并去除开头的 "./"
        normalized_path: str = original_path.replace("\\", "/")
        if normalized_path.startswith("./"):
            normalized_path = normalized_path[2:]

        # 尝试多种匹配方式找到对应的分析结果
        result: Optional[Dict[str, Any]] = None
        
        for key in image_analysis_results:
            # 对每个键也进行相同的标准化处理
            key_normalized: str = key.replace("\\", "/")
            if key_normalized.startswith("./"):
                key_normalized = key_normalized[2:]
            
            # 多种匹配策略：
            # 1. 完全匹配原始路径
            # 2. 标准化后的路径匹配  
            # 3. 一个路径是另一个的后缀（处理绝对路径vs相对路径的情况）
            if (key == original_path or 
                key_normalized == normalized_path or
                key.endswith(normalized_path) or
                normalized_path.endswith(key_normalized)):
                result = image_analysis_results[key]
                break

        if result:
            # 从分析结果中提取信息，提供默认值
            title: str = result.get("title", "图片")
            url: str = result.get("url", "")
            description: str = result.get("description", "")

            # 构建新的图片标记，格式为 ![title](url)
            new_image: str = f"![{title}]({url})"

            # 如果启用描述且有描述内容，添加引用块（以 > 开头的行）
            new_image += f"\n> {description}"

            return new_image
        else:            # 如果没有找到对应的分析结果，保持原有的图片标记不变
            return match.group(0)

    # 使用正则表达式替换所有图片引用
    # 匹配模式：![任意字符](路径)
    image_pattern: str = r"!\[.*?\]\(([^)]+)\)"
    updated_content: str = re.sub(image_pattern, replace_image, markdown_content)
    
    # 返回更新后的Markdown内容
    return updated_content
