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
    """Enemy class"""
    def __init__(self, name: str, target: int):
        self.name = name
        self.target = target  # Target value for dice roll (win if roll <= target)


class Player:
    """Player class"""
    def __init__(self):
        self.hp = 3
        self.max_hp = 3
    
    def heal(self, amount: int) -> None:
        """Heal HP"""
        self.hp = min(self.hp + amount, self.max_hp)
    
    def damage(self, amount: int) -> None:
        """Take damage"""
        self.hp = max(self.hp - amount, 0)
    
    def is_alive(self) -> bool:
        """Check if alive"""
        return self.hp > 0


class EventManager:
    """Event manager class"""
    def __init__(self):
        # Event ID: (type, description, early weight, late weight)
        self.events = {
            1: ("Path", "The path splits. Choose left or right.", 30, 15),
            2: ("Battle", "A cave monster appears!", 10, 40),
            3: ("Rest", "A quiet area. Nothing happens.", 25, 10),
            4: ("Water", "Water flows from the wall. Drink it?", 20, 10),
            5: ("Chest", "You found an old chest. Open it?", 15, 25)
        }
        
        # Enemy types: (name, target, min phase, max phase)
        self.enemies = [
            ("Bat", 7, 1, 3),
            ("Goblin", 6, 2, 5),
            ("Orc", 5, 4, 7),
            ("Troll", 4, 6, 9),
            ("Cave King", 3, 10, 10)  # Boss
        ]
    
    def get_event(self, phase: int) -> int:
        """Select random event based on phase"""
        if phase == 10:
            return 2  # Phase 10 is always battle
        
        # Change weights based on early/late game
        is_first_half = phase <= 5
        weights = [self.events[i][2 if is_first_half else 3] for i in range(1, 6)]
        
        return random.choices(range(1, 6), weights=weights)[0]
    
    def get_enemy(self, phase: int) -> Enemy:
        """Select enemy based on phase"""
        candidates = []
        
        for name, target, min_phase, max_phase in self.enemies:
            if min_phase <= phase <= max_phase:
                candidates.append((name, target))
        
        # Phase 10 is always boss
        if phase == 10:
            return Enemy("Cave King", 3)
        
        name, target = random.choice(candidates)
        return Enemy(name, target)


