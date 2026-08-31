import pygame
import random
import time
import os

# 初始化 Pygame
pygame.init()

# 常量设置
WIDTH, HEIGHT = 800, 600
FPS = 60
MOLE_DISPLAY_TIME = 1000 # 地鼠在每个位置停留的毫秒数
GAME_DURATION = 30 # 游戏总时长（秒）

# 颜色定义 - 更加现代和美观的配色方案
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
SKY_BLUE = (174, 226, 255)
GRASS_GREEN = (147, 198, 114)
HOLE_COLOR = (75, 56, 50)
UI_BG_COLOR = (60, 64, 72, 200) # 带透明度的深色背景
UI_TEXT_COLOR = (240, 240, 240)
SHADOW_COLOR = (0, 0, 0, 50)

# 游戏状态常量
STATE_VISIBLE = 1
STATE_HIDDEN = 2
HIDE_DURATION = 200 # 消失后的等待时间(毫秒)

# 地洞位置定义 (3x3 网格)
HOLES = [
    (150, 250), (400, 250), (650, 250),
    (150, 400), (400, 400), (650, 400),
    (150, 550), (400, 550), (650, 550)
]

# 设置显示窗口
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("打地鼠 (Whack-a-Mole) - 精美版")

# 加载资源
current_dir = os.path.dirname(os.path.abspath(__file__))
mole_image_path = os.path.join(current_dir, "mole.png")
try:
    mole_image = pygame.image.load(mole_image_path)
    mole_image = pygame.transform.scale(mole_image, (100, 100))
except Exception as e:
    print(f"加载图片失败: {e}")
    pygame.quit()
    exit()

# 字体设置 - 确保支持中文
def get_chinese_font(size):
    font_paths = [
        r'C:\Windows\Fonts\msyh.ttc',
        r'C:\Windows\Fonts\msyhbd.ttc',
        r'C:\Windows\Fonts\simhei.ttf',
        r'C:\Windows\Fonts\simsun.ttc'
    ]
    for path in font_paths:
        if os.path.exists(path):
            return pygame.font.Font(path, size)
    return pygame.font.Font(None, size)

font = get_chinese_font(36)
large_font = get_chinese_font(72)
ui_font = get_chinese_font(28)

def draw_text(text, font, color, surface, x, y):
    textobj = font.render(text, True, color)
    textrect = textobj.get_rect()
    textrect.center = (x, y)
    
    # 绘制带阴影的文本
    shadowobj = font.render(text, True, (30, 30, 30))
    shadowrect = shadowobj.get_rect()
    shadowrect.center = (x + 2, y + 2)
    
    surface.blit(shadowobj, shadowrect)
    surface.blit(textobj, textrect)

def draw_ui_panel(surface, score, remaining_time):
    # 绘制半透明的UI背景面板
    ui_surface = pygame.Surface((WIDTH, 60), pygame.SRCALPHA)
    pygame.draw.rect(ui_surface, UI_BG_COLOR, (0, 0, WIDTH, 60))
    # 底部边界高光
    pygame.draw.line(ui_surface, (100, 100, 110, 200), (0, 59), (WIDTH, 59), 2)
    surface.blit(ui_surface, (0, 0))
    
    # 绘制UI文本
    score_text = ui_font.render(f"🎯 得分: {score}", True, UI_TEXT_COLOR)
    time_text = ui_font.render(f"⏳ 剩余时间: {int(remaining_time)}s", True, UI_TEXT_COLOR)
    
    surface.blit(score_text, (40, 15))
    surface.blit(time_text, (WIDTH - time_text.get_width() - 40, 15))

