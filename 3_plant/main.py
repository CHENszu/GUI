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
        self.root.geometry("500x650")
        
        # 居中显示窗口
        self.center_window(500, 650)
        
        # 标题
        self.lbl_title = ctk.CTkLabel(root, text="植物大战僵尸 AI 助手", 
                                      font=ctk.CTkFont(family="Microsoft YaHei", size=22, weight="bold"))
        self.lbl_title.pack(pady=(25, 15))
        
        # 按钮容器
        self.btn_frame = ctk.CTkFrame(root, fg_color="transparent")
        self.btn_frame.pack(pady=5)

        # 选择窗口按钮
        self.btn_select = ctk.CTkButton(self.btn_frame, text="🎯 1. 标定游戏主窗口", 
                                        font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                                        command=self.on_select_window, width=160, height=35)
        self.btn_select.grid(row=0, column=0, padx=10, pady=5)
        
        # 标定植物栏按钮
        self.btn_plants = ctk.CTkButton(self.btn_frame, text="🌱 2. 标定植物栏", 
                                        font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                                        command=self.on_select_plants, width=160, height=35, fg_color="#27ae60", hover_color="#2ecc71")
        self.btn_plants.grid(row=0, column=1, padx=10, pady=5)
        
        # 标定草地按钮
        self.btn_lawn = ctk.CTkButton(self.btn_frame, text="🟩 3. 标定草地网格", 
                                      font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                                      command=self.on_select_lawn, width=160, height=35, fg_color="#8e44ad", hover_color="#9b59b6")
        self.btn_lawn.grid(row=1, column=0, padx=10, pady=5)
        
        # 开始游戏按钮
        self.btn_start = ctk.CTkButton(self.btn_frame, text="🚀 4. 开始游戏", 
                                       font=ctk.CTkFont(family="Microsoft YaHei", size=13),
                                       command=self.on_start_game, width=160, height=35)
        self.btn_start.grid(row=1, column=1, padx=10, pady=5)
        
        # 自动拾取阳光按钮
        self.btn_sun = ctk.CTkButton(self.btn_frame, text="🌞 开启自动拾取", 
                                     font=ctk.CTkFont(family="Microsoft YaHei", size=14),
                                     command=self.toggle_sun_collector, width=340, height=40,
                                     fg_color="#e67e22", hover_color="#d35400")
        self.btn_sun.grid(row=2, column=0, columnspan=2, pady=(15, 0))
        
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
        grid_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grid_config.json')
        
        status_parts = []
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    region = json.load(f)
                coord_text = f"主窗口: ({region['top_left']['x']}, {region['top_left']['y']}) -> ({region['bottom_right']['x']}, {region['bottom_right']['y']}) [{region['width']}x{region['height']}]"
                status_parts.append("已加载主窗口")
            except Exception as e:
                coord_text = "加载主窗口失败"
        else:
            coord_text = "当前未设置主窗口"
            
        if os.path.exists(grid_path):
            try:
                with open(grid_path, 'r', encoding='utf-8') as f:
                    grids = json.load(f)
                if "plants" in grids:
                    coord_text += f"\n植物栏: {grids['plants']['count']} 个格子"
                    status_parts.append("植物栏")
                if "lawn" in grids:
                    coord_text += f"\n草地: {grids['lawn']['rows']}x{grids['lawn']['cols']} 网格"
                    status_parts.append("草地")
            except Exception:
                pass
                
        self.coord_var.set(coord_text)
        if status_parts:
            self.update_status(f"状态: 已加载 {', '.join(status_parts)}")
        else:
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
        grid_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grid_config.json')
        
        if not os.path.exists(config_path):
            self.update_status("未找到主窗口配置，无法显示")
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
            
            # 为了能画出可能超出主窗口的网格，我们将画布设为全屏
            screen_width = self.root.winfo_screenwidth()
            screen_height = self.root.winfo_screenheight()
            self.overlay_window.geometry(f"{screen_width}x{screen_height}+0+0")

            # Windows 下的透明背景色
            transparent_color = "#abcdef"
            self.overlay_window.configure(bg=transparent_color)
            self.overlay_window.attributes("-transparentcolor", transparent_color)

            canvas = tk.Canvas(self.overlay_window, bg=transparent_color, highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            
            # 画主窗口红框
            canvas.create_rectangle(x, y, x+w-1, y+h-1, outline="#ff4757", width=4)
            canvas.create_text(x + 5, y + 5, text="主窗口", fill="#ff4757", font=("Arial", 12, "bold"), anchor="nw")

            # 如果有植物栏或草地配置，也画出来
            if os.path.exists(grid_path):
                with open(grid_path, 'r', encoding='utf-8') as f:
                    grids = json.load(f)
                
                # 画植物栏
                if "plants" in grids:
                    pr = grids["plants"]["region"]
                    px, py, pw, ph = pr["top_left"]["x"], pr["top_left"]["y"], pr["width"], pr["height"]
                    count = grids["plants"]["count"]
                    
                    canvas.create_rectangle(px, py, px+pw-1, py+ph-1, outline="#2ecc71", width=3)
                    cell_w = pw / count
                    for i in range(count):
                        cell_x = px + i * cell_w
                        # 画分隔线
                        if i > 0:
                            canvas.create_line(cell_x, py, cell_x, py+ph, fill="#2ecc71", width=2)
                        # 画中心点和编号
                        cx = cell_x + cell_w / 2
                        cy = py + ph / 2
                        canvas.create_oval(cx-3, cy-3, cx+3, cy+3, fill="#2ecc71")
                        canvas.create_text(cx, cy - 15, text=str(i+1), fill="#2ecc71", font=("Arial", 14, "bold"))

                # 画草地网格
                if "lawn" in grids:
                    lr = grids["lawn"]["region"]
                    lx, ly, lw, lh = lr["top_left"]["x"], lr["top_left"]["y"], lr["width"], lr["height"]
                    rows = grids["lawn"]["rows"]
                    cols = grids["lawn"]["cols"]
                    
                    canvas.create_rectangle(lx, ly, lx+lw-1, ly+lh-1, outline="#9b59b6", width=3)
                    cell_w = lw / cols
                    cell_h = lh / rows
                    
                    # 画网格线
                    for r in range(1, rows):
                        canvas.create_line(lx, ly + r * cell_h, lx + lw, ly + r * cell_h, fill="#9b59b6", width=1, dash=(4, 4))
                    for c in range(1, cols):
                        canvas.create_line(lx + c * cell_w, ly, lx + c * cell_w, ly + lh, fill="#9b59b6", width=1, dash=(4, 4))
                        
                    # 画中心点和编号 (例如 Row1-Col1 可以用 A1 形式，或者简单的行列数字)
                    for r in range(rows):
                        for c in range(cols):
                            cx = lx + c * cell_w + cell_w / 2
                            cy = ly + r * cell_h + cell_h / 2
                            canvas.create_oval(cx-2, cy-2, cx+2, cy+2, fill="#9b59b6")
                            # 用大写字母代表行(A,B,C...)，数字代表列(1,2,3...)
                            row_char = chr(ord('A') + r)
                            canvas.create_text(cx, cy, text=f"{row_char}{c+1}", fill="#9b59b6", font=("Arial", 12, "bold"))

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
        
        # 启动后台线程执行截图逻辑
        threading.Thread(target=self.run_select_region, daemon=True).start()

    def run_select_region(self):
        try:
            region = select_game_region(status_callback=self.update_status, msg_prefix="主窗口")
            if region:
                self.update_status("主窗口区域已成功保存")
                self.root.after(0, self.load_saved_region)
            else:
                self.update_status("选择已取消或失败")
        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
        finally:
            self.root.after(0, lambda: self.btn_select.configure(state="normal"))

    def on_select_plants(self):
        self.hide_overlay()
        
        dialog = ctk.CTkInputDialog(text="请输入植物栏中可用的植物槽位数量:", title="标定植物栏")
        # CustomTkinter 的 CTkInputDialog 没有直接支持默认值的参数，但我们可以通过这种方式 hack 进去
        dialog.after(100, lambda: dialog._entry.insert(0, "10"))
        
        count_str = dialog.get_input()
        if not count_str or not count_str.isdigit():
            self.update_status("输入无效，已取消标定植物栏")
            return
            
        count = int(count_str)
        self.btn_plants.configure(state="disabled")
        self.update_status("正在等待点击(1/2): 请点击植物栏左上角")
        
        threading.Thread(target=self.run_select_plants, args=(count,), daemon=True).start()
        
    def run_select_plants(self, count):
        try:
            region = select_game_region(status_callback=self.update_status, save_to_file=False, msg_prefix="植物栏")
            if region:
                grid_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grid_config.json')
                grids = {}
                if os.path.exists(grid_path):
                    with open(grid_path, 'r', encoding='utf-8') as f:
                        grids = json.load(f)
                
                grids["plants"] = {
                    "region": region,
                    "count": count
                }
                with open(grid_path, 'w', encoding='utf-8') as f:
                    json.dump(grids, f, ensure_ascii=False, indent=4)
                    
                self.update_status("植物栏区域已成功保存")
                self.root.after(0, self.load_saved_region)
            else:
                self.update_status("选择已取消或失败")
        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
        finally:
            self.root.after(0, lambda: self.btn_plants.configure(state="normal"))

    def on_select_lawn(self):
        self.hide_overlay()
        
        dialog = ctk.CTkInputDialog(text="请输入草地网格的 行数,列数:", title="标定草地")
        dialog.after(100, lambda: dialog._entry.insert(0, "5,9"))
        
        grid_str = dialog.get_input()
        if not grid_str or ',' not in grid_str:
            self.update_status("输入无效，已取消标定草地")
            return
            
        try:
            r, c = map(int, grid_str.split(','))
        except:
            self.update_status("输入格式错误，已取消")
            return
            
        self.btn_lawn.configure(state="disabled")
        self.update_status("正在等待点击(1/2): 请点击草地左上角")
        
        threading.Thread(target=self.run_select_lawn, args=(r, c), daemon=True).start()
        
    def run_select_lawn(self, rows, cols):
        try:
            region = select_game_region(status_callback=self.update_status, save_to_file=False, msg_prefix="草地")
            if region:
                grid_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'grid_config.json')
                grids = {}
                if os.path.exists(grid_path):
                    with open(grid_path, 'r', encoding='utf-8') as f:
                        grids = json.load(f)
                
                grids["lawn"] = {
                    "region": region,
                    "rows": rows,
                    "cols": cols
                }
                with open(grid_path, 'w', encoding='utf-8') as f:
                    json.dump(grids, f, ensure_ascii=False, indent=4)
                    
                self.update_status("草地区域已成功保存")
                self.root.after(0, self.load_saved_region)
            else:
                self.update_status("选择已取消或失败")
        except Exception as e:
            self.update_status(f"发生错误: {str(e)}")
        finally:
            self.root.after(0, lambda: self.btn_lawn.configure(state="normal"))

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