class Game:
    """Game class"""
    # Game states
    STATE_TITLE = 0
    STATE_EVENT = 1
    STATE_BATTLE = 2
    STATE_ENDING = 3
    STATE_GAME_OVER = 4
    STATE_TEXT = 5  # Text display state
    
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Cave Explorer RPG")
        self.clock = pygame.time.Clock()
        self.font_large = pygame.font.SysFont(None, 48)
        self.font_medium = pygame.font.SysFont(None, 36)
        self.font_small = pygame.font.SysFont(None, 24)
        
        self.state = self.STATE_TITLE
        self.player = Player()
        self.event_manager = EventManager()
        self.phase = 1  # Current phase (1-10)
        self.current_event = None
        self.current_enemy = None
        self.message = ""
        self.sub_message = ""
        self.message_timer = 0
        self.dice_result = 0
        self.choice = 0  # Choice (0: left/yes, 1: right/no)
        self.battle_result = False
        
    def run(self):
        """Main game loop"""
        running = True
        
        while running:
            # Event handling
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self.handle_key_event(event.key)
            
            # Update state
            self.update()
            
            # Draw
            self.screen.fill(BLACK)
            self.draw()
            
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()
    
    def handle_key_event(self, key):
        """Handle key input"""
        if self.state == self.STATE_TITLE:
            if key == pygame.K_SPACE:
                self.start_game()
        
        elif self.state == self.STATE_TEXT:
            if key == pygame.K_z:
                self.message_timer = 0  # Skip message
        
        elif self.state == self.STATE_BATTLE:
            if key == pygame.K_z:
                self.show_message(f"{'You won!' if self.battle_result else 'You lost...'}")
        
        elif self.state == self.STATE_EVENT:
            if self.current_event == 1:  # Path event
                if key == pygame.K_LEFT:
                    self.choice = 0
                    self.show_message("You went left.")
                elif key == pygame.K_RIGHT:
                    self.choice = 1
                    self.show_message("You went right.")
                elif key == pygame.K_z:
                    if self.choice == 0:
                        self.show_message("You went left.")
                    else:
                        self.show_message("You went right.")
            
            elif self.current_event == 3:  # Rest event
                if key == pygame.K_z:
                    self.show_message("You rested in a quiet area. Nothing happens.")
            
            elif self.current_event == 4:  # Water event
                if key == pygame.K_z and self.choice == 0:  # Drink
                    if random.random() < 0.5:
                        self.player.heal(1)
                        self.show_message("You drank the water. You feel better!", f"HP: {self.player.hp}/{self.player.max_hp}")
                    else:
                        self.player.damage(1)
                        self.show_message("You drank the water. Your stomach hurts...", f"HP: {self.player.hp}/{self.player.max_hp}")
                        if not self.player.is_alive():
                            self.game_over()
                            return
                elif key == pygame.K_z and self.choice == 1:  # Don't drink
                    self.show_message("You didn't drink the water. Nothing happens.")
                elif key == pygame.K_LEFT:
                    self.choice = 0  # Drink
                elif key == pygame.K_RIGHT:
                    self.choice = 1  # Don't drink
            
            elif self.current_event == 5:  # Chest event
                if key == pygame.K_z and self.choice == 0:  # Open
                    result = random.randint(1, 3)
                    if result == 1:  # Empty
                        self.show_message("The chest was empty...")
                    elif result == 2:  # Heal
                        self.player.heal(1)
                        self.show_message("You found a healing potion!", f"HP: {self.player.hp}/{self.player.max_hp}")
                    else:  # Trap (battle)
                        self.show_message("It was a trap! A monster jumps out!")
                        self.start_battle()
                elif key == pygame.K_z and self.choice == 1:  # Don't open
                    self.show_message("You left the chest alone.")
                elif key == pygame.K_LEFT:
                    self.choice = 0  # Open
                elif key == pygame.K_RIGHT:
                    self.choice = 1  # Don't open
    
    def update(self):
        """Update state"""
        if self.state == self.STATE_TEXT:
            self.message_timer += 1
            if self.message_timer >= FPS * 2:  # 2 seconds
                self.message_timer = 0
                
                # After battle processing
                if self.current_event == 2:
                    if self.battle_result:
                        # 20% chance to heal after victory
                        if random.random() < 0.2:
                            self.player.heal(1)
                            self.show_message(f"You won the battle! You recovered some HP!", f"HP: {self.player.hp}/{self.player.max_hp}")
                            return
                        
                        # If final battle, go to ending
                        if self.phase == 10:
                            self.state = self.STATE_ENDING
                            return
                    else:
                        self.game_over()
                        return
                
                # Next phase
                if self.phase < 10:
                    self.phase += 1
                    self.next_event()
                else:
                    self.state = self.STATE_ENDING
    
    def draw(self):
        """Draw everything"""
        if self.state == self.STATE_TITLE:
            self.draw_title()
        elif self.state == self.STATE_EVENT:
            self.draw_event()
        elif self.state == self.STATE_BATTLE:
            self.draw_battle()
        elif self.state == self.STATE_TEXT:
            self.draw_text_screen()
        elif self.state == self.STATE_ENDING:
            self.draw_ending()
        elif self.state == self.STATE_GAME_OVER:
            self.draw_game_over()
        
        # Show phase (except title screen)
        if self.state != self.STATE_TITLE:
            phase_text = self.font_small.render(f"Phase: {self.phase}/10", True, WHITE)
            self.screen.blit(phase_text, (SCREEN_WIDTH - 120, 10))
            
            # Show HP
            hp_text = self.font_small.render(f"HP: {self.player.hp}/{self.player.max_hp}", True, WHITE)
            self.screen.blit(hp_text, (10, 10))
    
    def draw_title(self):
        """Draw title screen"""
        title = self.font_large.render("Cave Explorer RPG", True, WHITE)
        subtitle = self.font_medium.render("- Find the Treasure -", True, WHITE)
        instruction = self.font_small.render("Press SPACE to start", True, WHITE)
        
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 220))
        self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
    
    def draw_event(self):
        """Draw event screen"""
        # Show event type
        event_type = self.event_manager.events[self.current_event][0]
        event_text = self.font_medium.render(f"Event: {event_type}", True, WHITE)
        self.screen.blit(event_text, (SCREEN_WIDTH // 2 - event_text.get_width() // 2, 80))
        
        # Show event description
        description = self.event_manager.events[self.current_event][1]
        desc_text = self.font_small.render(description, True, WHITE)
        self.screen.blit(desc_text, (SCREEN_WIDTH // 2 - desc_text.get_width() // 2, 150))
        
        # Event-specific drawing
        if self.current_event == 1:  # Path
            left_text = self.font_small.render("<- Go Left", True, WHITE if self.choice == 0 else GRAY)
            right_text = self.font_small.render("Go Right ->", True, WHITE if self.choice == 1 else GRAY)
            self.screen.blit(left_text, (100, 250))
            self.screen.blit(right_text, (SCREEN_WIDTH - 100 - right_text.get_width(), 250))
            
            instruction = self.font_small.render("<- -> to select, Z to confirm", True, WHITE)
            self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
        
        elif self.current_event == 4:  # Water
            drink_text = self.font_small.render("<- Drink", True, WHITE if self.choice == 0 else GRAY)
            ignore_text = self.font_small.render("Don't Drink ->", True, WHITE if self.choice == 1 else GRAY)
            self.screen.blit(drink_text, (100, 250))
            self.screen.blit(ignore_text, (SCREEN_WIDTH - 100 - ignore_text.get_width(), 250))
            
            instruction = self.font_small.render("<- -> to select, Z to confirm", True, WHITE)
            self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
        
        elif self.current_event == 5:  # Chest
            open_text = self.font_small.render("<- Open", True, WHITE if self.choice == 0 else GRAY)
            leave_text = self.font_small.render("Don't Open ->", True, WHITE if self.choice == 1 else GRAY)
            self.screen.blit(open_text, (100, 250))
            self.screen.blit(leave_text, (SCREEN_WIDTH - 100 - leave_text.get_width(), 250))
            
            instruction = self.font_small.render("<- -> to select, Z to confirm", True, WHITE)
            self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
        
        else:  # Other events
            instruction = self.font_small.render("Press Z to continue", True, WHITE)
            self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
    
    def draw_battle(self):
        """Draw battle screen"""
        # Show enemy name
        enemy_text = self.font_medium.render(f"Enemy: {self.current_enemy.name}", True, RED)
        self.screen.blit(enemy_text, (SCREEN_WIDTH // 2 - enemy_text.get_width() // 2, 80))
        
        # Show dice result
        dice_text = self.font_large.render(f"Dice Roll: {self.dice_result}", True, WHITE)
        self.screen.blit(dice_text, (SCREEN_WIDTH // 2 - dice_text.get_width() // 2, 180))
        
        # Show battle result
        result_color = GREEN if self.battle_result else RED
        result_text = self.font_medium.render(
            f"{'Victory!' if self.battle_result else 'Defeat...'} (Target: {self.current_enemy.target})",
            True, result_color
        )
        self.screen.blit(result_text, (SCREEN_WIDTH // 2 - result_text.get_width() // 2, 250))
        
        # Show instruction
        instruction = self.font_small.render("Press Z to continue", True, WHITE)
        self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
    
    def draw_text_screen(self):
        """Draw text screen"""
        # Show message
        message_text = self.font_medium.render(self.message, True, WHITE)
        self.screen.blit(message_text, (SCREEN_WIDTH // 2 - message_text.get_width() // 2, 200))
        
        # Show sub-message (if any)
        if self.sub_message:
            sub_text = self.font_small.render(self.sub_message, True, WHITE)
            self.screen.blit(sub_text, (SCREEN_WIDTH // 2 - sub_text.get_width() // 2, 250))
        
        # Show instruction
        instruction = self.font_small.render("Press Z to skip", True, WHITE)
        self.screen.blit(instruction, (SCREEN_WIDTH // 2 - instruction.get_width() // 2, 350))
    
    def draw_ending(self):
        """Draw ending screen"""
        title = self.font_large.render("Game Clear!", True, GREEN)
        message1 = self.font_medium.render("You found the legendary treasure!", True, WHITE)
        message2 = self.font_medium.render("You will be known as a hero...", True, WHITE)
        
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))
        self.screen.blit(message1, (SCREEN_WIDTH // 2 - message1.get_width() // 2, 220))
        self.screen.blit(message2, (SCREEN_WIDTH // 2 - message2.get_width() // 2, 270))
    
    def draw_game_over(self):
        """Draw game over screen"""
        title = self.font_large.render("Game Over", True, RED)
        message = self.font_medium.render("You were lost in the darkness...", True, WHITE)
        
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))
        self.screen.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, 220))
    
    def start_game(self):
        """Start game"""
        self.state = self.STATE_EVENT
        self.player = Player()
        self.phase = 1
        self.next_event()
    
    def next_event(self):
        """Set up next event"""
        self.current_event = self.event_manager.get_event(self.phase)
        self.choice = 0  # Reset choice
        
        if self.current_event == 2:  # Battle event
            self.start_battle()
        elif self.current_event == 3:  # Rest event
            self.show_message("You rested in a quiet area. Nothing happens.")
        elif self.current_event == 4:  # Water event
            self.state = self.STATE_EVENT
        elif self.current_event == 5:  # Chest event
            self.state = self.STATE_EVENT
        else:
            self.state = self.STATE_EVENT
    
    def start_battle(self):
        """Start battle"""
        self.current_enemy = self.event_manager.get_enemy(self.phase)
        self.dice_result = random.randint(1, 10)
        self.battle_result = self.dice_result <= self.current_enemy.target
        self.state = self.STATE_BATTLE
    
    def show_message(self, message: str, sub_message: str = ""):
        """Show message"""
        self.message = message
        self.sub_message = sub_message
        self.state = self.STATE_TEXT
        self.message_timer = 0
    
    def game_over(self):
        """Game over processing"""
        self.state = self.STATE_GAME_OVER


if __name__ == "__main__":
    game = Game()
    game.run()