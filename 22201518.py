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
start_time = 0
player_pos = [-250, -250, 30]
player_angle = 0
player_health = 100
player_coins = 0
bunker_uses = 0
bunker_time = 0
in_bunker = False
kills = 0
obstacles = []
coins = []
zombies = []
bullets = []
cheat_active = False
cheat_start_time = 0
cheat_time = 0
last_update_time = 0
normal_zombie_count = 6

GRAY = (0.5, 0.5, 0.5)
BROWN = (0.6, 0.4, 0.2)
PURPLE = (.5,0,1)
SKIN = (1, 0.8, 0.6)
YELLOW = (1, 1, 0)
GREEN = (0, 1, 0)
RED = (1, 0, 0)

class GameObject:
    def __init__(self, x, y, z=0):
        self.x = x
        self.y = y
        self.z = z
        self.active = True

class Bullet(GameObject):
    def __init__(self, x, y, angle):
        super().__init__(x, y, 15)
        self.angle = angle
        self.speed = 700
        self.lifetime = 3.0
        self.created = time.time()
        
    def update(self, dt):
        global kills
        self.x += math.cos(math.radians(self.angle)) * self.speed * dt
        self.y += math.sin(math.radians(self.angle)) * self.speed * dt
        
        if time.time() - self.created > self.lifetime:
            self.active = False
            
        for zombie in zombies:
            if zombie.active:
                distance = math.sqrt((self.x - zombie.x)**2 + (self.y - zombie.y)**2)
                if distance < 30:
                    zombie.health -= 1
                    if zombie.health <= 0:
                        zombie.active = False
                        kills += 1
                        spawn_zombie_far_from_bunker()
                    self.active = False
                    break

def init_game():
    global obstacles, coins, zombies, bullets, player_pos, player_health, player_coins
    global bunker_uses, start_time, last_wave_check_time, player_angle, in_bunker, bunker_time
    global cheat_active, kills, cheat_time, last_update_time
    global normal_zombie_count
    
    obstacles.clear()
    coins.clear()
    zombies.clear()
    bullets.clear()
    
    player_pos = [-250, -250, 30]
    player_health = 100
    player_coins = 0
    player_angle = 0
    bunker_uses = 0
    bunker_time = 0
    in_bunker = False
    start_time = time.time()
    last_wave_check_time = time.time()
    kills = 0
    cheat_time = 0
    last_update_time = 0
    
    cheat_active = False
    
    if difficulty == EASY:
        max_bunker_uses = 5
        num_obstacles = 6
        normal_zombie_count = 6
    elif difficulty == MEDIUM:
        max_bunker_uses = 3
        num_obstacles = 10
        normal_zombie_count = 10
    else:
        max_bunker_uses = 2
        num_obstacles = 14
        normal_zombie_count = 14
    
    for i in range(num_obstacles):
        while True:
            x = random.randint(-230, 230)
            y = random.randint(-230, 230)
            if distance_to_bunker(x, y) > 100 and math.sqrt((x+250)**2 + (y+250)**2) > 80:
                too_close = False
                for obs in obstacles:
                    dist = math.sqrt((x - obs.x)**2 + (y - obs.y)**2)
                    if dist < 100:
                        too_close = True
                        break
                if not too_close:
                    obstacles.append(GameObject(x, y, 0))
                    break
    
    for i in range(3):
        while True:
            x = random.randint(-280, 280)
            y = random.randint(-280, 280)
            valid = True
            for obs in obstacles:
                if math.sqrt((x - obs.x)**2 + (y - obs.y)**2) < 60:
                    valid = False
                    break
            if distance_to_bunker(x, y) > 80 and valid:
                coins.append(GameObject(x, y, 10))
                break
    
    for i in range(normal_zombie_count):
        spawn_zombie_far_from_bunker()

def distance_to_bunker(x, y):
    return math.sqrt((x + 250)**2 + (y - 250)**2)

def damage_player(amount):
    global player_health, game_state
    player_health -= amount
    if player_health <= 0:
        player_health = 0
        game_state = GAME_OVER

def update_game():
    global cheat_active, cheat_time, last_update_time
    
    if game_state != GAME_PLAYING:
        return
    
    current_time = time.time()
    dt = current_time - last_update_time
    last_update_time = current_time

    if cheat_active:
        cheat_time += dt
        if cheat_time > 20:
            cheat_active = False
    
    for bullet in bullets:
        bullet.update(dt)
    
    bullets[:] = [b for b in bullets if b.active]

def draw_player():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(player_angle, 0, 0, 1)
    
    glColor3fv(PURPLE)
    draw_cube(20, 30, 40)
    
    glTranslatef(0, 0, 30)
    glColor3fv(SKIN)
    draw_cube(15, 15, 15)
    
    glTranslatef(15, 0, -10)
    glColor3fv(YELLOW)
    glRotatef(90, 0, 1, 0)
    draw_cylinder(3, 3, 25)
    
    glPopMatrix()

def draw_obstacle(obs):
    glPushMatrix()
    glTranslatef(obs.x, obs.y, obs.z)
    
    glColor3fv(GRAY)
    draw_cube(40, 20, 60)
    
    glTranslatef(0, 0, 35)
    glPushMatrix()
    glScalef(20, 5, 5)
    glutSolidCube(1)
    glPopMatrix()
    glPushMatrix()
    glScalef(5, 5, 15)
    glutSolidCube(1)
    glPopMatrix()
    
    glPopMatrix()

