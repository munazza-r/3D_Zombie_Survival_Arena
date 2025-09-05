# 🧟 Zombie Survival Arena

This is a 3D zombie survival arena built with **OpenGL** and **GLUT** in Python.  


---

## 🖥️ Gameplay description

The game offers three difficulty modes:  
- **Easy** – For the weak of heart  
- **Medium** – For thrill seekers  
- **Hard** – Attempt only if you dare  

Walls with grills surround the arena that represents a cemetery with gravestones that the player has to skillfully navigate around. Additionally, the camera can be moved to follow the player for an immersive experience.

The player must survive waves of incoming zombies, collect coins and avoid losing health to race against the timer and reach the goal score to win the game. Otherwise, prepare to lose and get your brain eaten by the zombies!🧠

Low on health? Simply boost your health by redeeming your collected coins🔋

Surrounded by zombies? Take the easy way out with the cheat mode! Or just restart the game.
You can also take shelter in the bunker for a limited time. Use them wisely, you only get a few!💥

You also lose when the timer runs out and you have failed to achieve the goal or if you spend too long in the bunker.


---

## 🎮 Features
- **Player Movement**: Move inside the arena using arrow keys and `A`/`D` for rotation.  
- **Camera Controls**: Zoom with `W`/`S`, rotate arena with `=`/`-`.  
- **Shooting Mechanism**: Fire bullets with **Mouse Left Click**.  
- **Enemies**:  
  - Red zombies – slower but stronger  
  - Blue zombies – faster but weaker  
- **Zombie Waves**: New wave every 30 seconds lasting 10 second.  
- **Coin System**: Collect coins for score.  
- **Health System**: Health drops 10% after each zombie hit.  
- **Health Boost**: Redeem 2 coins for +10% health (`C`).  
- **Timer**: 90 seconds to survive and reach the goal.  
- **Difficulty Levels**: Different goals, enemy counts, and obstacles.  
- **Restart Option**: Reset game instantly (`R`).  
- **Cheat Mode**: Freeze enemies to farm coins/kills (`V`).  
- **Bunker**: Shelter for limited safe time (few uses only).  
- **Arena Design**: Cemetery-themed with gravestones and walls with grills.  

---

## 🕹️ Controls

| Key | Action |
|-----|--------|
| `↑`| Move Forward |
| `↓` | Move Backward |
| `←` | Turn Left |
| `→` | Turn Right |
| `A` | Rotate player anticlockwise |
| `D` | Rotate player clockwise |
| `W` | Zoom out of Arena |
| `S` | Zoom into Arena |
| `=` | Rotate Arena clockwise |
| `-` | Rotate Arena anticlockwise |
| `R` | Restart current game |
| `C` | Redeem 2 coins for +10% health |
| `V` | Activate Cheat mode |
| Mouse Left Click | Shoot bullet |

---
## ⚙️ Requirements:

Make sure you have Python 3.8+ installed.

Download [Python](https://www.python.org/downloads/), if you don’t have it.
 
## 🔧 Installation:

**Install the dependencies:**

**Windows / Linux / macOS (default Python environment):**

```bash
pip install PyOpenGL PyOpenGL_accelerate numpy
```

**If you’re using pip3 (common on Linux/macOS):**

```bash
pip3 install PyOpenGL PyOpenGL_accelerate numpy
```

**If you’re using Anaconda (recommended for science/graphics projects):**

```bash
conda install -c conda-forge pyopengl numpy
```

## ▶️ How to Run

**1. Clone this repository:**

```bash
git clone https://github.com/your-username/zombie-survival-arena.git
cd zombie-survival-arena
```

**2. Run the game:**

```bash
python main.py
```

## 🚀 Future Improvements:
- Cheat Cooldown and Cooldown Timer will be added
- Player hands and legs will be added
- Bunker will disappear when bunker uses run out
- Power-ups will be added
- Pause and Quit buttons
  
-----

**Developed by [Munazza Binte Rafiq](https://github.com/munazza-r), [Afia Abida Shohid](https://github.com/Afia-Abida) and [Mahima Mahzabin Sandria](https://github.com/mahzabinsandria). Go check out our profiles!**

**If you like this project, ⭐ the repo and share with friends!**


