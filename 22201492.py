from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

# Game states
COVER_SCREEN = 0
DIFFICULTY_SCREEN = 1
GAME_PLAYING = 2
GAME_OVER = 3
GAME_WIN = 4

# Difficulty levels
EASY = 0
MEDIUM = 1
HARD = 2


game_state = COVER_SCREEN
difficulty = EASY
start_time = 0
game_duration = 90  
camera_pos = [0, -800, 600]
camera_angle_x = 0
camera_angle_y = 0
grid_rotation = 0  


player_pos = [-250, -250, 30]  
player_angle = 0
player_health = 100
player_coins = 0
bunker_uses = 0
bunker_time = 0
kills = 0
in_bunker = False
obstacles = []
coins = []
zombies = []
bullets = []


cheat_active = False
cheat_start_time = 0
cheat_time = 0
last_update_time = 0

last_wave_check_time = 0
wave_active = False
normal_zombie_count = 6  


RED = (1, 0, 0)
ZOMBIE_GREEN = (0.263, 0.424, 0.243)
GREEN = (0, 1, 0)
BLUE = (0, 0, 1)
YELLOW = (1, 1, 0)
WHITE = (1, 1, 1)
BLACK = (0, 0, 0)
GRAY = (0.5, 0.5, 0.5)
BROWN = (0.6, 0.4, 0.2)
SKIN = (1, 0.8, 0.6)
GOLD = (1, 0.84, 0)
PURPLE = (.5,0,1)

class GameObject:
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z
        self.active = True

class Zombie(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 30)
        self.health = 1 if random.random() < 0.5 else 2  
        self.speed = 50 if self.health == 1 else 25  
        self.last_move = time.time()
        
    def update(self):
        if not self.active or cheat_active:
            return
            
        current_time = time.time()
        if current_time - self.last_move > 0.1:  
            
            dx = player_pos[0] - self.x
            dy = player_pos[1] - self.y
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 5:
                self.x += (dx/distance) * self.speed * 0.05
                self.y += (dy/distance) * self.speed * 0.05
            self.last_move = current_time
            
            if distance < 40 and not in_bunker:
                damage_player(10) 
                self.respawn_random()
                
            # Check collision with bunker
            if distance_to_bunker(self.x, self.y) < 60:
                if in_bunker:
                    self.respawn_random()
    
    def respawn_random(self):
        """Respawn zombie at random location far from player, bunker, and other zombies"""
        max_attempts = 100
        attempts = 0
        
        while attempts < max_attempts:
            x = random.randint(-290, 290)
            y = random.randint(-290, 290)
            
            player_distance = math.sqrt((x - player_pos[0])**2 + (y - player_pos[1])**2)
            bunker_distance = distance_to_bunker(x, y)
            
            not_in_bunker = not (x >= -290 and x <= -210 and y >= 210 and y <= 290)
            
            overlap = False
            for other_zombie in zombies:
                if other_zombie != self and other_zombie.active:
                    dx = other_zombie.x - x
                    dy = other_zombie.y - y
                    if dx*dx + dy*dy < 3600:  
                        overlap = True
                        break
            #zombie should respawn far from player, bunker and other zombies
            if player_distance > 100 and bunker_distance > 200 and not_in_bunker and not overlap:
                self.x = x
                self.y = y
                break
            
            attempts += 1

        if attempts >= max_attempts:
            safe_positions = [
                (200, 200),   
                (200, -200),    
                (-200, -200), 
                (0, -290),    
                (290, 0)      
            ]
            x, y = random.choice(safe_positions)
            self.x = x
            self.y = y

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    if game_state == GAME_PLAYING:
        glColor3f(1, 1, 1) 
    else:
        glColor3f(1, 0, 0.2)  
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glRasterPos2f(x, y)
    for ch in text:
        glutBitmapCharacter(font, ord(ch))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def update_game():

    global last_wave_check_time, wave_active, cheat_active, bunker_time, in_bunker, cheat_time, last_update_time
    
    if game_state != GAME_PLAYING:
        return
    
    current_time = time.time()
    if last_update_time == 0:
        last_update_time = current_time
        return
    
    dt = current_time - last_update_time  
    last_update_time = current_time

    # cheat mode
    if cheat_active:
        cheat_time = current_time - cheat_start_time 
        if cheat_time > 20:
            cheat_active = False
    
    game_time = current_time - start_time
    

    wave_start_times = [30, 60]  # Wave starts 30s and 60s
    
    current_wave = False
    for wave_start in wave_start_times:
        if wave_start <= game_time <= wave_start + 10: 
            current_wave = True
            break
    

    if current_wave and not wave_active:
        wave_active = True
        active_zombie_count = len([z for z in zombies if z.active])
        for i in range(active_zombie_count):
            spawn_zombie_far_from_bunker()
    elif not current_wave and wave_active:
        wave_active = False
    
    # Update bunker time
    if in_bunker:
        bunker_time += dt

    # Update cheat timer
    if cheat_active:
        cheat_time += dt
    
    # Update zombies
    for zombie in zombies:
        zombie.update()
    
    # Update bullets
    for bullet in bullets:
        bullet.update(dt)
    
    zombies[:] = [z for z in zombies if z.active]
    bullets[:] = [b for b in bullets if b.active]
    
 
    active_zombie_count = len([z for z in zombies if z.active])
    if active_zombie_count < normal_zombie_count:
        zombies_to_spawn = normal_zombie_count - active_zombie_count
        for _ in range(zombies_to_spawn):
            spawn_zombie_far_from_bunker()
    
    check_win_condition()
    check_game_over()


