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
        
        # Check lifetime
        if time.time() - self.created > self.lifetime:
            self.active = False
            
        # Check collision with zombies
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
    global cheat_active, wave_active, kills, cheat_time, grid_rotation, last_update_time
    global normal_zombie_count
    
    obstacles.clear()
    coins.clear()
    zombies.clear()
    bullets.clear()
    
    # Reset 
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
    grid_rotation = 0
    camera_pos[2] = 600
    last_update_time = 0
    

    cheat_active = False
    wave_active = False
    
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
    
    # Create obstacles
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
    
    # Create coins
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
    
    # Create zombies
    for i in range(normal_zombie_count):
        spawn_zombie_far_from_bunker()

def spawn_zombie_far_from_bunker():
    while True:
        x = random.randint(-290, 290)
        y = random.randint(-290, 290)
        if distance_to_bunker(x, y) > 150: 
            zombies.append(Zombie(x, y))
            break

def distance_to_bunker(x, y):

    return math.sqrt((x + 250)**2 + (y - 250)**2) 

def damage_player(amount):
    global player_health, game_state
    player_health -= amount
    if player_health <= 0:
        player_health = 0
        game_state = GAME_OVER

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
    

    wave_start_times = [30, 60]  # Wave starts at 30s and 60s
    
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

#draw background
def draw_dead_face(x, y, size=100):

    head_size = size
    eye_size = head_size * 0.2
    cross_thickness = eye_size * 0.3
    mouth_width = head_size * 0.5
    mouth_height = head_size * 0.2
    mouth_thickness = 0.2 * mouth_height

    # Draw head 
    glColor3f(0.7, 0.7, 0.7)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + head_size, y)
    glVertex2f(x + head_size, y + head_size)
    glVertex2f(x, y + head_size)
    glEnd()

    # Draw eyes 
    glColor3f(1.0, 0.0, 0.0)
    # Left eye vertical
    glBegin(GL_QUADS)
    glVertex2f(x + head_size * 0.25 - cross_thickness/2+10, y + head_size * 0.7)
    glVertex2f(x + head_size * 0.25 + cross_thickness/2+10, y + head_size * 0.7)
    glVertex2f(x + head_size * 0.25 + cross_thickness/2+10, y + head_size * 0.85)
    glVertex2f(x + head_size * 0.25 - cross_thickness/2+10, y + head_size * 0.85)
    glEnd()
    # Left eye horizontal
    glBegin(GL_QUADS)
    glVertex2f(x + head_size * 0.15+10, y + head_size * 0.775 - cross_thickness/2)
    glVertex2f(x + head_size * 0.35+10, y + head_size * 0.775 - cross_thickness/2)
    glVertex2f(x + head_size * 0.35+10, y + head_size * 0.775 + cross_thickness/2)
    glVertex2f(x + head_size * 0.15+10, y + head_size * 0.775 + cross_thickness/2)
    glEnd()

    # Right eye vertical
    glBegin(GL_QUADS)
    glVertex2f(x + head_size * 0.65 - cross_thickness/2, y + head_size * 0.7)
    glVertex2f(x + head_size * 0.65 + cross_thickness/2, y + head_size * 0.7)
    glVertex2f(x + head_size * 0.65 + cross_thickness/2, y + head_size * 0.85)
    glVertex2f(x + head_size * 0.65 - cross_thickness/2, y + head_size * 0.85)
    glEnd()
    # Right eye horizontal
    glBegin(GL_QUADS)
    glVertex2f(x + head_size * 0.55, y + head_size * 0.775 - cross_thickness/2)
    glVertex2f(x + head_size * 0.75, y + head_size * 0.775 - cross_thickness/2)
    glVertex2f(x + head_size * 0.75, y + head_size * 0.775 + cross_thickness/2)
    glVertex2f(x + head_size * 0.55, y + head_size * 0.775 + cross_thickness/2)
    glEnd()

    # Draw mouth
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(x + head_size*0.25, y + head_size*0.2)
    glVertex2f(x + head_size*0.75, y + head_size*0.2)
    glVertex2f(x + head_size*0.75, y + head_size*0.35)
    glVertex2f(x + head_size*0.25, y + head_size*0.35)
    glEnd()

