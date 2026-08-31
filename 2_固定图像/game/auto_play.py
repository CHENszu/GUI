import pyautogui as pa
import time
from PIL import Image
import os
import ctypes
import sys
import signal
import keyboard

def force_exit(sig=None, frame=None):
    print("\n[停止运行] 已收到终止指令，脚本已强制终止！", flush=True)
    os._exit(0)

# 注册终端内的 Ctrl+C 信号处理函数
signal.signal(signal.SIGINT, force_exit)

# 注册全局的 Ctrl+C 热键，无论焦点在哪都能强制结束进程
# 注意：这需要管理员权限运行，或者在支持的终端下运行
keyboard.add_hotkey('ctrl+c', force_exit)

# 禁用 Windows DPI 缩放，使 pyautogui 获取真实的屏幕物理分辨率和坐标
try:
    ctypes.windll.user32.SetProcessDPIAware()
except Exception:
    pass

# 获取当前代码文件所在的目录
if getattr(sys, 'frozen', False):
    current_dir = sys._MEIPASS
else:
    current_dir = os.path.dirname(os.path.abspath(__file__))
# 拼接图片路径，这样无论在哪里运行脚本，都能准确找到同目录下的图片
image_path = os.path.join(current_dir, 'mole.png') # 如果你换成了 test.png，可以把这里改成 test.png

# 提前将图片读取到内存中
mole_img = Image.open(image_path)
# 【关键修复】游戏源码(main.py)中将图片强制缩放到了 100x100，所以这里也必须缩放到相同的像素大小！
# 否则 pyautogui 会用原图尺寸去屏幕上找，绝对找不到。
mole_img = mole_img.resize((100, 100))

print("自动打地鼠脚本已启动...", flush=True)
print("按 Ctrl+C 停止运行", flush=True)

try:
    while True:
        try:
            # 寻找屏幕上的地鼠图像（只匹配第一个，即“匹配一次”）
            target = pa.locateOnScreen(image=mole_img, confidence=0.85)
            
            if target is not None:
                # 获取地鼠的中心点并点击（点击一次）
                pa.click(pa.center(target))
                
                # 移动鼠标到旁边的空白处，防止鼠标停留在地鼠上遮挡下一次识别
                # 这里用 moveTo 代替 click，避免误点到其他窗口（如 IDE 或桌面图标）
                pa.moveTo(x=300, y=300)
                
                # 【关键修复】点击后等待一小段时间（如0.3秒）
                # 原因是：游戏里的地鼠被点击后，通常需要播放消失动画（零点几秒）。
                # 如果不加延时，循环太快（0.05秒），地鼠还没消失又会被识别到，导致“一直点一个位置”
                time.sleep(0.3)
        except pa.FailSafeException:
            # 【关键修复】遇到防失控机制（鼠标移到角落）时，直接抛出异常，跳出循环终止程序！
            raise
        except Exception as e:
            # 获取异常的名字和具体信息
            err_type = type(e).__name__
            err_msg = str(e)
            
            # 如果是找不到图片的异常（PyAutoGUI在新版中找不到图片会抛出 ImageNotFoundException，且信息往往为空）
            if 'Could not locate the image' in err_msg or err_type == 'ImageNotFoundException' or err_msg == '':
                pass
            else:
                import traceback
                print(f'发生错误 [{err_type}]: {err_msg}')
                traceback.print_exc()
        
        # 增加微小延时，防止CPU占用过高
        time.sleep(0.05)
except KeyboardInterrupt:
    print("\n[停止运行] 已收到 Ctrl+C，脚本已强制终止！", flush=True)
    os._exit(0)
except pa.FailSafeException:
    print("\n[停止运行] 已触发鼠标防失控机制（鼠标移至角落），脚本已强制终止！", flush=True)
    os._exit(0)
