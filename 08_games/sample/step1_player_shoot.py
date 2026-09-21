"""
ステップ1: 自機の移動と弾の発射
シューティングゲームの一番の土台になるサンプルです。

操作方法:
  左右矢印キー / A・D : 左右移動
  スペースキー         : 弾を発射
  Esc または ウィンドウを閉じる : 終了
"""

import pygame
import sys

# ---------- 初期設定 ----------
pygame.init()

SCREEN_WIDTH = 480
SCREEN_HEIGHT = 640
FPS = 60

WHITE = (255, 255, 255)
BLACK = (10, 10, 30)
PLAYER_COLOR = (80, 200, 255)
BULLET_COLOR = (255, 220, 80)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Step1: Player Move & Shoot")
clock = pygame.time.Clock()


# ---------- 自機クラス ----------
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 30))
        self.image.fill(PLAYER_COLOR)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 20
        self.speed = 5

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed

        # 画面外に出ないように制限
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, SCREEN_WIDTH)


# ---------- 弾クラス ----------
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((6, 16))
        self.image.fill(BULLET_COLOR)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = 8

    def update(self, keys=None):
        self.rect.y -= self.speed
        # 画面上に出たら消す
        if self.rect.bottom < 0:
            self.kill()


# ---------- グループ作成 ----------
player = Player()
player_group = pygame.sprite.GroupSingle(player)
bullets = pygame.sprite.Group()

font = pygame.font.SysFont(None, 28)


def draw_text(text, x, y):
    surface = font.render(text, True, WHITE)
    screen.blit(surface, (x, y))


# ---------- メインループ ----------
def main():
    running = True
    while running:
        clock.tick(FPS)  # FPSを固定(環境による速度差を防ぐ)

        # --- イベント処理 ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    bullets.add(Bullet(player.rect.centerx, player.rect.top))

        # --- 更新 ---
        keys = pygame.key.get_pressed()
        player_group.update(keys)
        bullets.update()

        # --- 描画 ---
        screen.fill(BLACK)
        player_group.draw(screen)
        bullets.draw(screen)
        draw_text(f"Bullets: {len(bullets)}", 10, 10)
        draw_text("← → : Move   SPACE : Shoot", 10, SCREEN_HEIGHT - 30)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
