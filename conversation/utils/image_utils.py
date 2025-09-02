import io
import base64
from typing import Optional
from PIL import Image
import requests
import os


def resolve_image_path(image_path: str) -> str:
    """解析图片路径，支持相对路径、绝对路径和URL"""
    # URL直接返回
    if image_path.startswith(('http://', 'https://')):
        return image_path
    
    # 绝对路径直接返回
    if os.path.isabs(image_path):
        return image_path
    
    # 如果路径以 ./ 或 ../ 开头，说明是相对当前目录的路径，直接返回
    if image_path.startswith(('./', '../')):
        return image_path

    # 如果是文件能够直接获取到，直接返回
    if os.path.exists(image_path):
        return image_path

    # 其他相对路径，基于IMAGE_BASE_DIR解析
    base_dir = os.getenv('IMAGE_BASE_DIR')
    if base_dir:
        return os.path.join(base_dir, image_path)
    else:
        return image_path

def load_image(image_path: str, return_type: str = "base64") -> Optional[object]:
    """
    加载本地图片或URL图片，返回 PIL.Image 或 base64 字符串。
    return_type: 
        "image" 返回 PIL.Image。
        "base64" 返回 base64 字符串。
        
    返回: 
        PIL.Image 或 base64 字符串，失败返回 None。
    """
    # HSC: resolve base64 input
    # 解析图片路径
    resolved_path = resolve_image_path(image_path)
    
    # 判断是否为URL
    if resolved_path.startswith("http://") or resolved_path.startswith("https://"):
        resp = requests.get(resolved_path, timeout=10)
        resp.raise_for_status()
        img_bytes = io.BytesIO(resp.content)
    else:
        if not os.path.exists(resolved_path):
            raise FileNotFoundError(f"文件不存在: {resolved_path}")
        with open(resolved_path, 'rb') as f:
            img_bytes = io.BytesIO(f.read())
    img = Image.open(img_bytes)
    fmt = img.format or "PNG"
    if return_type == "image":
        return {"image": img, "format": fmt}
    elif return_type == "base64":
        buffered = io.BytesIO()
        img.save(buffered, format=fmt)
        img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        return {"base64": img_b64, "format": fmt}
    else:
        raise ValueError(f"不支持的返回类型: {return_type}")