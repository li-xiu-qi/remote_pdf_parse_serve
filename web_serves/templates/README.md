# Web服务模板重构说明

## 概述
原来的 `test.html` 文件包含了大量重复的代码和样式，已经被重构为更模块化的结构。

## 新的文件结构

### 模板文件 (templates/)
```
templates/
├── base.html           # 基础模板，包含通用布局
├── index.html          # 主页，包含所有功能
├── image_upload.html   # 专用图片上传页面
└── pdf_upload.html     # 专用PDF处理页面
```

### 静态资源 (static/)
```
static/
├── css/
│   └── styles.css      # 统一的样式文件
└── js/
    └── upload.js       # 统一的JavaScript功能
```

## 访问地址

- **主页**: http://localhost:8000/ - 包含完整功能的页面
- **图片上传**: http://localhost:8000/image - 专门用于图片上传
- **PDF处理**: http://localhost:8000/pdf - 专门用于PDF文件处理
- **旧版本**: http://localhost:8000/test.html - 重定向页面，引导用户使用新页面

## 重构优势

1. **模块化**: 每个页面专注于特定功能
2. **可维护性**: CSS和JS分离，便于维护
3. **可扩展性**: 基于Jinja2模板系统，易于扩展
4. **代码复用**: 通过base模板避免代码重复
5. **更好的用户体验**: 页面加载更快，功能更专一

## 使用说明

1. 确保安装了所有依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 启动服务：
   ```bash
   python app.py
   ```

3. 访问对应的页面进行测试

## 模板系统

使用Jinja2模板引擎，支持：
- 模板继承 (`{% extends %}`)
- 块定义 (`{% block %}`)
- 变量插值 (`{{ variable }}`)
- 静态文件引用 (`{{ url_for('static', path='...') }}`)

## 注意事项

- 静态文件路径已更新为相对于 `/static/` 目录
- 所有JavaScript功能保持不变
- CSS样式统一管理，更容易主题定制
