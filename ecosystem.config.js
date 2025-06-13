module.exports = {
  apps: [{
    // 应用基本信息
    name: 'pdf-parse-server',
    script: 'run_server.py',
    interpreter: '/home/xiaoke/miniconda3/envs/mineru/bin/python',
    args: '',
    cwd: '/home/xiaoke/projects/remote_pdf_parse_serve',
    
    // 进程管理
    instances: 1,                    // 单实例运行
    exec_mode: 'fork',              // 执行模式：fork 或 cluster
    
    // 自动重启配置
    autorestart: true,              // 自动重启
    watch: false,                   // 不监听文件变化（生产环境建议关闭）
    max_memory_restart: '48G',      // 内存超过48GB时重启
    min_uptime: '30s',              // 最小运行时间，避免无限重启
    max_restarts: 15,               // 最大重启次数
    restart_delay: 4000,            // 重启延迟时间（毫秒）
    
    // 优雅关闭配置
    kill_timeout: 10000,            // 强制杀死进程前的等待时间（毫秒）
    listen_timeout: 8000,           // 应用启动监听的超时时间
    
    // 环境变量配置
    env: {
      NODE_ENV: 'development',
      PYTHONPATH: '/home/xiaoke/projects/remote_pdf_parse_serve',
      PATH: '/home/xiaoke/miniconda3/envs/mineru/bin:' + process.env.PATH,
      CONDA_DEFAULT_ENV: 'mineru',
      PORT: '10001',
      HOST: '0.0.0.0',
      WORKERS: '4',
      LOG_LEVEL: 'INFO'
    },
    env_production: {
      NODE_ENV: 'production',
      PYTHONPATH: '/home/xiaoke/projects/remote_pdf_parse_serve',
      PATH: '/home/xiaoke/miniconda3/envs/mineru/bin:' + process.env.PATH,
      CONDA_DEFAULT_ENV: 'mineru',
      PORT: '10001',
      HOST: '0.0.0.0',
      WORKERS: '8',
      LOG_LEVEL: 'WARNING'
    },
    env_development: {
      NODE_ENV: 'development',
      PYTHONPATH: '/home/xiaoke/projects/remote_pdf_parse_serve',
      PATH: '/home/xiaoke/miniconda3/envs/mineru/bin:' + process.env.PATH,
      CONDA_DEFAULT_ENV: 'mineru',
      PORT: '10001',
      HOST: '127.0.0.1',
      WORKERS: '2',
      LOG_LEVEL: 'DEBUG'
    },
    
    // 日志配置
    out_file: './logs/out.log',           // 标准输出日志
    error_file: './logs/error.log',       // 错误日志
    log_file: './logs/combined.log',      // 合并日志
    time: true,                           // 日志时间戳
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',  // 时间格式
    merge_logs: true,                     // 合并日志
    log_type: 'json',                     // 日志格式：json 或 raw
    
    // 文件监听配置（开发模式可启用）
    ignore_watch: [
      'node_modules',
      'logs',
      'uploads',
      'temp',
      'assets',
      'docs',
      'tests',
      '*.log',
      '*.pid',
      '*.sock',
      '.git',
      '.vscode',
      '__pycache__',
      '*.pyc',
      '*.pyo'
    ],
    
    // 健康检查
    health_check_grace_period: 3000,      // 健康检查宽限期
    
    // 其他配置
    source_map_support: false,            // 是否启用source map支持
    instance_var: 'INSTANCE_ID',          // 实例变量名
    
    // 自定义启动脚本（可选）
    // pre_stop: './scripts/pre-stop.sh',   // 停止前执行的脚本
    // post_start: './scripts/post-start.sh', // 启动后执行的脚本
    
    // 集群模式配置（如果使用多实例）
    // increment_var: 'PORT',               // 端口递增变量
    // port: 10001,                         // 起始端口
    
    // 监控配置
    pmx: true,                            // 启用PM2监控
    
    // 高级配置
    vizion: true,                         // 启用版本控制元数据
    autorestart: true,                    // 应用崩溃时自动重启
    treekill: true,                       // 杀死整个进程树
    
    // 自定义信号处理
    // shutdown_with_message: false,        // 是否使用消息关闭
    // wait_ready: false,                   // 等待ready信号
    // listen_timeout: 8000,                // 监听超时
    // kill_retry_time: 100,                // 重试杀死进程的间隔
    
    // 错误处理
    // error_file: null,                    // 设置为null禁用错误日志
    // out_file: null,                      // 设置为null禁用输出日志
    
    // 性能配置
    // node_args: [],                       // Node.js参数（Python应用不需要）
    // max_old_logs: 10,                    // 保留的旧日志文件数量
    
    // 部署后钩子
    // post_update: ['npm install', 'echo "Application updated"']
  }],
  
  // 全局部署配置（可选）
  deploy: {
    production: {
      user: 'xiaoke',
      host: 'localhost',
      ref: 'origin/main',
      repo: 'git@github.com:your-username/remote_pdf_parse_serve.git',
      path: '/home/xiaoke/projects/remote_pdf_parse_serve',
      'pre-deploy-local': '',
      'post-deploy': 'pip install -r requirements.txt && pm2 reload ecosystem.config.js --env production',
      'pre-setup': ''
    }
  }
};
