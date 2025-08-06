import pygame
import sys
import random
import os
import json
import pygame.mixer  # Add pygame.mixer for sound

# Constants
WIN_WIDTH, WIN_HEIGHT = 432, 768
BASE_HEIGHT = 100  # New constant for base height
FLOOR_Y = WIN_HEIGHT - BASE_HEIGHT  # Adjust floor Y position
PIPE_GAP_MIN = 140  # Minimum gap between top and bottom pipes
PIPE_GAP_MAX = 220  # Maximum gap between top and bottom pipes
FPS = 60
PIPE_VELOCITY = 3  # Slightly faster pipe
GRAVITY = 0.8      # Increased gravity for faster falling
FLAP_POWER = -8    # Stronger flap power for more consistent height
MAX_VEL_UP = 7     # Maximum upward velocity
MAX_VEL_DOWN = 10  # Maximum downward velocity
BIRD_SIZE = 30
PIPE_WIDTH = 70
PIPE_SPACING_MIN = 180  # Minimum space between pipes
PIPE_SPACING_MAX = 250  # Maximum space between pipes

def load_assets():
    """Load all game assets"""
    # Load and scale background
    bg = pygame.image.load(os.path.join('assets', 'background.png'))
    bg = pygame.transform.scale(bg, (WIN_WIDTH, WIN_HEIGHT))
    
    # Load and scale bird animation frames
    bird_frames = [
        pygame.transform.scale(pygame.image.load(os.path.join('assets', f'bird-{flap}flap.png')), (BIRD_SIZE, BIRD_SIZE))
        for flap in ['down', 'mid', 'up']
    ]
    
    # Load and scale pipe image to proper height
    pipe_img = pygame.image.load(os.path.join('assets', 'pipe.png'))
    pipe_img = pygame.transform.scale(pipe_img, (PIPE_WIDTH, FLOOR_Y))
    
    # Load and scale base - make it twice the width of the window
    base = pygame.image.load(os.path.join('assets', 'base.png'))
    base = pygame.transform.scale(base, (WIN_WIDTH * 2, BASE_HEIGHT))
    
    return bg, base, bird_frames, pipe_img

def load_sounds():
    """Load all game sounds"""
    pygame.mixer.init()
    # Load sound effects
    sounds = {
        'wing': pygame.mixer.Sound(os.path.join('audio', 'wing.wav')),
        'hit': pygame.mixer.Sound(os.path.join('audio', 'hit.wav')),
        'point': pygame.mixer.Sound(os.path.join('audio', 'point.wav')),
        'die': pygame.mixer.Sound(os.path.join('audio', 'die.wav'))
    }
    
    # Load and set up background music
    pygame.mixer.music.load(os.path.join('audio', 'background.wav'))
    pygame.mixer.music.set_volume(0.3)  # Set music volume to 30%
    
    return sounds

def load_highscore():
    try:
        with open('highscore.json', 'r') as f:
            return json.load(f)['highscore']
    except:
        return 0

def save_highscore(score):
    with open('highscore.json', 'w') as f:
        json.dump({'highscore': score}, f)

