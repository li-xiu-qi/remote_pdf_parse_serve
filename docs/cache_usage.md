# PDF解析缓存功能使用说明

## 功能介绍

为`mineru_parse.py`模块添加了基于`diskcache`的缓存功能，可以显著提高重复解析相同PDF文件的速度。

## 主要特性

1. **基于文件内容的缓存**：使用PDF文件前8KB内容生成缓存key，确保文件内容变化时缓存失效
2. **参数敏感**：缓存key包含解析参数（backend、method、lang等），不同参数组合使用不同缓存
3. **自动过期**：缓存默认7天过期，可以自定义过期时间
4. **完整文件恢复**：缓存包含markdown内容、图片文件和其他辅助文件
5. **向前兼容**：添加了`use_cache`参数，默认开启，不影响现有代码

## 使用方法

### 基本用法

```python
from web_serves.pdf_utils.mineru_parse import mineru_pdf2md

# 使用缓存（默认）
result = mineru_pdf2md(
    pdf_file_path="/path/to/your.pdf",
    md_output_path="/path/to/output",
    use_cache=True  # 默认值，可以省略
)

# 不使用缓存
result = mineru_pdf2md(
    pdf_file_path="/path/to/your.pdf", 
    md_output_path="/path/to/output",
    use_cache=False
)
```

### 批量处理

```python
from web_serves.pdf_utils.mineru_parse import mineru_multi_pdf2md

# 批量处理多个PDF文件，支持缓存
results = mineru_multi_pdf2md(
    pdf_file_paths=["/path/to/pdf1.pdf", "/path/to/pdf2.pdf"],
    md_output_path="/path/to/output",
    use_cache=True
)
```

### 缓存管理

```python
from web_serves.pdf_utils.mineru_parse import clear_pdf_cache, get_cache_stats

# 获取缓存统计信息
stats = get_cache_stats()
print(f"缓存大小: {stats['cache_size']}")
print(f"缓存目录: {stats['cache_directory']}")
print(f"磁盘使用: {stats['disk_usage']}")

# 清理缓存
success = clear_pdf_cache()
if success:
    print("缓存清理成功")
```

## 缓存存储位置

缓存文件默认存储在：`~/.cache/remote_pdf_parse_serve/`

## 缓存key生成规则

缓存key由以下部分组成：
- PDF文件前8KB内容的SHA256哈希值
- 解析参数（backend、method、lang、start_page_id、end_page_id）的MD5哈希值

格式：`pdf_parse_{文件哈希}_{参数哈希}`

## 缓存内容

每个缓存条目包含：
- `md_content`: Markdown内容
- `images`: 图片文件字典（文件名->二进制内容）
- `files`: 其他文件字典（如JSON配置文件等）

## 性能优化

1. **首次解析**：正常解析时间，同时将结果保存到缓存
2. **缓存命中**：直接从缓存读取，速度提升显著（通常50%以上）
3. **缓存未命中**：当文件内容或参数变化时，重新解析并更新缓存

## 注意事项

1. 缓存key基于文件前8KB内容，对于大文件的微小变化可能无法检测到
2. 缓存会占用磁盘空间，建议定期清理
3. 多进程环境下缓存是共享的，需要注意并发访问
4. 如果mineru库版本更新，建议清理缓存以避免兼容性问题

## 测试

运行测试脚本验证缓存功能：

```bash
python test_cache.py
```

测试会进行以下验证：
1. 清理旧缓存
2. 第一次解析（建立缓存）
3. 第二次解析（使用缓存）
4. 比较时间和结果
5. 测试不使用缓存的情况

## 故障排除

如果缓存功能异常：

1. 检查diskcache是否正确安装
2. 确认缓存目录权限
3. 清理缓存后重试
4. 检查磁盘空间是否充足

## 配置选项

可以通过修改`mineru_parse.py`中的以下变量来调整缓存行为：

- `CACHE_DIR`: 缓存目录路径
- `expire_time`: 缓存过期时间（秒）
