import configparser

import pygame
import sys
import random

from config import *

#--------- 初期設定 ----------
pygame.init()

screen = pygame.display.set_mode((
    Config.SCREEN_WIDTH, Config.SCREEN_HEIGHT
))
pygame.display.set_caption("Step2: Enemies & Collision")
clock = pygame.time.Clock()

font = pygame.font.SysFont(None, 28)
big_font = pygame.font.SysFont(None, 60)


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


#-------- 敵クラス ----------
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        size = random.randint(24,40)
        self.image = pygame.Surface((size, size))
        self.image.fill(Config.ENEMY_COLOR)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, Config.SCREEN_WIDTH - size)
        self.rect.y = -size
        self.speed = random.randint(2,5)

    def update(self, keys=None):
        self.rect.y += self.speed
        # 画面下に出たら消す
        if self.rect.top > Config.SCREEN_HEIGHT:
            self.kill()


def draw_text(text, x, y, color=Config.WHITE, font_obj=None):
    font_obj = font_obj or font
    surface = font_obj.render(text, True, color)
    screen.blit(surface, (x, y))


def draw_center_text(text, y, color=Config.WHITE):
    surface = big_font.render(text, True, color)
    rect = surface.get_rect(center=(Config.SCREEN_WIDTH // 2, y))
    screen.blit(surface, rect)


# -------- ゲーム状態の初期化 ----------
def reset_game():
    player = Player()
    return {
        "player_group": pygame.sprite.GroupSingle(player),
        "player": player,
        "bullets": pygame.sprite.Group(),
        "enemies": pygame.sprite.Group(),
        "score": 0,
        "game_over": False,
        "spawn_timer": 0,
    }


# -------- メインループ ----------
def main():
    state = reset_game()
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
                elif event.key == pygame.K_SPACE and not state["game_over"]:
                    p = state["player"]
                    state["bullets"].add(Bullet(p.rect.centerx, p.rect.top))
                elif event.key == pygame.K_r and state["game_over"]:
                    state = reset_game()

        if not state["game_over"]:
            # 更新
            keys = pygame.key.get_pressed()
            state["player_group"].update(keys)
            state["bullets"].update()
            state["enemies"].update()

            # 敵の出現（タイマー式）
            state["spawn_timer"] += 1
            if state["spawn_timer"] >= 30:
                state["enemies"].add(Enemy())
                state["spawn_timer"] = 0

            # 弾　＊　敵　の当たり判定（両方消してスコア加算）
            hits = pygame.sprite.groupcollide(
                state["bullets"], state["enemies"], True, True)
            state["score"] += len(hits) * 10

        # 描画
        screen.fill(Config.BLACK)
        state["player_group"].draw(screen)
        state["bullets"].draw(screen)
        state["enemies"].draw(screen)
        draw_text(f"Score: {state['score']}", 10, 10)

        if state["game_over"]:
            draw_center_text("GAME OVER", Config.SCREEN_HEIGHT // 2 - 20, Config.RED)
            draw_text(
                "Press R to Restart",
                Config.SCREEN_WIDTH // 2 - 80,
                Config.SCREEN_HEIGHT // 2 + 30,
            )


        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    main()