def spawn_zombie_far_from_bunker():
    while len(zombies)<=normal_zombie_count or wave_active:
        x = random.randint(-290, 290)
        y = random.randint(-290, 290)
        if distance_to_bunker(x, y) > 150 and distance_to_player(x,y)>100:
            zombies.append(Zombie(x, y))
            break

def distance_to_bunker(x, y):

    return math.sqrt((x + 250)**2 + (y - 250)**2) 

def distance_to_player(x,y):
    
    dx = x - player_pos[0]
    dy = y - player_pos[1]
        
    return math.sqrt(dx * dx + dy * dy)

def check_game_over():
    global game_state, bunker_time, in_bunker
    
    current_time = time.time()
    
    if player_health <= 0:
        game_state = GAME_OVER
        
    if current_time - start_time > game_duration:
        game_state = GAME_OVER
        
    if in_bunker and bunker_time >= 15:
        game_state = GAME_OVER

def check_win_condition():
    global game_state, kills
    if difficulty == EASY and player_coins >= 6:
        game_state = GAME_WIN
    elif difficulty == MEDIUM and player_coins >= 10:
        game_state = GAME_WIN
    elif difficulty == HARD and player_coins >= 10 and kills >= 10:
        game_state = GAME_WIN

def draw_hud():
 
    #Health
    draw_health_bar()
    draw_text(10, 770, f"Health: {player_health}%")
    draw_text(10, 720, f"Tired of fighting? Press V for an escape")
    
    time_left = max(0, game_duration - (time.time() - start_time))
    draw_text(750, 770, f"Coins: {player_coins}")
    draw_text(750, 750, f"Kills: {kills}")
    draw_text(750, 730, f"Time: {int(time_left)}")
    
    # Bunker uses
    max_uses = 5 if difficulty == EASY else (3 if difficulty == MEDIUM else 2)
    draw_text(750, 710, f"Remaining bunker entries: {max_uses - bunker_uses}")

    # Bunker timer
    if in_bunker:
        bunker_time_left = max(0, 15 - bunker_time)
        
        
        if bunker_time_left <= 3:  
            timer_color = (1, 0, 0)
        elif bunker_time_left <= 8:  
            timer_color = (1, 1, 0)
        else:  
            timer_color = (0, 1, 0)
        
        
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 1000, 0, 800)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        
        glColor3fv(timer_color)
        glRasterPos2f(750, 690)
        timer_text = f"Bunker Timer: {bunker_time_left:.0f}"
        for ch in timer_text:
            glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(ch))
        
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
    
    if cheat_active:
        draw_text(400, 750, "CHEAT MODE ACTIVE!")
        cheat_time_left = max(0, 20 - cheat_time)
        draw_text(440, 710, f"Cheat Timer: {cheat_time_left:.0f}")

