from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time

# Difficulty levels
EASY = 0
MEDIUM = 1
HARD = 2

difficulty = EASY
player_pos = [-250, -250, 30]
player_angle = 0
player_health = 100
player_coins = 0
bunker_uses = 0
bunker_time = 0
in_bunker = False
obstacles = []
coins = []
zombies = []
start_time = time.time()
game_state = GAME_PLAYING
kills = 0
normal_zombie_count = 6

RED = (1, 0, 0)
ZOMBIE_GREEN = (0.263, 0.424, 0.243)
BLUE = (0, 0, 1)
GRAY = (0.5, 0.5, 0.5)
GOLD = (1, 0.84, 0)
GREEN = (0, 1, 0)

class GameObject:
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z
        self.active = True

class Zombie(GameObject):
    def __init__(self, x, y):
        super().__init__(x, y, 30)
        self.health = 1 if random.random() < 0.5 else 3
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
                
            if distance_to_bunker(self.x, self.y) < 60:
                if in_bunker:
                    self.respawn_random()
    
    def respawn_random(self):
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

def spawn_zombie_far_from_bunker():
    while True:
        x = random.randint(-290, 290)
        y = random.randint(-290, 290)
        if distance_to_bunker(x, y) > 150:
            zombies.append(Zombie(x, y))
            break

def distance_to_bunker(x, y):
    return math.sqrt((x + 250)**2 + (y - 250)**2)

def respawn_coin():
    max_attempts = 50
    attempts = 0
    
    while attempts < max_attempts:
        x = random.randint(-280, 280)
        y = random.randint(-280, 280)
        
        valid = True
        for obs in obstacles:
            if math.sqrt((x - obs.x)**2 + (y - obs.y)**2) < 60:
                valid = False
                break
        player_distance = math.sqrt((x - player_pos[0])**2 + (y - player_pos[1])**2)
        
        if distance_to_bunker(x, y) > 80 and valid and player_distance > 50:
            coins.append(GameObject(x, y, 10))
            break
        
        attempts += 1

def check_win_condition():
    global game_state, kills
    if difficulty == EASY and player_coins >= 6:
        game_state = GAME_WIN
    elif difficulty == MEDIUM and player_coins >= 10:
        game_state = GAME_WIN
    elif difficulty == HARD and player_coins >= 10 and kills >= 10:
        game_state = GAME_WIN

def check_game_over():
    global game_state, bunker_time, in_bunker
    
    current_time = time.time()
    
    if player_health <= 0:
        game_state = GAME_OVER
        
    if current_time - start_time > game_duration:
        game_state = GAME_OVER
        
    if in_bunker and bunker_time >= 15:
        game_state = GAME_OVER

def update_game():
    global bunker_time, in_bunker
    
    if game_state != GAME_PLAYING:
        return
    
    current_time = time.time()
    dt = current_time - last_update_time
    
    if in_bunker:
        bunker_time += dt
    
    for zombie in zombies:
        zombie.update()
    
    zombies[:] = [z for z in zombies if z.active]

def draw_zombie(zombie):
    glPushMatrix()
    glTranslatef(zombie.x, zombie.y, zombie.z+15)
    
    glColor3fv(ZOMBIE_GREEN)
    draw_cube(12, 12, 12)
    
    glTranslatef(0, 0, -20)
    if zombie.health == 1:
        glColor3fv(BLUE)
        draw_cube(17, 17, 17)
    else:
        glColor3fv(RED)
        draw_cube(25, 25, 25)
    
    glColor3fv(ZOMBIE_GREEN)
    glTranslatef(-12, 0, 0)
    draw_cube(8, 8, 20)
    glTranslatef(24, 0, 0)
    draw_cube(8, 8, 20)
    glTranslatef(-18, 0, -20)
    draw_cube(8, 8,15)
    glTranslatef(12, 0, 0)
    draw_cube(8, 8, 15)
    
    glPopMatrix()

def draw_coin(coin):
    glPushMatrix()
    glTranslatef(coin.x, coin.y, coin.z)
    glColor3f(1.0, 0.84, 0.0)
    gluSphere(gluNewQuadric(), 8, 20, 20)
    glPopMatrix()

def draw_bunker():
    glPushMatrix()
    glTranslatef(-250, 250, 0)
    if in_bunker:
        glColor3f(0, 1, 0)
    else:
        glColor3fv(GRAY)
    draw_cube(80, 80, 40)
    glPopMatrix()

