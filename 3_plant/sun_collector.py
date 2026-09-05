import pyautogui as pa
import time
import os
import json
import threading
from PIL import Image

class SunCollector:
    def __init__(self, status_callback=None):
        self.running = False
        self.status_callback = status_callback
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'region_config.json')
        self.sun_img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sun.png')

    def start(self):
        if self.running: return
        self.running = True
        threading.Thread(target=self._collect_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _collect_loop(self):
        if not os.path.exists(self.config_path):
            if self.status_callback: self.status_callback("未找到区域配置，无法拾取阳光")
            self.running = False
            return
            
        if not os.path.exists(self.sun_img_path):
            if self.status_callback: self.status_callback("未找到阳光图片 (sun.png)")
            self.running = False
            return

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                region_data = json.load(f)
                
            x = region_data['top_left']['x']
            y = region_data['top_left']['y']
            w = region_data['width']
            h = region_data['height']
            search_region = (x, y, w, h)
            
            # 提前加载图片
            sun_img = Image.open(self.sun_img_path)
            
            # 因为窗口可以由用户自由拉伸，阳光的大小也会改变
            # 为了简单稳定，我们暂时使用原图（假定用户框选的窗口比例和截图时差不多）
            # 如果后续发现阳光大小变化太大识别不到，可以在这里根据 w 的宽度对 sun_img 进行 resize
            
        except Exception as e:
            if self.status_callback: self.status_callback(f"加载配置或图片失败: {e}")
            self.running = False
            return

        if self.status_callback: self.status_callback("已开启自动拾取阳光")

        # 临时降低 PyAutoGUI 的默认延迟，让鼠标瞬间移回，减少控制感
        old_pause = pa.PAUSE
        pa.PAUSE = 0.01

        while self.running:
            try:
                # 在指定区域内寻找所有阳光。置信度设置在 0.75 左右，容忍阳光的动画形变
                suns = pa.locateAllOnScreen(sun_img, region=search_region, confidence=0.75)
                
                # 【核心修复1】去重：OpenCV 会对同一个阳光返回几十个重叠的微小偏移识别框
                valid_targets = []
                for sun in suns:
                    cx, cy = pa.center(sun)
                    
                    # 【核心修复2】屏蔽左上角的阳光槽：假定它在截图区域的左上角 (宽120, 高80) 范围内
                    # 如果不屏蔽，程序会把 UI 上的阳光图标当成掉落的阳光，一直狂点
                    if cx < x + 120 and cy < y + 80:
                        continue
                        
                    # 检查是否与已有的目标太近（距离小于 40 像素认为是同一个阳光）
                    is_duplicate = False
                    for vx, vy in valid_targets:
                        if abs(cx - vx) < 40 and abs(cy - vy) < 40:
                            is_duplicate = True
                            break
                    
                    if not is_duplicate:
                        valid_targets.append((cx, cy))
                
                clicked_any = False
                for cx, cy in valid_targets:
                    if not self.running: break
                    
                    # 记录当前的鼠标位置
                    orig_x, orig_y = pa.position()
                    
                    # 点击阳光并瞬间移回原位
                    pa.click(cx, cy)
                    pa.moveTo(orig_x, orig_y)
                    
                    clicked_any = True
                    time.sleep(0.05) # 多个阳光之间稍微间隔
                    
                if clicked_any:
                    # 点完一批阳光后，等它们飞走，避免下一帧重复点同一批
                    time.sleep(0.5)
                else:
                    time.sleep(0.2)
                    
            except pa.ImageNotFoundException:
                # 找不到图片是正常现象
                time.sleep(0.2)
            except pa.FailSafeException:
                # 用户把鼠标移到屏幕角落，触发了安全机制，停止脚本
                if self.status_callback: self.status_callback("触发防失控机制，已停止拾取")
                self.running = False
                break
            except Exception as e:
                # 其他异常
                time.sleep(0.5)
                
        pa.PAUSE = old_pause
        if self.status_callback: self.status_callback("已停止自动拾取阳光")
