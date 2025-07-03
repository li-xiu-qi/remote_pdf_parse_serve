import json
import shutil
import os
import argparse

import requests
from modelscope import snapshot_download


def download_json(url):
    # 下载JSON文件
    response = requests.get(url)
    response.raise_for_status()  # 检查请求是否成功
    return response.json()


def download_and_modify_json(url, local_filename, modifications, force=False):
    if os.path.exists(local_filename) and not force:
        data = json.load(open(local_filename))
        config_version = data.get('config_version', '0.0.0')
        if config_version < '1.2.0':
            data = download_json(url)
    else:
        data = download_json(url)

    # 修改内容
    for key, value in modifications.items():
        data[key] = value

    # 保存修改后的内容
    with open(local_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


if __name__ == '__main__':
    # 命令行参数解析
    parser = argparse.ArgumentParser(description='下载MinerU模型并配置')
    parser.add_argument('--device', choices=['cpu', 'cuda'], default=None, 
                       help='选择设备模式: cpu 或 cuda (默认: 自动检测)')
    parser.add_argument('--force', action='store_true', 
                       help='强制重新下载配置文件，即使本地已存在')
    args = parser.parse_args()

    # 自动检测CUDA
    detected_device = 'cpu'
    if args.device is not None:
        detected_device = args.device
    else:
        try:
            import torch
            if torch.cuda.is_available():
                detected_device = 'cuda'
        except ImportError:
            pass

    print(f"🚀 开始下载MinerU模型...")
    print(f"⚙️  设备模式: {detected_device}")
    
    mineru_patterns = [
        # "models/Layout/LayoutLMv3/*",
        "models/Layout/YOLO/*",
        "models/MFD/YOLO/*",
        "models/MFR/unimernet_hf_small_2503/*",
        "models/OCR/paddleocr_torch/*",
        # "models/TabRec/TableMaster/*",
        # "models/TabRec/StructEqTable/*",
    ]
    model_dir = snapshot_download('opendatalab/PDF-Extract-Kit-1.0', allow_patterns=mineru_patterns)
    layoutreader_model_dir = snapshot_download('ppaanngggg/layoutreader')
    model_dir = model_dir + '/models'
    print(f'model_dir is: {model_dir}')
    print(f'layoutreader_model_dir is: {layoutreader_model_dir}')

    # paddleocr_model_dir = model_dir + '/OCR/paddleocr'
    # user_paddleocr_dir = os.path.expanduser('~/.paddleocr')
    # if os.path.exists(user_paddleocr_dir):
    #     shutil.rmtree(user_paddleocr_dir)
    # shutil.copytree(paddleocr_model_dir, user_paddleocr_dir)

    json_url = 'https://gcore.jsdelivr.net/gh/opendatalab/MinerU@master/magic-pdf.template.json'
    config_file_name = 'magic-pdf.json'
    home_dir = os.path.expanduser('~')
    config_file = os.path.join(home_dir, config_file_name)

    json_mods = {
        'models-dir': model_dir,
        'layoutreader-model-dir': layoutreader_model_dir,
        'device-mode': detected_device,
        'formula-config': {
            'mfd_model': 'yolo_v8_mfd',
            'mfr_model': 'unimernet_hf_small_2503',
            'enable': True
        }
    }

    download_and_modify_json(json_url, config_file, json_mods, args.force)
    print(f'✅ 配置文件已成功生成: {config_file}')
    print(f'🎯 设备模式已设置为: {detected_device}')
    if detected_device == 'cuda':
        print('⚠️  请确保您的系统已正确安装CUDA和对应的PyTorch版本')
        print('💡 可使用 nvidia-smi 检查GPU状态')