def draw_cube(size_x=1, size_y=1, size_z=1):
    glPushMatrix()
    glScalef(size_x, size_y, size_z)
    glutSolidCube(1)
    glPopMatrix()

def specialKeyListener(key, x, y):
    global player_pos, player_angle, in_bunker, bunker_uses, bunker_time, player_coins
    
    if game_state != GAME_PLAYING:
        return
    
    old_x, old_y = player_pos[0], player_pos[1]
    
    if key == GLUT_KEY_UP:
        new_x = player_pos[0] + math.cos(math.radians(player_angle)) * 20
        new_y = player_pos[1] + math.sin(math.radians(player_angle)) * 20
        
        can_move = True
        for obs in obstacles:
            if math.sqrt((new_x - obs.x)**2 + (new_y - obs.y)**2) < 35:
                can_move = False
                break
        
        safe_distance = 20
        if (new_x > 300 - safe_distance or new_x < -300 + safe_distance or
            new_y > 300 - safe_distance or new_y < -300 + safe_distance):
            can_move = False
        
        if new_x < -290 or new_x > 290 or new_y < -290 or new_y > 290:
            can_move = False
        
        if can_move:
            player_pos[0] = new_x
            player_pos[1] = new_y
    
    elif key == GLUT_KEY_DOWN:
        new_x = player_pos[0] - math.cos(math.radians(player_angle)) * 20
        new_y = player_pos[1] - math.sin(math.radians(player_angle)) * 20
        
        can_move = True
        for obs in obstacles:
            if math.sqrt((new_x - obs.x)**2 + (new_y - obs.y)**2) < 35:
                can_move = False
                break
        
        safe_distance = 20
        if (new_x > 300 - safe_distance or new_x < -300 + safe_distance or
            new_y > 300 - safe_distance or new_y < -300 + safe_distance):
            can_move = False
        
        if new_x < -290 or new_x > 290 or new_y < -290 or new_y > 290:
            can_move = False
        
        if can_move:
            player_pos[0] = new_x
            player_pos[1] = new_y
    
    elif key == GLUT_KEY_LEFT:
        player_angle += 90
        new_x = player_pos[0] + math.cos(math.radians(player_angle)) * 20
        new_y = player_pos[1] + math.sin(math.radians(player_angle)) * 20
        
        can_move = True
        for obs in obstacles:
            if math.sqrt((new_x - obs.x)**2 + (new_y - obs.y)**2) < 35:
                can_move = False
                break
        
        safe_distance = 20
        if (new_x > 300 - safe_distance or new_x < -300 + safe_distance or
            new_y > 300 - safe_distance or new_y < -300 + safe_distance):
            can_move = False
        
        if new_x < -290 or new_x > 290 or new_y < -290 or new_y > 290:
            can_move = False
        
        if can_move:
            player_pos[0] = new_x
            player_pos[1] = new_y
            
    elif key == GLUT_KEY_RIGHT:
        player_angle -= 90
        new_x = player_pos[0] + math.cos(math.radians(player_angle)) * 20
        new_y = player_pos[1] + math.sin(math.radians(player_angle)) * 20
        
        can_move = True
        for obs in obstacles:
            if math.sqrt((new_x - obs.x)**2 + (new_y - obs.y)**2) < 35:
                can_move = False
                break
        
        safe_distance = 20
        if (new_x > 300 - safe_distance or new_x < -300 + safe_distance or
            new_y > 300 - safe_distance or new_y < -300 + safe_distance):
            can_move = False
        
        if new_x < -290 or new_x > 290 or new_y < -290 or new_y > 290:
            can_move = False
        
        if can_move:
            player_pos[0] = new_x
            player_pos[1] = new_y
    
    bunker_distance = distance_to_bunker(player_pos[0], player_pos[1])
    if bunker_distance < 60:
        max_uses = 5 if difficulty == EASY else (3 if difficulty == MEDIUM else 2)
        if not in_bunker and bunker_uses < max_uses:
            in_bunker = True
            bunker_time = 0
            bunker_uses += 1
    else:
        if in_bunker:
            in_bunker = False
            bunker_time = 0
    
    for coin in coins:
        if coin.active:
            distance = math.sqrt((player_pos[0] - coin.x)**2 + (player_pos[1] - coin.y)**2)
            if distance < 25:
                coin.active = False
                player_coins += 1
                respawn_coin()