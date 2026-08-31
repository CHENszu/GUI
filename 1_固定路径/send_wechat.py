import os
import pyautogui
import pyperclip
import time

def send_wechat_message(contact_name, message):
    print("开始执行微信自动化发送脚本...")
    
    # 步骤 1：主动启动/唤醒微信
    print("正在唤醒微信...")
    # Windows 系统可以通过直接执行微信的可执行文件路径来启动
    # 或者通过 explorer 命令尝试唤醒（如果之前使用 start wechat 失败，我们可以用 explorer 配合微信默认安装路径，或者提示用户打开微信）
    # 更稳妥的做法是要求用户提供微信路径，但作为通用脚本，我们可以先给出提示，并尝试几个常见路径
    wechat_paths = [
        r"C:\Program Files\Tencent\WeChat\WeChat.exe",
        r"C:\Program Files (x86)\Tencent\WeChat\WeChat.exe"
    ]
    
    launched = False
    for path in wechat_paths:
        if os.path.exists(path):
            os.startfile(path)
            launched = True
            break
            
    if not launched:
        print("未在默认路径找到微信，请确保微信已经运行...")
        # 尝试使用全局快捷键唤醒（前提是用户没有修改过微信的默认快捷键）
        pyautogui.hotkey('ctrl', 'alt', 'w')
    
    # 等待微信登录界面或主界面弹出
    print("等待微信界面加载...")
    time.sleep(2)
    
    # 步骤 2：回车确认登录
    # 如果微信未登录，这里会触发“登录”按钮；
    # 如果微信已登录，start wechat 会唤醒主界面，这里的回车通常不会有负面影响。
    print("尝试回车登录...")
    pyautogui.press('enter')
    
    # 等待登录完成，主界面加载和消息同步（如果刚登录，可能需要稍长一点的时间）
    print("等待微信主界面准备就绪...")
    time.sleep(8)
    
    # 步骤 3：定位到搜索框
    print("正在搜索联系人...")
    pyautogui.hotkey('ctrl', 'f')
    time.sleep(1)
    
    # 步骤 4：输入联系人姓名
    pyperclip.copy(contact_name)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(2)  # 等待微信搜索出结果
    
    # 回车进入聊天窗口
    pyautogui.press('enter')
    time.sleep(1)  # 等待聊天窗口加载
    
    # 步骤 5：输入并发送消息
    print(f"正在发送消息: {message}")
    pyperclip.copy(message)
    pyautogui.hotkey('ctrl', 'v')
    time.sleep(0.5)
    
    # 回车发送
    pyautogui.press('enter')
    print("消息发送完成！")

if __name__ == '__main__':
    # 为了防止误触，留出3秒钟的准备时间
    print("脚本将在 3 秒后开始运行，请不要移动鼠标或敲击键盘...")
    time.sleep(3)
    
    target_contact = "vl"
    msg_content = "这是一个测试消息"
    
    send_wechat_message(target_contact, msg_content)