class Bird:
    def __init__(self, x, y, frames):
        self.x = x
        self.y = y
        self.vel = 0
        self.tick_count = 0
        self.frames = frames
        self.frame_index = 0
        self.animation_speed = 5  # Change frame every 5 ticks
        self.animation_count = 0

    def flap(self):
        self.vel = FLAP_POWER
        self.tick_count = 0

    def update(self):
        self.tick_count += 1
        
        # Calculate vertical movement
        if self.vel < MAX_VEL_DOWN:
            self.vel += GRAVITY
            
        # Limit upward velocity
        if self.vel < -MAX_VEL_UP:
            self.vel = -MAX_VEL_UP
            
        # Move bird based on velocity
        self.y += self.vel

    def draw(self, surface):
        # Update animation frame
        self.animation_count = (self.animation_count + 1) % self.animation_speed
        if self.animation_count == 0:
            self.frame_index = (self.frame_index + 1) % 3
        
        # Rotate bird based on velocity
        rotation = max(-90, min(self.vel * -3, 30))
        rotated_bird = pygame.transform.rotate(self.frames[self.frame_index], rotation)
        
        # Center the rotated image
        rect = rotated_bird.get_rect(center=(self.x + BIRD_SIZE//2, self.y + BIRD_SIZE//2))
        surface.blit(rotated_bird, rect.topleft)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, BIRD_SIZE, BIRD_SIZE)

class Pipe:
    def __init__(self, x, pipe_img):
        self.x = x
        # Random gap size between pipes
        self.gap_size = random.randint(PIPE_GAP_MIN, PIPE_GAP_MAX)
        
        # Adjust gap_y range to ensure pipes connect with top and bottom
        min_gap_y = 150  # Minimum distance from top
        max_gap_y = FLOOR_Y - 150 - self.gap_size  # Maximum distance, accounting for gap and bottom margin
        self.gap_y = random.randrange(min_gap_y, max_gap_y)
        self.scored = False
        self.PIPE_TOP = pygame.transform.flip(pipe_img, False, True)
        self.PIPE_BOTTOM = pipe_img

    def update(self):
        self.x -= PIPE_VELOCITY

    def draw(self, surface):
        # Draw top pipe (connected to top of screen)
        surface.blit(self.PIPE_TOP, (self.x, self.gap_y - self.PIPE_TOP.get_height()))
        # Draw bottom pipe (connected to floor)
        surface.blit(self.PIPE_BOTTOM, (self.x, self.gap_y + self.gap_size))

    def collide(self, bird):
        bird_rect = bird.get_rect()
        top_pipe = pygame.Rect(self.x, 0, PIPE_WIDTH, self.gap_y)
        bottom_pipe = pygame.Rect(self.x, self.gap_y + self.gap_size, PIPE_WIDTH, 
                                FLOOR_Y - (self.gap_y + self.gap_size))
        return bird_rect.colliderect(top_pipe) or bird_rect.colliderect(bottom_pipe)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont('Arial', 40, bold=True)

    # Load assets and sounds
    bg, base, bird_frames, pipe_img = load_assets()
    sounds = load_sounds()
    pygame.mixer.music.play(-1)  # -1 means loop indefinitely
    
    base_x = 0
    
    def reset_game():
        bird = Bird(100, WIN_HEIGHT // 2, bird_frames)
        pipes = []
        score = 0
        return bird, pipes, score

    bird, pipes, score = reset_game()
    game_state = 'START'
    
    # Add after loading assets
    highscore = load_highscore()

    running = True
    while running:
        clock.tick(FPS)
        screen.blit(bg, (0, 0))
        
        # Draw pipes
        for pipe in pipes:
            pipe.draw(screen)
        
        # Draw and scroll base - modified to stay in frame
        base_x = -((-base_x + PIPE_VELOCITY) % WIN_WIDTH)  # Reversed scrolling logic
        screen.blit(base, (base_x, FLOOR_Y))
        screen.blit(base, (base_x + WIN_WIDTH, FLOOR_Y))
        
        # Draw bird
        bird.draw(screen)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if game_state == 'START':
                    game_state = 'PLAYING'
                    # Initialize with 3 pipes at random spacing
                    pipes = []
                    next_pipe_x = WIN_WIDTH + 100
                    for _ in range(3):
                        pipes.append(Pipe(next_pipe_x, pipe_img))
                        next_pipe_x += random.randint(PIPE_SPACING_MIN, PIPE_SPACING_MAX)
                    bird.vel = 0
                    bird.tick_count = 0
                    bird.flap()
                    sounds['wing'].play()
                elif game_state == 'PLAYING':
                    bird.flap()
                    sounds['wing'].play()
                elif game_state == 'GAME_OVER':
                    # Reset the game when space is pressed after game over
                    bird, pipes, score = reset_game()
                    game_state = 'START'
                    pygame.mixer.music.play(-1)  # Restart music

        if game_state == 'PLAYING':
            bird.update()
            remove_pipes = []
            add_pipe = False
            
            for pipe in pipes:
                pipe.update()
                if pipe.collide(bird):
                    sounds['hit'].play()
                    sounds['die'].play()
                    pygame.mixer.music.stop()  # Stop music on game over
                    game_state = 'GAME_OVER'
                if pipe.x + PIPE_WIDTH < 0:
                    remove_pipes.append(pipe)
                    add_pipe = True
                if not pipe.scored and pipe.x < bird.x:
                    score += 1
                    pipe.scored = True
                    sounds['point'].play()

            for pipe in remove_pipes:
                pipes.remove(pipe)
            if add_pipe:
                last_pipe_x = max(pipe.x for pipe in pipes)
                new_pipe_x = last_pipe_x + random.randint(PIPE_SPACING_MIN, PIPE_SPACING_MAX)
                pipes.append(Pipe(new_pipe_x, pipe_img))

            if bird.y + BIRD_SIZE >= FLOOR_Y or bird.y < 0:
                sounds['hit'].play()
                sounds['die'].play()
                game_state = 'GAME_OVER'

        if game_state == 'START':
            title = font.render('Press SPACE to Start', True, (255, 255, 255))
            best_score = font.render(f'Best: {highscore}', True, (255, 255, 255))
            screen.blit(title, (WIN_WIDTH//2 - title.get_width()//2, WIN_HEIGHT//2 - 50))
            screen.blit(best_score, (WIN_WIDTH//2 - best_score.get_width()//2, WIN_HEIGHT//2 + 50))
            
        # Inside PLAYING state, after updating score
        if score > highscore:
            highscore = score
            save_highscore(highscore)

        if game_state == 'GAME_OVER':
            game_over = font.render('Game Over', True, (255, 255, 255))
            press_space = font.render('Press SPACE to Restart', True, (255, 255, 255))
            screen.blit(game_over, (WIN_WIDTH//2 - game_over.get_width()//2, WIN_HEIGHT//2 - 50))
            screen.blit(press_space, (WIN_WIDTH//2 - press_space.get_width()//2, WIN_HEIGHT//2 + 50))
        
        score_text = font.render(str(score), True, (255, 255, 255))
        screen.blit(score_text, (WIN_WIDTH // 2 - score_text.get_width() // 2, 50))

        pygame.display.update()

    pygame.quit()
    sys.exit()

if __name__ == '__main__':
    main()