def draw_gravestone_2d(x, y, width=120, height=180):
    # Gravestone
    glColor3f(0.5, 0.5, 0.5) 
    glBegin(GL_QUADS)
    glVertex2f(x - width // 2, y)
    glVertex2f(x + width // 2, y)
    glVertex2f(x + width // 2, y + height)
    glVertex2f(x - width // 2, y + height)
    glEnd()

    # Cross
    #  vertical bar
    glColor3f(0.3, 0.3, 0.3)
    glBegin(GL_QUADS)
    glVertex2f(x - 10, y + height)
    glVertex2f(x + 10, y + height)
    glVertex2f(x + 10, y + height + 60)
    glVertex2f(x - 10, y + height + 60)
    glEnd()

    # Cross 
    # horizontal bar
    glBegin(GL_QUADS)
    glVertex2f(x - 30, y + height + 30)
    glVertex2f(x + 30, y + height + 30)
    glVertex2f(x + 30, y + height + 50)
    glVertex2f(x - 30, y + height + 50)
    glEnd()

def draw_zombie_2d(x, y, scale=1.0):
    body_w, body_h = 30 * scale, 60 * scale
    head_size = 30 * scale
    arm_w, arm_h = 40 * scale, 10 * scale
    eye_size = 5 * scale

    # Body 
    if x==350 or x==650:
        glColor3f(1, 0, 0)
    else:
        glColor3f(0, 0, 1)
    glBegin(GL_QUADS)
    glVertex2f(x - body_w / 2, y)
    glVertex2f(x + body_w / 2, y)
    glVertex2f(x + body_w / 2, y + body_h)
    glVertex2f(x - body_w / 2, y + body_h)
    glEnd()

    # Head
    glColor3f(0.263, 0.424, 0.243)

    glBegin(GL_QUADS)
    glVertex2f(x - head_size / 2, y + body_h)
    glVertex2f(x + head_size / 2, y + body_h)
    glVertex2f(x + head_size / 2, y + body_h + head_size)
    glVertex2f(x - head_size / 2, y + body_h + head_size)
    glEnd()

    # Eyes
    glColor3f(1, 1, 1)
    glBegin(GL_QUADS)
    glVertex2f(x - 8 * scale, y + body_h + head_size * 0.6)
    glVertex2f(x - 3 * scale, y + body_h + head_size * 0.6)
    glVertex2f(x - 3 * scale, y + body_h + head_size * 0.8)
    glVertex2f(x - 8 * scale, y + body_h + head_size * 0.8)

    glVertex2f(x + 3 * scale, y + body_h + head_size * 0.6)
    glVertex2f(x + 8 * scale, y + body_h + head_size * 0.6)
    glVertex2f(x + 8 * scale, y + body_h + head_size * 0.8)
    glVertex2f(x + 3 * scale, y + body_h + head_size * 0.8)
    glEnd()

    # Arms
    glColor3f(0.263, 0.424, 0.243)
    glBegin(GL_QUADS)
    glVertex2f(x - body_w / 2 - arm_w, y + body_h * 0.7)
    glVertex2f(x - body_w / 2, y + body_h * 0.7)
    glVertex2f(x - body_w / 2, y + body_h * 0.7 + arm_h)
    glVertex2f(x - body_w / 2 - arm_w, y + body_h * 0.7 + arm_h)

    glVertex2f(x + body_w / 2, y + body_h * 0.7)
    glVertex2f(x + body_w / 2 + arm_w, y + body_h * 0.7)
    glVertex2f(x + body_w / 2 + arm_w, y + body_h * 0.7 + arm_h)
    glVertex2f(x + body_w / 2, y + body_h * 0.7 + arm_h)
    glEnd()

def draw_text(x, y, text, font=GLUT_BITMAP_HELVETICA_18):
    """Draw text on screen"""
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

def draw_cover_screen():
    glClearColor(0.1, 0.1, 0.1, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_DEPTH_TEST) 
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    draw_gravestone_2d(500, 200)
    # Zombies
    draw_zombie_2d(350, 200, 1.2)   # Left 1
    draw_zombie_2d(260, 150, 1.0)   # Left 2
    draw_zombie_2d(650, 200, 1.2)   # Right 1
    draw_zombie_2d(740, 150, 1.0)   # Right 2
    
    # Draw text
    draw_text(380, 720, "ZOMBIE SURVIVAL ARENA", GLUT_BITMAP_HELVETICA_18)
    draw_text(450, 670, "INSTRUCTIONS", GLUT_BITMAP_HELVETICA_12)
    draw_text(370, 640, "  Movement: UP/DOWN/LEFT/RIGHT arrows", GLUT_BITMAP_HELVETICA_12)
    draw_text(450, 620, "Rotate: A/D keys", GLUT_BITMAP_HELVETICA_12)
    draw_text(425, 600, "Camera zoom: W/S keys", GLUT_BITMAP_HELVETICA_12)
    draw_text(435, 580, " Grid Rotation: +/- keys", GLUT_BITMAP_HELVETICA_12)
    draw_text(430, 560, "Shoot: Left mouse click", GLUT_BITMAP_HELVETICA_12)
    draw_text(435, 540, "Redeem coins: C key", GLUT_BITMAP_HELVETICA_12)
    draw_text(410, 520, "Bunker: Move to top-left corner", GLUT_BITMAP_HELVETICA_12)
    draw_text(415, 480, "Press ENTER to start", GLUT_BITMAP_HELVETICA_18)


def draw_difficulty_screen():
    glClearColor(0.1, 0.1, 0.1, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_DEPTH_TEST) 
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    draw_gravestone_2d(500, 200)
    # Zombies
    draw_zombie_2d(350, 200, 1.2)   # Left 1
    draw_zombie_2d(260, 150, 1.0)   # Left 2
    draw_zombie_2d(650, 200, 1.2)   # Right 1
    draw_zombie_2d(740, 150, 1.0)   # Right 2
    # Draw text
    draw_text(410, 650, "SELECT DIFFICULTY", GLUT_BITMAP_HELVETICA_18)
    draw_text(450, 580, "1 - EASY", GLUT_BITMAP_HELVETICA_18)
    draw_text(450, 530, "2 - MEDIUM", GLUT_BITMAP_HELVETICA_18)
    draw_text(450, 480, "3 - HARD", GLUT_BITMAP_HELVETICA_18)

def draw_game_over_screen():
    glClearColor(0.1, 0.1, 0.1, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_DEPTH_TEST) 
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    draw_dead_face(460, 550, 100)
    draw_text(450, 500, "GAME OVER!", GLUT_BITMAP_HELVETICA_18)
    draw_text(400, 450, "The zombies ate your brain!", GLUT_BITMAP_HELVETICA_18)
    draw_text(450, 380, "Press R to restart", GLUT_BITMAP_HELVETICA_18)
    draw_text(400, 340, "Press Enter to go back to start", GLUT_BITMAP_HELVETICA_18)

def draw_game_win_screen():
    glClearColor(0.1, 0.1, 0.1, 1)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glDisable(GL_DEPTH_TEST) 
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)

    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    draw_gravestone_2d(500, 200)
    # Zombies
    draw_zombie_2d(350, 200, 1.2)   # Left 1
    draw_zombie_2d(260, 150, 1.0)   # Left 2
    draw_zombie_2d(650, 200, 1.2)   # Right 1
    draw_zombie_2d(740, 150, 1.0)   # Right 2
    
    draw_text(450, 600, "YOU WIN!", GLUT_BITMAP_HELVETICA_18)
    draw_text(420, 550, "Press R to restart", GLUT_BITMAP_HELVETICA_18)
    draw_text(380, 500, "Press Enter to go back to start", GLUT_BITMAP_HELVETICA_18)

def draw_cube(size_x=1, size_y=1, size_z=1):
    glPushMatrix()
    glScalef(size_x, size_y, size_z)
    glutSolidCube(1)
    glPopMatrix()

def draw_cylinder(base_radius, top_radius, height):
    gluCylinder(gluNewQuadric(), base_radius, top_radius, height, 10, 10)

def draw_player():
    glPushMatrix()
    glTranslatef(player_pos[0], player_pos[1], player_pos[2])
    glRotatef(player_angle, 0, 0, 1)
    
    # Body
    glColor3fv(PURPLE)
    draw_cube(20, 30, 40)
    
    # Head
    glTranslatef(0, 0, 30)
    glColor3fv(SKIN)
    draw_cube(15, 15, 15)
    
    # Gun
    glTranslatef(15, 0, -10)
    glColor3fv(YELLOW)
    glRotatef(90, 0, 1, 0)
    draw_cylinder(3, 3, 25)
    
    glPopMatrix()

def draw_zombie(zombie):
    """Draw a zombie"""
    glPushMatrix()
    glTranslatef(zombie.x, zombie.y, zombie.z+15)
    
    # Head
    glColor3fv(ZOMBIE_GREEN)
    draw_cube(12, 12, 12)
    
    # Body
    glTranslatef(0, 0, -20)
    if zombie.health == 1:
        glColor3fv(BLUE)
        draw_cube(17, 17, 17)  # Smaller body
    else:  # Walker
        glColor3fv(RED)
        draw_cube(25, 25, 25)  # Bigger body
    
    glColor3fv(ZOMBIE_GREEN)
    # Left arm
    glTranslatef(-12, 0, 0)
    draw_cube(8, 8, 20)
    # Right arm
    glTranslatef(24, 0, 0)
    draw_cube(8, 8, 20)
    # Left leg
    glTranslatef(-18, 0, -20)
    draw_cube(8, 8,15)
    # Right leg
    glTranslatef(12, 0, 0)
    draw_cube(8, 8, 15)
    
    glPopMatrix()

def draw_obstacle(obs):

    glPushMatrix()
    glTranslatef(obs.x, obs.y, obs.z)
    
    # Gravestone
    glColor3fv(GRAY)
    draw_cube(40, 20, 60)
    
    # Cross
    glTranslatef(0, 0, 35)
    # Horizontal bar
    glPushMatrix()
    glScalef(20, 5, 5)
    glutSolidCube(1)
    glPopMatrix()
    # Vertical bar
    glPushMatrix()
    glScalef(5, 5, 15)
    glutSolidCube(1)
    glPopMatrix()
    
    glPopMatrix()

def draw_coin(coin):
    glPushMatrix()
    glTranslatef(coin.x, coin.y, coin.z)
    glColor3f(1.0, 0.84, 0.0)  
    glutSolidSphere(8, 20, 20)  
    glPopMatrix()

def draw_bullet(bullet):

    glPushMatrix()
    glTranslatef(bullet.x, bullet.y, bullet.z)
    glColor3fv(YELLOW)
    draw_cube(3, 3, 6)
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

    # Right wall 
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
    # Left wall 
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
    # Top wall
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
    # Bottom wall
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

    
def draw_health_bar():

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 1000, 0, 800)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    
    # Health bar
    health_width = (200 / 100) * player_health
    if player_health > 70:
        glColor3f(0, 1, 0)  # Green
    elif player_health > 20:
        glColor3f(1, 1, 0)  # Yellow
    else:
        glColor3f(1, 0, 0)  # Red
    
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
    
def setupCamera():
    """Set up the camera"""
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(60, 1.25, 0.1, 2000)
    
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    
    x, y, z = camera_pos
    gluLookAt(x, y, z, 0, 0, 0, 0, 0, 1)

def showScreen():
    """Main display function"""
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

def keyboardListener(key, x, y):
    """Handle keyboard input"""
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

def specialKeyListener(key, x, y):
    """Handle special keys (arrows)"""
    global player_pos, player_angle, in_bunker, bunker_uses, bunker_time, player_coins
    
    if game_state != GAME_PLAYING:
        return
    
    old_x, old_y = player_pos[0], player_pos[1]
    
    # Move player
    if key == GLUT_KEY_UP:
        new_x = player_pos[0] + math.cos(math.radians(player_angle)) * 20
        new_y = player_pos[1] + math.sin(math.radians(player_angle)) * 20
        
        # collision with obstacles
        can_move = True
        for obs in obstacles:
            if math.sqrt((new_x - obs.x)**2 + (new_y - obs.y)**2) < 35:
                can_move = False
                break
        
        # set boundary
        safe_distance = 20 
        if (new_x > 300 - safe_distance or new_x < -300 + safe_distance or
            new_y > 300 - safe_distance or new_y < -300 + safe_distance):
            can_move = False
        
        # Check boundaries
        if new_x < -290 or new_x > 290 or new_y < -290 or new_y > 290:
            can_move = False
        
        if can_move:
            player_pos[0] = new_x
            player_pos[1] = new_y
    
    elif key == GLUT_KEY_DOWN:
        new_x = player_pos[0] - math.cos(math.radians(player_angle)) * 20
        new_y = player_pos[1] - math.sin(math.radians(player_angle)) * 20
        
        # Check collision with obstacles
        can_move = True
        for obs in obstacles:
            if math.sqrt((new_x - obs.x)**2 + (new_y - obs.y)**2) < 35:
                can_move = False
                break
        
        # Check collision with walls (x = ±300 and y = ±300)
        safe_distance = 20  # Account for player size
        if (new_x > 300 - safe_distance or new_x < -300 + safe_distance or
            new_y > 300 - safe_distance or new_y < -300 + safe_distance):
            can_move = False
        
        # Check boundaries (inner grid limit)
        if new_x < -290 or new_x > 290 or new_y < -290 or new_y > 290:
            can_move = False
        
        if can_move:
            player_pos[0] = new_x
            player_pos[1] = new_y
    
    elif key == GLUT_KEY_LEFT:
        # Turn left and move forward
        player_angle += 90  # Turn left
        new_x = player_pos[0] + math.cos(math.radians(player_angle)) * 20
        new_y = player_pos[1] + math.sin(math.radians(player_angle)) * 20
        
        # Check collision with obstacles
        can_move = True
        for obs in obstacles:
            if math.sqrt((new_x - obs.x)**2 + (new_y - obs.y)**2) < 35:
                can_move = False
                break
        
        # Check collision with walls 
        safe_distance = 20  
        if (new_x > 300 - safe_distance or new_x < -300 + safe_distance or
            new_y > 300 - safe_distance or new_y < -300 + safe_distance):
            can_move = False
        
        # Check boundaries
        if new_x < -290 or new_x > 290 or new_y < -290 or new_y > 290:
            can_move = False
        
        if can_move:
            player_pos[0] = new_x
            player_pos[1] = new_y
            
    elif key == GLUT_KEY_RIGHT:
        # Turn right and move forward
        player_angle -= 90  # Turn right
        new_x = player_pos[0] + math.cos(math.radians(player_angle)) * 20
        new_y = player_pos[1] + math.sin(math.radians(player_angle)) * 20
        
        # Check collision with obstacles
        can_move = True
        for obs in obstacles:
            if math.sqrt((new_x - obs.x)**2 + (new_y - obs.y)**2) < 35:
                can_move = False
                break
        
        # Check collision with walls (x = ±300 and y = ±300)
        safe_distance = 20  # Account for player size
        if (new_x > 300 - safe_distance or new_x < -300 + safe_distance or
            new_y > 300 - safe_distance or new_y < -300 + safe_distance):
            can_move = False
        
        # Check boundaries
        if new_x < -290 or new_x > 290 or new_y < -290 or new_y > 290:
            can_move = False
        
        if can_move:
            player_pos[0] = new_x
            player_pos[1] = new_y
    
    # Check bunker entry/exit
    bunker_distance = distance_to_bunker(player_pos[0], player_pos[1])
    if bunker_distance < 60:  # Near bunker
        max_uses = 5 if difficulty == EASY else (3 if difficulty == MEDIUM else 2)
        if not in_bunker and bunker_uses < max_uses:
            in_bunker = True
            bunker_time = 0
            bunker_uses += 1
    else:
        if in_bunker:
            in_bunker = False
            bunker_time = 0
    
    # Check coin collection 
    for coin in coins:
        if coin.active:
            distance = math.sqrt((player_pos[0] - coin.x)**2 + (player_pos[1] - coin.y)**2)
            if distance < 25:
                coin.active = False
                player_coins += 1
                respawn_coin()

def mouseListener(button, state, x, y):
    if game_state == GAME_PLAYING and button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
        
        gun_forward = 15 
        
        # Gun position
        gun_x = player_pos[0] + gun_forward * math.cos(math.radians(player_angle))
        gun_y = player_pos[1] + gun_forward * math.sin(math.radians(player_angle))
        gun_z = player_pos[2] + 20  
        
        bullet = Bullet(gun_x, gun_y, player_angle)
        bullet.z = gun_z 
        bullets.append(bullet)

def idle():

    update_game()
    glutPostRedisplay()

def main():

    glutInit()
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(1000, 800)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"Zombie Survival Arena")
    
    glEnable(GL_DEPTH_TEST)
    glClearColor(0, 0, 0, 1)
    
    glutDisplayFunc(showScreen)
    glutKeyboardFunc(keyboardListener)
    glutSpecialFunc(specialKeyListener)
    glutMouseFunc(mouseListener)
    glutIdleFunc(idle)
    
    glutMainLoop()

if __name__ == "__main__":
    main()

