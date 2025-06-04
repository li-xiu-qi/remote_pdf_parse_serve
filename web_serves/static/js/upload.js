// API 基础 URL - 从后端配置获取
let API_BASE_URL = window.CONFIG ? window.CONFIG.API_BASE_URL : 'http://localhost:8000';

// 动态加载配置（备用方案）
async function loadConfig() {
    // 如果已经有配置，直接使用
    if (window.CONFIG) {
        console.log('使用服务器传递的配置:', window.CONFIG);
        return window.CONFIG;
    }
    
    // 否则尝试通过API获取
    try {
        const response = await fetch('/config');
        if (response.ok) {
            const config = await response.json();
            API_BASE_URL = config.api_base_url;
            console.log('配置加载成功:', config);
            return config;
        } else {
            console.warn('无法加载配置，使用默认配置');
            return null;
        }
    } catch (error) {
        console.warn('加载配置失败，使用默认配置:', error);
        return null;
    }
}

// 显示结果
function showResult(message, isError = false) {
    const resultDiv = document.getElementById('result');
    resultDiv.className = `result ${isError ? 'error' : 'success'}`;
    
    // 如果是Markdown内容，特殊处理
    if (message.includes('markdown_content')) {
        try {
            const parsed = JSON.parse(message);
            if (parsed.markdown_content) {
                resultDiv.innerHTML = `
                    <div class="file-info">
                        <strong>处理结果:</strong> ${parsed.message}<br>
                        <strong>文件名:</strong> ${parsed.file_info.original_filename}<br>
                        <strong>文件大小:</strong> ${(parsed.file_info.file_size / 1024 / 1024).toFixed(2)} MB<br>
                        <strong>提供商:</strong> ${parsed.file_info.provider}<br>
                        <strong>包含描述:</strong> ${parsed.file_info.include_descriptions ? '是' : '否'}
                    </div>
                    <div class="markdown-output">
                        <h4>生成的Markdown内容:</h4>
                        <pre>${parsed.markdown_content}</pre>
                    </div>
                `;
                return;
            }
        } catch (e) {
            // 如果解析失败，按普通文本处理
        }
    }
    
    resultDiv.textContent = message;
}

// 显示加载状态
function showLoading() {
    const resultDiv = document.getElementById('result');
    resultDiv.className = 'result loading';
    resultDiv.innerHTML = '<div style="text-align: center;">正在处理文件，请稍候...</div>';
}

// PDF上传处理
async function uploadPdf() {
    const fileInput = document.getElementById('pdfFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showResult('请选择一个PDF文件', true);
        return;
    }

    if (!file.name.toLowerCase().endsWith('.pdf')) {
        showResult('请选择PDF文件', true);
        return;
    }

    showLoading();    const formData = new FormData();
    formData.append('file', file);
    formData.append('provider', document.getElementById('provider').value);
    formData.append('include_descriptions', document.getElementById('includeDescriptions').checked);

    try {
        const response = await fetch(`${API_BASE_URL}/upload/pdf`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (response.ok) {
            showResult(JSON.stringify(result, null, 2));
        } else {
            showResult(`PDF处理失败：${result.detail || '未知错误'}`, true);
        }
    } catch (error) {
        showResult(`网络错误：${error.message}`, true);
    }
}

// 单文件上传
async function uploadSingle() {
    const fileInput = document.getElementById('singleFile');
    const file = fileInput.files[0];
    
    if (!file) {
        showResult('请选择一个文件', true);
        return;
    }

    showLoading();

    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/upload/image`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (response.ok) {
            showResult(`上传成功！\n\n${JSON.stringify(result, null, 2)}`);
        } else {
            showResult(`上传失败：${result.detail || '未知错误'}`, true);
        }
    } catch (error) {
        showResult(`网络错误：${error.message}`, true);
    }
}

// 多文件上传
async function uploadMultiple() {
    const fileInput = document.getElementById('multipleFiles');
    const files = fileInput.files;
    
    if (files.length === 0) {
        showResult('请选择至少一个文件', true);
        return;
    }

    showLoading();

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
        formData.append('files', files[i]);
    }

    try {
        const response = await fetch(`${API_BASE_URL}/upload/images`, {
            method: 'POST',
            body: formData
        });

        const result = await response.json();
        
        if (response.ok) {
            showResult(`批量上传完成！\n\n${JSON.stringify(result, null, 2)}`);
        } else {
            showResult(`上传失败：${result.detail || '未知错误'}`, true);
        }
    } catch (error) {
        showResult(`网络错误：${error.message}`, true);
    }
}

// 页面加载时初始化配置并检查 API 状态
window.addEventListener('load', async () => {
    // 先确保有配置
    if (window.CONFIG) {
        API_BASE_URL = window.CONFIG.API_BASE_URL;
        console.log('使用服务器配置，API地址:', API_BASE_URL);
    } else {
        // 如果没有配置，尝试加载
        await loadConfig();
    }
    
    // 然后检查 API 状态
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            console.log('API 服务正常运行');
        } else {
            console.warn('API 服务可能未启动');
        }
    } catch (error) {
        console.warn('无法连接到 API 服务，请确保服务已启动');
    }
});
