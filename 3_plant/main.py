import tkinter as tk
from tkinter import scrolledtext
import threading
import json
import os
import ctypes
from select_region import select_game_region
from qwen_agent import analyze_game_screen

# 修复 Windows 下的 DPI 缩放问题，防止坐标和窗口大小偏移
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("植物大战僵尸 AI 助手")
        self.root.geometry("450x400")
        
        # 居中显示窗口
        self.center_window(450, 400)
        
        # 标题
        lbl_title = tk.Label(root, text="植物大战僵尸 AI 助手", font=("Microsoft YaHei", 14, "bold"))
        lbl_title.pack(pady=10)
        
        # 按钮容器
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=5)

        # 选择窗口按钮
        self.btn_select = tk.Button(btn_frame, text="1. 选择窗口区域", font=("Microsoft YaHei", 10), 
                                    command=self.on_select_window, width=15, cursor="hand2")
        self.btn_select.grid(row=0, column=0, padx=10)
        
        # 开始游戏按钮
        self.btn_start = tk.Button(btn_frame, text="2. 开始游戏", font=("Microsoft YaHei", 10), 
                                  command=self.on_start_game, width=15, cursor="hand2")
        self.btn_start.grid(row=0, column=1, padx=10)
        
        # 状态标签
        self.status_var = tk.StringVar()
        self.status_var.set("状态: 待命")
        lbl_status = tk.Label(root, textvariable=self.status_var, font=("Microsoft YaHei", 9), fg="gray")
        lbl_status.pack(pady=5)

        # 坐标显示标签
        self.coord_var = tk.StringVar()
        self.coord_var.set("")
        lbl_coord = tk.Label(root, textvariable=self.coord_var, font=("Microsoft YaHei", 9), fg="blue")
        lbl_coord.pack(pady=0)
        
        # 切换遮罩框按钮
        self.btn_toggle = tk.Button(root, text="显示窗口", font=("Microsoft YaHei", 9), 
                                    command=self.toggle_overlay, width=12, cursor="hand2")
        self.btn_toggle.pack(pady=5)
        
        # 结果显示文本框
        self.txt_result = scrolledtext.ScrolledText(root, width=50, height=10, font=("Microsoft YaHei", 9))
        self.txt_result.pack(pady=10)

        # 保存遮罩窗口的引用
        self.overlay_window = None

        # 启动时加载保存的区域
        self.load_saved_region()

    def load_saved_region(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'region_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    region = json.load(f)
                coord_text = f"已加载上次坐标: ({region['top_left']['x']}, {region['top_left']['y']}) -> ({region['bottom_right']['x']}, {region['bottom_right']['y']})\n大小: {region['width']}x{region['height']}"
                self.coord_var.set(coord_text)
                self.update_status("已加载保存的区域，可直接开始游戏")
            except Exception as e:
                self.coord_var.set("加载保存的区域失败")
                self.update_status("状态: 待命")
        else:
            self.coord_var.set("当前未设置截图区域，请先选择")
            self.update_status("状态: 待命")

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.root.geometry(f'{width}x{height}+{int(x)}+{int(y)}')

    def update_status(self, msg):
        # 确保在主线程更新UI
        self.root.after(0, self.status_var.set, f"状态: {msg}")

    def toggle_overlay(self):
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.hide_overlay()
        else:
            self.show_overlay()

    def show_overlay(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'region_config.json')
        if not os.path.exists(config_path):
            self.update_status("未找到区域配置，无法显示")
            return

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                region = json.load(f)
            x = region['top_left']['x']
            y = region['top_left']['y']
            w = region['width']
            h = region['height']

            self.overlay_window = tk.Toplevel(self.root)
            self.overlay_window.overrideredirect(True)
            self.overlay_window.attributes("-topmost", True)
            self.overlay_window.geometry(f"{w}x{h}+{x}+{y}")

            # Windows 下的透明背景色
            transparent_color = "#abcdef"
            self.overlay_window.configure(bg=transparent_color)
            self.overlay_window.attributes("-transparentcolor", transparent_color)

            # 画一个红框
            canvas = tk.Canvas(self.overlay_window, bg=transparent_color, highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            canvas.create_rectangle(0, 0, w-1, h-1, outline="red", width=6)

            self.btn_toggle.config(text="关闭窗口")
        except Exception as e:
            self.update_status(f"显示区域失败: {str(e)}")

    def hide_overlay(self):
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.destroy()
            self.overlay_window = None
        self.btn_toggle.config(text="显示窗口")

    def on_select_window(self):
        self.hide_overlay()  # 选择时先隐藏原有的框
        self.btn_select.config(state=tk.DISABLED)
        self.update_status("正在等待点击(1/2): 请点击左上角")
        self.coord_var.set("")
        
        # 启动后台线程执行截图逻辑，防止阻塞UI主线程
        threading.Thread(target=self.run_select_region, daemon=True).start()

    def run_select_region(self):
        try:
            region = select_game_region(status_callback=self.update_status)
            if region:
                self.update_status("截图区域已成功保存")
                coord_text = f"坐标: ({region['top_left']['x']}, {region['top_left']['y']}) -> ({region['bottom_right']['x']}, {region['bottom_right']['y']})\n大小: {region['width']}x{region['height']}"
                self.root.after(0, self.coord_var.set, coord_text)
            else:
                self.update_status("选择已取消或失败")
        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
        finally:
            self.root.after(0, lambda: self.btn_select.config(state=tk.NORMAL))

    def on_start_game(self):
        self.btn_start.config(state=tk.DISABLED)
        self.txt_result.delete(1.0, tk.END)
        self.txt_result.insert(tk.END, "开始分析局势...\n")
        
        # 启动后台线程执行 API 请求
        threading.Thread(target=self.run_analyze_screen, daemon=True).start()

    def run_analyze_screen(self):
        try:
            result = analyze_game_screen(status_callback=self.update_status)
            self.root.after(0, self.append_result, f"\n【Qwen 分析结果】:\n{result}")
        except Exception as e:
            self.update_status("运行失败")
            self.root.after(0, self.append_result, f"\n【错误】: {str(e)}")
        finally:
            self.root.after(0, lambda: self.btn_start.config(state=tk.NORMAL))
            
    def append_result(self, text):
        self.txt_result.insert(tk.END, text)
        self.txt_result.see(tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
