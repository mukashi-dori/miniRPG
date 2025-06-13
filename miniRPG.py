import pygame
import random
import sys
from typing import List, Dict, Tuple, Optional, Union

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
GRAY = (150, 150, 150)


class Enemy:
    """敵クラス"""
    def __init__(self, name: str, target: int):
        self.name = name
        self.target = target  # ダイスロールの目標値（ロール <= target で勝利）


class Player:
    """プレイヤークラス"""
    def __init__(self):
        self.hp = 3
        self.max_hp = 3
    
    def heal(self, amount: int) -> None:
        """HPを回復"""
        self.hp = min(self.hp + amount, self.max_hp)
    
    def damage(self, amount: int) -> None:
        """ダメージを受ける"""
        self.hp = max(self.hp - amount, 0)
    
    def is_alive(self) -> bool:
        """生存確認"""
        return self.hp > 0


class EventManager:
    """イベント管理クラス"""
    def __init__(self):
        # イベントID: (タイプ, 説明, 序盤の重み, 終盤の重み)
        self.events = {
            1: ("道", "道が分かれている。左右どちらに進む？", 30, 15),
            2: ("戦闘", "洞窟のモンスターが現れた！", 10, 40),
            3: ("休憩", "静かな場所。何も起こらない。", 25, 10),
            4: ("水場", "壁から水が流れている。飲む？", 20, 10),
            5: ("宝箱", "古い宝箱を見つけた。開ける？", 15, 25)
        }
        
        # 敵タイプ: (名前, 目標値, 最小フェーズ, 最大フェーズ)
        self.enemies = [
            ("コウモリ", 7, 1, 3),
            ("ゴブリン", 6, 2, 5),
            ("オーク", 5, 4, 7),
            ("トロール", 4, 6, 9),
            ("洞窟の王", 3, 10, 10)  # ボス
        ]
    
    def get_event(self, phase: int) -> int:
        """フェーズに基づいてランダムイベントを選択"""
        if phase == 10:
            return 2  # フェーズ10は常に戦闘
        
        # 序盤/終盤で重みを変更
        is_first_half = phase <= 5
        weights = [self.events[i][2 if is_first_half else 3] for i in range(1, 6)]
        
        return random.choices(range(1, 6), weights=weights)[0]
    
    def get_enemy(self, phase: int) -> Enemy:
        """フェーズに基づいて敵を選択"""
        candidates = []
        
        for name, target, min_phase, max_phase in self.enemies:
            if min_phase <= phase <= max_phase:
                candidates.append((name, target))
        
        # フェーズ10は常にボス
        if phase == 10:
            return Enemy("洞窟の王", 3)
        
        name, target = random.choice(candidates)
        return Enemy(name, target)