def main():
    clock = pygame.time.Clock()
    score = 0
    start_time = time.time()

    mole_rect = mole_image.get_rect()
    
    mole_state = STATE_VISIBLE
    current_hole_index = -1
    state_change_time = pygame.time.get_ticks()

    def spawn_mole():
        nonlocal current_hole_index, mole_state, state_change_time
        # 选择一个不同于当前地洞的新地洞
        new_index = current_hole_index
        while new_index == current_hole_index:
            new_index = random.randint(0, len(HOLES) - 1)
        current_hole_index = new_index
        
        # 将地鼠放置在地洞位置，略微向上偏移使其看起来像是钻出来
        hole_x, hole_y = HOLES[current_hole_index]
        mole_rect.centerx = hole_x
        mole_rect.bottom = hole_y + 10 
        
        mole_state = STATE_VISIBLE
        state_change_time = pygame.time.get_ticks()

    def hide_mole():
        nonlocal mole_state, state_change_time
        mole_state = STATE_HIDDEN
        state_change_time = pygame.time.get_ticks()

    # 初始化第一次地鼠出现
    spawn_mole()

    running = True
    game_over = False

    while running:
        current_time_ticks = pygame.time.get_ticks()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN and not game_over:
                if event.button == 1: # 左键点击
                    if mole_state == STATE_VISIBLE and mole_rect.collidepoint(event.pos):
                        score += 1
                        hide_mole() # 击中后立刻消失
            
            if event.type == pygame.KEYDOWN and game_over:
                if event.key == pygame.K_r:
                    # 重新开始游戏
                    score = 0
                    start_time = time.time()
                    game_over = False
                    spawn_mole()

        if not game_over:
            elapsed_time = time.time() - start_time
            remaining_time = max(0, GAME_DURATION - elapsed_time)

            if remaining_time == 0:
                game_over = True
            
            # 状态切换逻辑
            if mole_state == STATE_VISIBLE:
                # 如果显示时间超过设定时间，地鼠逃跑（隐藏）
                if current_time_ticks - state_change_time > MOLE_DISPLAY_TIME:
                    hide_mole()
            elif mole_state == STATE_HIDDEN:
                # 隐藏一段时间后，重新出现
                if current_time_ticks - state_change_time > HIDE_DURATION:
                    spawn_mole()

        # --- 绘制阶段 ---
        
        # 1. 绘制天空背景
        pygame.draw.rect(screen, SKY_BLUE, (0, 0, WIDTH, HEIGHT // 3))
        # 2. 绘制草地背景
        pygame.draw.rect(screen, GRASS_GREEN, (0, HEIGHT // 3, WIDTH, HEIGHT * 2 // 3))
        # 在草地顶部画一条分界线（模拟远处的山坡/阴影）
        pygame.draw.line(screen, (120, 180, 90), (0, HEIGHT // 3), (WIDTH, HEIGHT // 3), 4)

        # 3. 绘制所有的地洞
        for hole_x, hole_y in HOLES:
            # 洞穴阴影
            pygame.draw.ellipse(screen, SHADOW_COLOR, (hole_x - 60, hole_y - 25, 120, 50))
            # 洞穴内部
            pygame.draw.ellipse(screen, HOLE_COLOR, (hole_x - 55, hole_y - 20, 110, 40))
            # 洞穴内边缘高光/暗部增强立体感
            pygame.draw.ellipse(screen, (45, 30, 25), (hole_x - 50, hole_y - 15, 100, 30))

        if not game_over:
            # 4. 如果地鼠是可见状态，绘制地鼠
            if mole_state == STATE_VISIBLE:
                screen.blit(mole_image, mole_rect)
            
            # 5. 绘制顶部的 UI 面板
            draw_ui_panel(screen, score, remaining_time)
        else:
            # 绘制半透明黑色遮罩
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            
            # 绘制游戏结束界面
            draw_text("游戏结束!", large_font, WHITE, screen, WIDTH//2, HEIGHT//2 - 60)
            draw_text(f"🏆 最终得分: {score} 分", font, (255, 215, 0), screen, WIDTH//2, HEIGHT//2 + 20)
            
            # 闪烁的重新开始提示
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                draw_text("👉 按 'R' 键重新开始 👈", font, WHITE, screen, WIDTH//2, HEIGHT//2 + 100)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