def draw_ground():
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.1, 0.05)
    glVertex3f(-250, -250, 1)
    glVertex3f(250, -250, 1)
    glVertex3f(250, 250, 1)
    glVertex3f(-250, 250, 1)
    glEnd()
    glBegin(GL_QUADS)
    glColor3f(0.15, 0.3, 0.23)
    glVertex3f(-300, -300, 0)
    glVertex3f(300, -300, 0)
    glVertex3f(300, 300, 0)
    glVertex3f(-300, 300, 0)
    glEnd()

    wall_height = 40
    grill_height = 20
    grill_spacing = 40
    grill_width = 5

    glBegin(GL_QUADS)

    glColor3f(0.2, 0.2, 0.2)
    glVertex3f(300, -300, 0)
    glVertex3f(300, 300, 0)
    glVertex3f(300, 300, wall_height)
    glVertex3f(300, -300, wall_height)
    for y in range(-280, 301, grill_spacing):
        glColor3f(0.0, 0.0, 0.0)
        glVertex3f(300 - grill_width/2, y, wall_height)
        glVertex3f(300 + grill_width/2, y, wall_height)
        glVertex3f(300 + grill_width/2, y, wall_height + grill_height)
        glVertex3f(300 - grill_width/2, y, wall_height + grill_height)
    glColor3f(0.2, 0.2, 0.2)
    glVertex3f(-300, -300, 0)
    glVertex3f(-300, 300, 0)
    glVertex3f(-300, 300, wall_height)
    glVertex3f(-300, -300, wall_height)
    for y in range(-280, 301, grill_spacing):
        glColor3f(0.0, 0.0, 0.0)
        glVertex3f(-300 - grill_width/2, y, wall_height)
        glVertex3f(-300 + grill_width/2, y, wall_height)
        glVertex3f(-300 + grill_width/2, y, wall_height + grill_height)
        glVertex3f(-300 - grill_width/2, y, wall_height + grill_height)
    glColor3f(0.2, 0.2, 0.2)
    glVertex3f(-300, 300, 0)
    glVertex3f(300, 300, 0)
    glVertex3f(300, 300, wall_height)
    glVertex3f(-300, 300, wall_height)
    for x in range(-280, 301, grill_spacing):
        glColor3f(0.0, 0.0, 0.0)
        glVertex3f(x, 300 - grill_width/2, wall_height)
        glVertex3f(x, 300 + grill_width/2, wall_height)
        glVertex3f(x, 300 + grill_width/2, wall_height + grill_height)
        glVertex3f(x, 300 - grill_width/2, wall_height + grill_height)
    glColor3f(0.2, 0.2, 0.2)
    glVertex3f(-300, -300, 0)
    glVertex3f(300, -300, 0)
    glVertex3f(300, -300, wall_height)
    glVertex3f(-300, -300, wall_height)
    for x in range(-280, 301, grill_spacing):
        glColor3f(0.0, 0.0, 0.0)
        glVertex3f(x, -300 - grill_width/2, wall_height)
        glVertex3f(x, -300 + grill_width/2, wall_height)
        glVertex3f(x, -300 + grill_width/2, wall_height + grill_height)
        glVertex3f(x, -300 - grill_width/2, wall_height + grill_height)
    glEnd()

def draw_health_bar():
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    health_width = (200 / 100) * player_health
    if player_health > 70:
        glColor3f(0, 1, 0)
    elif player_health > 20:
        glColor3f(1, 1, 0)
    else:
        glColor3f(1, 0, 0)
    
    glBegin(GL_QUADS)
    glVertex2f(10, 740)
    glVertex2f(10 + health_width, 740)
    glVertex2f(10 + health_width, 760)
    glVertex2f(10, 760)
    glEnd()
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_hud():
    draw_health_bar()
    draw_text(10, 770, f"Health: {player_health}%")
    draw_text(10, 720, f"Tired of fighting? Press V for an escape")

def draw_cube(size_x=1, size_y=1, size_z=1):
    glPushMatrix()
    glScalef(size_x, size_y, size_z)
    glutSolidCube(1)
    glPopMatrix()

def draw_cylinder(base_radius, top_radius, height):
    gluCylinder(gluNewQuadric(), base_radius, top_radius, height, 10, 10)

def draw_bullet(bullet):
    glPushMatrix()
    glTranslatef(bullet.x, bullet.y, bullet.z)
    glColor3fv(YELLOW)
    draw_cube(3, 3, 6)
    glPopMatrix()

def keyboardListener(key, x, y):
    global cheat_active, cheat_start_time, cheat_time, player_coins, player_health
    
    if game_state == GAME_PLAYING:
        if key == b'c':
            if player_coins >= 2:
                player_coins -= 2
                player_health = min(100, player_health + 10)
        
        elif key == b'v':
            if not cheat_active:
                cheat_active = True
                cheat_start_time = time.time()

def mouseListener(button, state, x, y):
    if game_state == GAME_PLAYING and button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        
        gun_forward = 15
        
        gun_x = player_pos[0] + gun_forward * math.cos(math.radians(player_angle))
        gun_y = player_pos[1] + gun_forward * math.sin(math.radians(player_angle))
        gun_z = player_pos[2] + 20
        
        bullet = Bullet(gun_x, gun_y, player_angle)
        bullet.z = gun_z
        bullets.append(bullet)