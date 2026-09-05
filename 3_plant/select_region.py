import os
import json
from pynput import mouse

def select_game_region(status_callback=None):
    clicks = []

    def on_click(x, y, button, pressed):
        if pressed and button == mouse.Button.left:
            clicks.append((int(x), int(y)))
            if len(clicks) == 1:
                msg = f"已记录左上角坐标: ({int(x)}, {int(y)})。请点击右下角..."
                if status_callback:
                    status_callback(msg)
                else:
                    print(msg)
            elif len(clicks) == 2:
                msg = f"已记录右下角坐标: ({int(x)}, {int(y)})。"
                if status_callback:
                    status_callback(msg)
                else:
                    print(msg)
                return False  # Stop listener

    init_msg = "请点击屏幕上的两点以确定截图区域：\n1. 点击左上角"
    if status_callback:
        status_callback(init_msg)
    else:
        print("\n" + init_msg)

    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

    if len(clicks) == 2:
        top_left = clicks[0]
        bottom_right = clicks[1]
        
        # 确保左上角和右下角坐标正确（即使点反了也可以自动纠正）
        x1 = min(top_left[0], bottom_right[0])
        y1 = min(top_left[1], bottom_right[1])
        x2 = max(top_left[0], bottom_right[0])
        y2 = max(top_left[1], bottom_right[1])
        
        region = {
            "top_left": {"x": x1, "y": y1},
            "bottom_right": {"x": x2, "y": y2},
            "width": x2 - x1,
            "height": y2 - y1
        }
        
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'region_config.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(region, f, ensure_ascii=False, indent=4)
            
        if not status_callback:
            print(f"\n截图区域已保存至 {config_path}:")
            print(json.dumps(region, ensure_ascii=False, indent=4))
            
        return region
    return None

if __name__ == "__main__":
    # 为了保持向后兼容或单独测试，保留直接运行的能力
    select_game_region()
