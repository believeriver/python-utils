import pygame
import sys

from config import *

#--------- 初期設定 ----------
pygame.init()

screen = pygame.display.set_mode((
    Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT
))
pygame.display.set_caption("Step1: Player Move & Shoot")
clock = pygame.time.Clock()


#--------- 自機クラス ----------
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((40, 30))
        self.image.fill(Config.PLAYER_COLOR)
        self.rect = self.image.get_rect()
        self.rect.centerx = Config.SCREEN_WIDTH // 2
        self.rect.bottom = Config.SCREEN_HEIGHT -20
        self.speed = 5

    def update(self, keys):
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed

        # 画面外に出ないように制限
        self.rect.left = max(self.rect.left, 0)
        self.rect.right = min(self.rect.right, Config.SCREEN_WIDTH)


#--------- 弾クラス ----------
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((6, 16))
        self.image.fill(Config.BULLET_COLOR)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = 8

    def update(self, keys=None):
        self.rect.y -= self.speed
        # 画面上に出たら消す
        if self.rect.bottom < 0:
            self.kill()


# -------- グループ作成 ----------
player = Player()
player_group = pygame.sprite.Group(player)
bullets = pygame.sprite.Group()

font = pygame.font.SysFont(None, 28)


def draw_text(text, x, y):
    surface = font.render(text, True, Config.WHITE)
    screen.blit(surface, (x, y))


# -------- メインループ ----------
def main():
    running = True
    while running:
        clock.tick(Config.FPS)

        # イベント処理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_SPACE:
                    # 弾を発射
                    bullet = Bullet(player.rect.centerx, player.rect.top)
                    bullets.add(bullet)

        # 更新
        keys = pygame.key.get_pressed()
        player_group.update(keys)
        bullets.update()

        # 描画
        screen.fill(Config.BLACK)
        player_group.draw(screen)
        bullets.draw(screen)
        draw_text(f"Bullets: {len(bullets)}", 10, 10)
        draw_text("← → or A D: Move, SPACE: Shoot, ESC: Quit", 10, Config.SCREEN_HEIGHT - 30)

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()