class Game:
    """ゲームクラス"""
    # ゲーム状態
    STATE_TITLE = 0
    STATE_EVENT = 1
    STATE_BATTLE = 2
    STATE_BATTLE_ROLL = 3  # ダイスロール前の戦闘状態
    STATE_ENDING = 4
    STATE_GAME_OVER = 5
    STATE_TEXT = 6  # テキスト表示状態
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("洞窟探検RPG")
        self.clock = pygame.time.Clock()
        
        # 日本語フォントの設定（OS別）
        if sys.platform.startswith('win'):
            self.font_large = pygame.font.SysFont("Yu Gothic", 48)
            self.font_medium = pygame.font.SysFont("Yu Gothic", 36)
            self.font_small = pygame.font.SysFont("Yu Gothic", 24)
        elif sys.platform.startswith('darwin'):  # macOS
            self.font_large = pygame.font.SysFont("Hiragino Sans", 48)
            self.font_medium = pygame.font.SysFont("Hiragino Sans", 36)
            self.font_small = pygame.font.SysFont("Hiragino Sans", 24)
        else:  # Linux
            self.font_large = pygame.font.SysFont("Noto Sans CJK JP", 48)
            self.font_medium = pygame.font.SysFont("Noto Sans CJK JP", 36)
            self.font_small = pygame.font.SysFont("Noto Sans CJK JP", 24)
        
        self.state = self.STATE_TITLE
        self.player = Player()
        self.event_manager = EventManager()
        self.phase = 1  # 現在のフェーズ (1-10)
        self.current_event = None
        self.current_enemy = None
        self.message = ""
        self.sub_message = ""
        self.message_timer = 0
        self.dice_result = 0
        self.choice = 0  # 選択 (0: 左/はい, 1: 右/いいえ)
        self.battle_result = False
        self.battle_continue = False  # 戦闘継続フラグ
        self.game_over_pending = False  # ゲームオーバー保留フラグ
        
    def run(self):
        """メインゲームループ"""
        running = True
        
        while running:
            # イベント処理
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key_event(event.key)
            
            # 状態更新
            self.update()
            
            # 描画
            self.screen.fill(BLACK)
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()
    
    def handle_key_event(self, key):
        """キー入力処理"""
        if self.state == self.STATE_TITLE:
            if key == pygame.K_SPACE:
                self.start_game()
        
        elif self.state == self.STATE_TEXT:
            if key == pygame.K_SPACE:
                self.next_after_text()  # テキスト後の処理へ
        
        elif self.state == self.STATE_BATTLE_ROLL:
            if key == pygame.K_SPACE:
                self.roll_dice()  # ダイスロール実行
        
        elif self.state == self.STATE_BATTLE:
            if key == pygame.K_SPACE:
                if self.battle_result:
                    self.show_message("勝利した！")
                else:
                    # ラスボスかどうかでメッセージを変える
                    damage = 3 if self.phase == 10 and self.current_enemy.name == "洞窟の王" else 1
                    self.show_message(f"敗北した... HPが{damage}減った！", f"HP: {self.player.hp}/{self.player.max_hp}")
                    
                    # ゲームオーバー保留中の場合はここでゲームオーバー処理
                    if self.game_over_pending:
                        # メッセージ表示後にゲームオーバーになるよう、フラグだけ設定
                        self.battle_continue = False
                    else:
                        # 敗北後、同じ敵との戦闘を続ける
                        self.battle_continue = True
        
        elif self.state == self.STATE_GAME_OVER:
            if key == pygame.K_SPACE:
                self.state = self.STATE_TITLE  # タイトル画面に戻る
        
        elif self.state == self.STATE_ENDING:
            if key == pygame.K_SPACE:
                self.state = self.STATE_TITLE  # タイトル画面に戻る
        
        elif self.state == self.STATE_EVENT:
            if self.current_event == 1:  # 道イベント
                if key == pygame.K_LEFT:
                    self.choice = 0
                elif key == pygame.K_RIGHT:
                    self.choice = 1
                elif key == pygame.K_SPACE:
                    if self.choice == 0:
                        self.show_message("左に進んだ。")
                    else:
                        self.show_message("右に進んだ。")
            
            elif self.current_event == 3:  # 休憩イベント
                if key == pygame.K_SPACE:
                    self.show_message("静かな場所で休憩した。何も起こらない。")
            
            elif self.current_event == 4:  # 水場イベント
                if key == pygame.K_SPACE and self.choice == 0:  # 飲む
                    if random.random() < 0.5:
                        self.player.heal(1)
                        self.show_message("水を飲んだ。体調が良くなった！", f"HP: {self.player.hp}/{self.player.max_hp}")
                    else:
                        self.player.damage(1)
                        self.show_message("水を飲んだ。お腹が痛い...", f"HP: {self.player.hp}/{self.player.max_hp}")
                        if not self.player.is_alive():
                            self.game_over()
                            return
                elif key == pygame.K_SPACE and self.choice == 1:  # 飲まない
                    self.show_message("水を飲まなかった。何も起こらない。")
                elif key == pygame.K_LEFT:
                    self.choice = 0  # 飲む
                elif key == pygame.K_RIGHT:
                    self.choice = 1  # 飲まない
            
            elif self.current_event == 5:  # 宝箱イベント
                if key == pygame.K_SPACE and self.choice == 0:  # 開ける
                    result = random.randint(1, 3)
                    if result == 1:  # 空
                        self.show_message("宝箱は空だった...")
                    elif result == 2:  # 回復
                        self.player.heal(1)
                        self.show_message("回復薬を見つけた！", f"HP: {self.player.hp}/{self.player.max_hp}")
                    else:  # 罠（戦闘）
                        self.show_message("罠だった！敵が現れた！")
                        # メッセージ表示後に戦闘を開始するため、current_eventを設定するだけにする
                        self.current_event = 2  # 戦闘イベントとして扱う
                elif key == pygame.K_SPACE and self.choice == 1:  # 開けない
                    self.show_message("宝箱をそのままにした。")
                elif key == pygame.K_LEFT:
                    self.choice = 0  # 開ける
                elif key == pygame.K_RIGHT:
                    self.choice = 1  # 開けない
    
    def update(self):
        """状態更新"""
        if self.state == self.STATE_TEXT:
            self.message_timer += 1
            if self.message_timer >= FPS * 2:  # 2秒
                self.next_after_text()
    
    def next_after_text(self):
        """テキスト表示後の処理"""
        self.message_timer = 0
        
        # ゲームオーバー保留中の場合はここでゲームオーバー処理
        if self.game_over_pending:
            self.game_over_pending = False
            self.game_over()
            return
            
        # 宝箱から敵が出てきた場合の処理
        if self.current_event == 2 and self.current_enemy is None:
            self.start_battle()
            return
            
        # 戦闘後の処理
        if self.current_event == 2 and self.current_enemy is not None:  # 敵が存在する場合のみ処理
            if self.battle_result:
                # 戦闘に勝利した場合
                heal_message = ""
                
                # 20%の確率で勝利後に回復（戦闘継続フラグがない場合のみ）
                if not self.battle_continue and random.random() < 0.2:
                    self.player.heal(1)
                    heal_message = "\nHPが回復した！"
                
                # 最終戦闘ならエンディングへ
                if self.phase == 10:
                    self.state = self.STATE_ENDING
                    return
                    
                if heal_message:
                    self.show_message(f"戦闘に勝利した！{heal_message}", f"HP: {self.player.hp}/{self.player.max_hp}")
                    return
            else:
                # 敗北時の処理
                if self.phase == 10:  # 最終戦闘で敗北した場合
                    self.game_over()
                    return
                
                # 戦闘継続フラグがある場合、同じ敵との戦闘を続ける
                if self.battle_continue:
                    self.battle_continue = False
                    self.show_message(f"{self.current_enemy.name}は道を塞いでいる！")
                    self.state = self.STATE_BATTLE_ROLL
                    return
        
        # 次のフェーズへ
        if self.phase < 10:
            self.phase += 1
            self.next_event()
        else:
            self.state = self.STATE_ENDING
    
    def draw(self):
        """描画処理"""
        if self.state == self.STATE_TITLE:
            self.draw_title()
        elif self.state == self.STATE_EVENT:
            self.draw_event()
        elif self.state == self.STATE_BATTLE_ROLL:
            self.draw_battle_roll()
        elif self.state == self.STATE_BATTLE:
            self.draw_battle()
        elif self.state == self.STATE_TEXT:
            self.draw_text_screen()
        elif self.state == self.STATE_ENDING:
            self.draw_ending()
        elif self.state == self.STATE_GAME_OVER:
            self.draw_game_over()
        
        # フェーズ表示（タイトル画面以外）
        if self.state != self.STATE_TITLE:
            phase_text = self.font_small.render(f"フェーズ: {self.phase}/10", True, WHITE)
            self.screen.blit(phase_text, (SCREEN_WIDTH - 160, 10))
            
            # HP表示
            hp_text = self.font_small.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, WHITE)
            self.screen.blit(hp_text, (10, 10))
    
    def draw_title(self):
        """タイトル画面描画"""
        title = self.font_large.render("洞窟探検RPG", True, WHITE)
        subtitle = self.font_medium.render("- 伝説の宝を探せ -", True, WHITE)
        phase_info = self.font_small.render("全10フェーズの冒険", True, WHITE)
        instruction = self.font_small.render("スペースキーでスタート", True, WHITE)
        
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 220))
        self.screen.blit(phase_info, (SCREEN_WIDTH // 2 - phase_info.get_width() // 2, 280))
        self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
    
    def draw_event(self):
        """イベント画面描画"""
        # イベントタイプ表示
        event_type = self.event_manager.events[self.current_event][0]
        event_text = self.font_medium.render(f"イベント: {event_type}", True, WHITE)
        self.screen.blit(event_text, (SCREEN_WIDTH // 2 - event_text.get_width() // 2, 80))
        
        # イベント説明表示
        description = self.event_manager.events[self.current_event][1]
        desc_text = self.font_small.render(description, True, WHITE)
        self.screen.blit(desc_text, (SCREEN_WIDTH // 2 - desc_text.get_width() // 2, 150))
        
        # イベント固有の描画
        if self.current_event == 1:  # 道
            left_text = self.font_small.render("<- 左へ進む", True, WHITE if self.choice == 0 else GRAY)
            right_text = self.font_small.render("右へ進む ->", True, WHITE if self.choice == 1 else GRAY)
            self.screen.blit(left_text, (100, 250))
            self.screen.blit(right_text, (SCREEN_WIDTH - 100 - right_text.get_width(), 250))
            
            instruction = self.font_small.render("<- -> で選択、スペースで決定", True, WHITE)
            self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
        
        elif self.current_event == 4:  # 水場
            drink_text = self.font_small.render("<- 飲む", True, WHITE if self.choice == 0 else GRAY)
            ignore_text = self.font_small.render("飲まない ->", True, WHITE if self.choice == 1 else GRAY)
            self.screen.blit(drink_text, (100, 250))
            self.screen.blit(ignore_text, (SCREEN_WIDTH - 100 - ignore_text.get_width(), 250))
            
            instruction = self.font_small.render("<- -> で選択、スペースで決定", True, WHITE)
            self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
        
        elif self.current_event == 5:  # 宝箱
            open_text = self.font_small.render("<- 開ける", True, WHITE if self.choice == 0 else GRAY)
            leave_text = self.font_small.render("開けない ->", True, WHITE if self.choice == 1 else GRAY)
            self.screen.blit(open_text, (100, 250))
            self.screen.blit(leave_text, (SCREEN_WIDTH - 100 - leave_text.get_width(), 250))
            
            instruction = self.font_small.render("<- -> で選択、スペースで決定", True, WHITE)
            self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
        
        else:  # その他のイベント
            instruction = self.font_small.render("スペースキーで続ける", True, WHITE)
            self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
    
    def draw_battle_roll(self):
        """戦闘開始画面描画"""
        # 敵の名前表示
        enemy_text = self.font_medium.render(f"敵: {self.current_enemy.name}", True, RED)
        self.screen.blit(enemy_text, (SCREEN_WIDTH // 2 - enemy_text.get_width() // 2, 80))
        
        # 戦闘説明
        battle_text = self.font_small.render(f"{self.current_enemy.name}が現れた！", True, WHITE)
        self.screen.blit(battle_text, (SCREEN_WIDTH // 2 - battle_text.get_width() // 2, 150))
        
        # 目標値表示
        target_text = self.font_small.render(f"ダイスを振れ！目標値：{self.current_enemy.target}以下", True, WHITE)
        self.screen.blit(target_text, (SCREEN_WIDTH // 2 - target_text.get_width() // 2, 200))
        
        # 指示表示
        instruction = self.font_small.render("スペースキーでダイスを振る", True, WHITE)
        self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
    
    def draw_battle(self):
        """戦闘結果画面描画"""
        # 敵の名前表示
        enemy_text = self.font_medium.render(f"敵: {self.current_enemy.name}", True, RED)
        self.screen.blit(enemy_text, (SCREEN_WIDTH // 2 - enemy_text.get_width() // 2, 80))
        
        # ダイスの結果表示
        dice_text = self.font_large.render(f"ダイス: {self.dice_result}", True, WHITE)
        self.screen.blit(dice_text, (SCREEN_WIDTH // 2 - dice_text.get_width() // 2, 180))
        
        # 戦闘結果表示
        result_color = GREEN if self.battle_result else RED
        result_text = self.font_medium.render(
            f"{'勝利！' if self.battle_result else '敗北...'} (目標値: {self.current_enemy.target})",
            True, result_color
        )
        self.screen.blit(result_text, (SCREEN_WIDTH // 2 - result_text.get_width() // 2, 250))
        
        # 指示表示
        instruction = self.font_small.render("スペースキーで続ける", True, WHITE)
        self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
    
    def draw_text_screen(self):
        """テキスト画面描画"""
        # メッセージ表示（改行対応）
        lines = self.message.split('\n')
        y_pos = 180
        
        for i, line in enumerate(lines):
            message_text = self.font_medium.render(line, True, WHITE)
            self.screen.blit(message_text, (SCREEN_WIDTH // 2 - message_text.get_width() // 2, y_pos + i * 40))
        
        # サブメッセージ表示（あれば）
        if self.sub_message:
            sub_text = self.font_small.render(self.sub_message, True, WHITE)
            self.screen.blit(sub_text, (SCREEN_WIDTH // 2 - sub_text.get_width() // 2, y_pos + len(lines) * 40 + 10))
        
        # 指示表示
        instruction = self.font_small.render("スペースキーで続ける", True, WHITE)
        self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
    
    def draw_ending(self):
        """エンディング画面描画"""
        title = self.font_large.render("ゲームクリア！", True, GREEN)
        message1 = self.font_medium.render("伝説の宝を見つけた！", True, WHITE)
        message2 = self.font_medium.render("あなたは英雄として称えられるだろう...", True, WHITE)
        instruction = self.font_small.render("スペースキーでタイトルに戻る", True, WHITE)
        
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))
        self.screen.blit(message1, (SCREEN_WIDTH // 2 - message1.get_width() // 2, 220))
        self.screen.blit(message2, (SCREEN_WIDTH // 2 - message2.get_width() // 2, 270))
        self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
    
    def draw_game_over(self):
        """ゲームオーバー画面描画"""
        title = self.font_large.render("ゲームオーバー", True, RED)
        message = self.font_medium.render("あなたは闇の中に消えた...", True, WHITE)
        instruction = self.font_small.render("スペースキーでタイトルに戻る", True, WHITE)
        
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))
        self.screen.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, 220))
        self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
    
    def start_game(self):
        """ゲーム開始"""
        self.state = self.STATE_EVENT
        self.player = Player()
        self.phase = 1
        self.next_event()
    
    def next_event(self):
        """次のイベント設定"""
        self.current_event = self.event_manager.get_event(self.phase)
        self.choice = 0  # 選択リセット
        
        if self.current_event == 2:  # 戦闘イベント
            self.start_battle()
        elif self.current_event == 3:  # 休憩イベント
            self.show_message("静かな場所で休憩した。何も起こらない。")
        elif self.current_event == 4:  # 水場イベント
            self.state = self.STATE_EVENT
        elif self.current_event == 5:  # 宝箱イベント
            self.state = self.STATE_EVENT
        else:
            self.state = self.STATE_EVENT
    
    def start_battle(self):
        """戦闘開始"""
        self.current_enemy = self.event_manager.get_enemy(self.phase)
        self.battle_continue = False  # 戦闘継続フラグをリセット
        self.state = self.STATE_BATTLE_ROLL
    
    def roll_dice(self):
        """ダイスロール実行"""
        self.dice_result = random.randint(1, 10)
        self.battle_result = self.dice_result <= self.current_enemy.target
        
        if not self.battle_result:
            # 敗北時はダメージを受ける（ラスボスは3ダメージ、それ以外は1ダメージ）
            damage = 3 if self.phase == 10 and self.current_enemy.name == "洞窟の王" else 1
            self.player.damage(damage)
            # HPが0になっても結果表示のため、ゲームオーバー処理は行わない
            self.game_over_pending = not self.player.is_alive()
        
        self.state = self.STATE_BATTLE
    
    def show_message(self, message: str, sub_message: str = ""):
        """メッセージ表示（文章の自動改行処理）"""
        # 「。」で区切って改行する
        if "。" in message:
            parts = message.split("。")
            formatted_message = ""
            for i, part in enumerate(parts):
                if part:  # 空文字列でない場合
                    if i < len(parts) - 1:  # 最後の要素でなければ「。」を付ける
                        formatted_message += part + "。\n"
                    else:  # 最後の要素で、それが空でなければ追加
                        formatted_message += part
            self.message = formatted_message.rstrip('\n')  # 末尾の改行を削除
        else:
            self.message = message
            
        self.sub_message = sub_message
        self.state = self.STATE_TEXT
        self.message_timer = 0
    
    def game_over(self):
        """ゲームオーバー処理"""
        self.state = self.STATE_GAME_OVER


if __name__ == "__main__":
    game = Game()
    game.run()