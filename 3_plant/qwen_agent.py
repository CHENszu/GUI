import os
import json
import base64
from io import BytesIO
from PIL import ImageGrab
from dotenv import load_dotenv
from openai import OpenAI

# 加载 .env 文件
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

def encode_image(image):
    buffered = BytesIO()
    # 保存为 JPEG 格式，可以调整 quality 压缩大小
    image.save(buffered, format="JPEG", quality=80)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def analyze_game_screen(status_callback=None):
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'region_config.json')
    if not os.path.exists(config_path):
        raise FileNotFoundError("未找到截图区域配置。请先使用“选择窗口”功能确定截图区域。")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        region = json.load(f)
    
    x1 = region['top_left']['x']
    y1 = region['top_left']['y']
    x2 = region['bottom_right']['x']
    y2 = region['bottom_right']['y']
    bbox = (x1, y1, x2, y2)
    
    if status_callback:
        status_callback("正在截取游戏画面...")
    
    # 截取指定区域的屏幕
    img = ImageGrab.grab(bbox)
    
    if status_callback:
        status_callback("正在将截图发送给 Qwen 大模型...")
        
    base64_image = encode_image(img)
    
    api_key = os.environ.get("api_key")
    if not api_key:
        raise ValueError("未在 .env 文件中找到 api_key，请确保 .env 格式为 api_key = sk-xxx")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    
    try:
        response = client.chat.completions.create(
            model="qwen-vl-max",  # 使用最新的 Qwen-VL-Max 模型
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "你是一个玩植物大战僵尸的AI。请分析这张游戏截图，告诉我你看到了什么植物和僵尸，以及当前的局势。"},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ]
        )
        result_text = response.choices[0].message.content
        if status_callback:
            status_callback("模型回复已完成")
        return result_text
    except Exception as e:
        raise Exception(f"调用大模型失败: {str(e)}")

if __name__ == "__main__":
    print(analyze_game_screen())