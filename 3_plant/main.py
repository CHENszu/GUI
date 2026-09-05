import tkinter as tk
import customtkinter as ctk
import threading
import json
import os
import ctypes
import keyboard
from select_region import select_game_region
from qwen_agent import analyze_game_screen
from sun_collector import SunCollector

# 强制退出的全局热键处理函数
def force_exit():
    print("收到全局 Ctrl+C 热键，正在强制退出程序...")
    os._exit(0)

# 注册全局热键，任何时候按下 Ctrl+C 都会秒退
keyboard.add_hotkey('ctrl+c', force_exit)

# 修复 Windows 下的 DPI 缩放问题，防止坐标和窗口大小偏移
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# 设置现代主题和颜色
ctk.set_appearance_mode("System")  # 支持跟随系统 (Dark / Light)
ctk.set_default_color_theme("blue")  # 默认蓝色主题

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("🌻 植物大战僵尸 AI 助手")
        self.root.geometry("500x550")
        
        # 居中显示窗口
        self.center_window(500, 550)
        
        # 标题
        self.lbl_title = ctk.CTkLabel(root, text="植物大战僵尸 AI 助手", 
                                      font=ctk.CTkFont(family="Microsoft YaHei", size=22, weight="bold"))
        self.lbl_title.pack(pady=(25, 15))
        
        # 按钮容器
        self.btn_frame = ctk.CTkFrame(root, fg_color="transparent")
        self.btn_frame.pack(pady=5)

        # 选择窗口按钮
        self.btn_select = ctk.CTkButton(self.btn_frame, text="🎯 1. 选择窗口区域", 
                                        font=ctk.CTkFont(family="Microsoft YaHei", size=14),
                                        command=self.on_select_window, width=160, height=40)
        self.btn_select.grid(row=0, column=0, padx=15)
        
        # 开始游戏按钮
        self.btn_start = ctk.CTkButton(self.btn_frame, text="🚀 2. 开始游戏", 
                                       font=ctk.CTkFont(family="Microsoft YaHei", size=14),
                                       command=self.on_start_game, width=160, height=40)
        self.btn_start.grid(row=0, column=1, padx=15)
        
        # 自动拾取阳光按钮
        self.btn_sun = ctk.CTkButton(self.btn_frame, text="🌞 开启自动拾取", 
                                     font=ctk.CTkFont(family="Microsoft YaHei", size=14),
                                     command=self.toggle_sun_collector, width=350, height=40,
                                     fg_color="#e67e22", hover_color="#d35400")
        self.btn_sun.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        
        # 状态标签
        self.status_var = tk.StringVar(value="状态: 待命")
        self.lbl_status = ctk.CTkLabel(root, textvariable=self.status_var, 
                                       font=ctk.CTkFont(family="Microsoft YaHei", size=13), text_color="gray")
        self.lbl_status.pack(pady=(10, 0))

        # 坐标显示标签
        self.coord_var = tk.StringVar(value="")
        self.lbl_coord = ctk.CTkLabel(root, textvariable=self.coord_var, 
                                      font=ctk.CTkFont(family="Microsoft YaHei", size=13), text_color="#3b8ed0")
        self.lbl_coord.pack(pady=0)
        
        # 切换遮罩框按钮 (做成扁平化按钮效果)
        self.btn_toggle = ctk.CTkButton(root, text="👁 显示窗口", font=ctk.CTkFont(family="Microsoft YaHei", size=12),
                                        command=self.toggle_overlay, width=100, height=28, 
                                        fg_color="transparent", border_width=1, text_color=("gray10", "#DCE4EE"))
        self.btn_toggle.pack(pady=(5, 10))
        
        # 结果显示文本框
        self.txt_result = ctk.CTkTextbox(root, width=450, height=180, font=ctk.CTkFont(family="Microsoft YaHei", size=13))
        self.txt_result.pack(pady=10)

        # 保存遮罩窗口的引用
        self.overlay_window = None
        
        # 阳光拾取器实例
        self.sun_collector = SunCollector(status_callback=self.update_status)

        # 启动时加载保存的区域
        self.load_saved_region()

    def center_window(self, width, height):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = int((screen_width / 2) - (width / 2))
        y = int((screen_height / 2) - (height / 2))
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def update_status(self, msg):
        self.root.after(0, self.status_var.set, f"状态: {msg}")

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

    def toggle_overlay(self):
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.hide_overlay()
        else:
            self.show_overlay()

    def toggle_sun_collector(self):
        if self.sun_collector.running:
            self.sun_collector.stop()
            self.btn_sun.configure(text="🌞 开启自动拾取", fg_color="#e67e22", hover_color="#d35400")
        else:
            self.sun_collector.start()
            self.btn_sun.configure(text="⏸ 关闭自动拾取", fg_color="#7f8c8d", hover_color="#95a5a6")

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

            # 这里继续使用 tk.Toplevel，因为它更容易处理 Windows 下的镂空透明
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
            canvas.create_rectangle(0, 0, w-1, h-1, outline="#ff4757", width=6)

            self.btn_toggle.configure(text="🙈 关闭窗口")
        except Exception as e:
            self.update_status(f"显示区域失败: {str(e)}")

    def hide_overlay(self):
        if self.overlay_window and self.overlay_window.winfo_exists():
            self.overlay_window.destroy()
            self.overlay_window = None
        self.btn_toggle.configure(text="👁 显示窗口")

    def on_select_window(self):
        self.hide_overlay()  # 选择时先隐藏原有的框
        self.btn_select.configure(state="disabled")
        self.update_status("正在等待点击(1/2): 请点击左上角")
        self.coord_var.set("")
        
        # 启动后台线程执行截图逻辑
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
            self.root.after(0, lambda: self.btn_select.configure(state="normal"))

    def on_start_game(self):
        self.btn_start.configure(state="disabled")
        self.txt_result.delete("1.0", tk.END)
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
            self.root.after(0, lambda: self.btn_start.configure(state="normal"))
            
    def append_result(self, text):
        self.txt_result.insert(tk.END, text)
        self.txt_result.see(tk.END)

if __name__ == "__main__":
    root = ctk.CTk()
    app = App(root)
    root.mainloop()