def setupCamera():
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, 1.25, 0.1, 2000)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    x, y, z = camera_pos
    gluLookAt(x, y, z, 0, 0, 0, 0, 0, 1)

def keyboardListener(key, x, y):
 
    global game_state, difficulty, player_angle, cheat_active, cheat_start_time,cheat_time
    global player_coins, player_health, in_bunker, bunker_uses, bunker_time, grid_rotation 
    
    # Cover screen
    if game_state == COVER_SCREEN and (key == b'\r' or key == b' '):
        game_state = DIFFICULTY_SCREEN
    
    # Difficulty selection
    elif game_state == DIFFICULTY_SCREEN:
        if key == b'1':
            difficulty = EASY
            init_game()
            game_state = GAME_PLAYING
        elif key == b'2':
            difficulty = MEDIUM
            init_game()
            game_state = GAME_PLAYING
        elif key == b'3':
            difficulty = HARD
            init_game()
            game_state = GAME_PLAYING
    
    # restart
    elif (game_state == GAME_OVER or game_state == GAME_WIN) and key == b'r':
        init_game()
        game_state = GAME_PLAYING
    
    #  go back to start
    elif (game_state == GAME_OVER or game_state == GAME_WIN) and key == b'\r':
        init_game()
        game_state = COVER_SCREEN
    
    # Game 
    elif game_state == GAME_PLAYING:
        
        if key == b'r':
            init_game()
            game_state = GAME_PLAYING
        # Rotate player
        elif key == b'a':
            player_angle += 10
        elif key == b'd':
            player_angle -= 10
            
        # Camera controls
        elif key == b'w' and camera_pos[2]<=800:
            camera_pos[2] += 20
        elif key == b's' and camera_pos[2]>=200:
            camera_pos[2] -= 20
        
        elif key == b'=': 
            grid_rotation -= 2 
            if grid_rotation >= 360:
                grid_rotation -= 360
            
        elif key == b'-': 
            # Rotate grid counterclockwise  
            grid_rotation += 2  
            if grid_rotation <= -360:
                grid_rotation += 360
            
        # Redeem coins
        elif key == b'c':
            if player_coins >= 2:
                player_coins -= 2
                player_health = min(100, player_health + 10)
            
        # Cheat mode
        elif key == b'v':
            if not cheat_active:
                cheat_active = True
                cheat_start_time = time.time()

def showScreen():
    glEnable(GL_DEPTH_TEST)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 1000, 800)
    
    if game_state == COVER_SCREEN:
        draw_cover_screen()
    elif game_state == DIFFICULTY_SCREEN:
        draw_difficulty_screen()
    elif game_state == GAME_OVER:
        draw_game_over_screen()
    elif game_state == GAME_WIN:
        draw_game_win_screen()
    elif game_state == GAME_PLAYING:
        setupCamera()
    
        glRotatef(grid_rotation, 0.0, 0.0, 1.0)  

        draw_ground()
        draw_bunker()
        
        draw_player()
        
        for zombie in zombies:
            if zombie.active:
                draw_zombie(zombie)
        
        for obs in obstacles:
            draw_obstacle(obs)
            
        for coin in coins:
            if coin.active:
                draw_coin(coin)
                
        for bullet in bullets:
            draw_bullet(bullet)
        
        draw_hud()
    
    glutSwapBuffers()

def idle():

    update_game()
    glutPostRedisplay()