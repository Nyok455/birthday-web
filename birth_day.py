import sys
import re
import os
import math
import random
import pygame

# Small birthday animation: Matrix background, 3-2-1 countdown,
# "Happy Birthday [name]", wish message, heart made of particles,
# overlay message, subtle balloons and confetti.

# ----------------- Configuration -----------------
NAME = 'Achai'  # default; you can pass a name as first arg
if len(sys.argv) > 1:
    NAME = sys.argv[1]

# optional date-of-birth as second CLI arg (accepted formats like 12-05-1990 or 1990/05/12)
DOB = None
if len(sys.argv) > 2:
    raw = sys.argv[2]
    parts = re.split(r"\D+", raw)
    if len(parts) >= 3 and all(p.isdigit() for p in parts[:3]):
        a, b, c = parts[0], parts[1], parts[2]
        # if first is year (4 digits), convert yyyy-mm-dd -> dd-mm-yyyy
        if len(a) == 4:
            DOB = f"{c.zfill(2)}-{b.zfill(2)}-{a}"
        else:
            DOB = f"{a.zfill(2)}-{b.zfill(2)}-{c}"

WISH = 'Wishing you a year full of joy and adventure!'
WIDTH, HEIGHT = 900, 640
FPS = 60
MATRIX_CINEMATIC = True  # if True, denser/faster Matrix-like effect
SHOW_CONFETTI = True

# ----------------- Initialization -----------------
pygame.init()
pygame.mixer.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption('Birthday Animation')
clock = pygame.time.Clock()

# Colors and fonts
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
MATRIX_GREEN = (0, 190, 0)
LIGHT_GREEN = (150, 255, 150)
HEART_RED = (255, 70, 110)
OVERLAY_COLOR = (255, 245, 245)
PINK_BASE = (255, 180, 200)
PINK_LIGHT = (255, 220, 235)
OFF_WHITE = (250, 248, 250)

font_matrix = pygame.font.SysFont('Consolas', 18)
font_big = pygame.font.SysFont('Arial', 76, bold=True)
font_mid = pygame.font.SysFont('Arial', 40)
font_small = pygame.font.SysFont('Arial', 22)

# rainbow palette for text
RAINBOW = [
    (255, 80, 80),
    (255, 150, 80),
    (255, 220, 100),
    (120, 220, 120),
    (100, 180, 255),
    (160, 120, 255),
    (240, 120, 200),
]


def render_rainbow_text(text, font):
    # render each character with cycling rainbow colors onto a surface
    pieces = [font.render(ch, True, RAINBOW[i % len(RAINBOW)])
              for i, ch in enumerate(text)]
    w = sum(p.get_width() for p in pieces)
    h = max((p.get_height() for p in pieces), default=0)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    x = 0
    for p in pieces:
        surf.blit(p, (x, 0))
        x += p.get_width()
    return surf


class Button:
    def __init__(self, rect, label, action, bg=(40, 40, 40), fg=(220, 220, 220)):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.action = action
        self.bg = bg
        self.fg = fg

    def draw(self, surf):
        pygame.draw.rect(surf, self.bg, self.rect, border_radius=6)
        txt = font_small.render(self.label, True, self.fg)
        tr = txt.get_rect(center=self.rect.center)
        surf.blit(txt, tr)

    def handle_event(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            if self.rect.collidepoint(ev.pos):
                self.action()


# ----------------- Matrix background -----------------


class MatrixColumn:
    def __init__(self, x, speed, length):
        self.x = x
        self.speed = speed
        self.length = length
        # entries: [y, char]
        self.entries = []
        for i in range(length):
            y = random.randint(-600, HEIGHT)
            ch = random.choice('0123456789abcdefghijklmnopqrstuvwxyz')
            self.entries.append([y, ch])

    def update_and_draw(self, surf):
        for entry in self.entries:
            entry[0] += self.speed
            if entry[0] > HEIGHT + 20:
                entry[0] = random.randint(-200, -10)
                entry[1] = random.choice(
                    '0123456789abcdefghijklmnopqrstuvwxyz')
            # occasionally change char
            if random.random() < 0.02:
                entry[1] = random.choice(
                    '0123456789abcdefghijklmnopqrstuvwxyz')

        for i, (y, ch) in enumerate(self.entries):
            # pinky-white gradient for matrix-like effect
            t = i / max(1, self.length - 1)
            # base pale pink shifting slightly along the column
            r = 255
            g = int(200 - 80 * t)
            b = int(220 - 60 * t)
            g = max(120, min(255, g))
            b = max(140, min(255, b))
            # occasional bright white/pale head
            if random.random() < 0.06:
                color = OFF_WHITE
            elif random.random() < 0.08:
                color = PINK_LIGHT
            else:
                color = (r, g, b)
            txt = font_matrix.render(ch, True, color)
            surf.blit(txt, (self.x, y))


# prepare columns
char_w, char_h = font_matrix.size('A')
cols = max(12, WIDTH // (char_w + 6))
matrix_columns = []


def create_matrix_columns(mode_cinematic=False):
    matrix_columns.clear()
    for i in range(cols):
        x = i * (char_w + 6)
        if mode_cinematic:
            speed = random.uniform(1.2, 3.6)
        else:
            speed = random.uniform(0.6, 1.6)
        length = random.randint(8, 28 if mode_cinematic else 12)
        matrix_columns.append(MatrixColumn(x, speed, length))


create_matrix_columns(MATRIX_CINEMATIC)


# ----------------- Sequence timings -----------------
COUNTDOWN_DURATION = 3300
NAME_DURATION = 2000
WISH_DURATION = 2600
START = pygame.time.get_ticks()


def now_ms():
    return pygame.time.get_ticks() - START


# ----------------- Countdown animation -----------------


class CountdownNumber:
    def __init__(self, n, start_ms, duration_ms=800):
        self.n = n
        self.start = start_ms
        self.dur = duration_ms
        self.dissolved = False

    def draw(self, surf, t):
        dt = t - self.start
        if dt < 0 or dt > self.dur:
            return
        p = dt / self.dur
        scale = 1 + 0.8 * (1 - (1 - p) ** 3)
        alpha = int(255 * (1 - p)) if p > 0.6 else 255
        s = font_big.render(str(self.n), True, WHITE)
        sw = pygame.transform.smoothscale(
            s, (int(s.get_width() * scale), int(s.get_height() * scale)))
        sw.set_alpha(alpha)
        r = sw.get_rect(center=(WIDTH // 2, HEIGHT // 2))
        surf.blit(sw, r)
        # spawn dissolve particles once near end
        if p > 0.92 and not self.dissolved:
            spawn_particles_from_surface(sw, r.topleft)
            self.dissolved = True


# cd steps
cd_steps = []
step_spacing = COUNTDOWN_DURATION // 3
for i, num in enumerate([3, 2, 1]):
    cd_steps.append(CountdownNumber(num, i * step_spacing, duration_ms=800))


# ----------------- Heart particles -----------------

def ease_out_cubic(p):
    return 1 - (1 - p) ** 3


class HeartParticle:
    def __init__(self, tx, ty):
        self.tx = tx
        self.ty = ty
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(HEIGHT * 0.6, HEIGHT + 120)
        self.size = random.uniform(3.5, 7.5)
        self.delay = random.uniform(0, 800)
        self.t0 = None
        self.draw_size = int(self.size)
    ROMANTIC_COLORS = [
        (255, 60, 110),
        (255, 110, 140),
        (255, 170, 190),
        (255, 140, 100),
        (255, 100, 130),
    ]

    def __init__(self, tx, ty):
        self.tx = tx
        self.ty = ty
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(HEIGHT * 0.6, HEIGHT + 120)
        self.size = random.uniform(4.0, 8.0)
        self.delay = random.uniform(0, 800)
        self.t0 = None
        self.draw_size = int(self.size)
        self.color = random.choice(self.ROMANTIC_COLORS)
        self.angle = random.uniform(0, math.pi * 2)

    def update(self, t_ms):
        if self.t0 is None:
            self.t0 = t_ms
        elapsed = t_ms - self.t0 - self.delay
        if elapsed < 0:
            return
        total = 1800
        p = min(1.0, elapsed / total)
        e = ease_out_cubic(p)
        self.x = self.x + (self.tx - self.x) * (0.06 + 0.9 * e * 0.04)
        self.y = self.y + (self.ty - self.y) * (0.06 + 0.9 * e * 0.04)
        # gentle pulsing
        self.draw_size = max(
            1, int(self.size * (1 + 0.25 * math.sin(p * math.pi * 3))))
        self.angle += 0.02 * (1 + e)

    def draw(self, surf):
        x = int(self.x)
        y = int(self.y)
        s = max(1, self.draw_size)
        c = self.color
        # left and right circles
        left = (x - s // 2, y - s // 4)
        right = (x + s // 2, y - s // 4)
        rsize = max(1, s // 1)
        pygame.draw.circle(surf, c, left, rsize)
        pygame.draw.circle(surf, c, right, rsize)
        # bottom triangle
        points = [(x - s, y), (x + s, y), (x, y + s + s // 2)]
        pygame.draw.polygon(surf, c, points)


# heart shape
heart_points = []
for a in range(0, 360, 6):
    t = math.radians(a)
    x = 16 * math.sin(t) ** 3
    y = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * \
        math.cos(3 * t) - math.cos(4 * t)
    sx = WIDTH // 2 + int(x * 13)
    sy = HEIGHT // 2 + int(-y * 13) - 10
    heart_points.append((sx, sy))

heart_particles = [HeartParticle(x, y) for x, y in heart_points]


# ----------------- Ring bubbles (tiny hearts that bubble around the big heart)


class RingBubbles:
    def __init__(self, positions, speed_ms=120, window=8):
        # positions: list of (x,y)
        self.positions = positions
        self.speed_ms = speed_ms
        self.window = max(3, window)

    def update_and_draw(self, surf, t_ms):
        n = len(self.positions)
        if n == 0:
            return
        base = int(t_ms / self.speed_ms)
        for idx, (x, y) in enumerate(self.positions):
            # distance in sequence from base pointer
            delta = (idx - base) % n
            if delta < self.window:
                # progress: 0.0 -> just lit, up to 1.0 -> about to fade
                p = 1.0 - (delta / float(self.window))
                e = ease_out_cubic(p)
                alpha = int(220 * e)
                size = int(6 + 6 * e)
                # romantic-ish pinks that vary slightly with progress
                c = (255, 90 + int(80 * e), 140 + int(45 * e))

                # draw a small heart with partial alpha onto a temp surface
                hs = max(2, size)
                tmpw = hs * 4
                tmp = pygame.Surface((tmpw, tmpw), pygame.SRCALPHA)
                col = (c[0], c[1], c[2], alpha)
                lx = tmpw // 2 - hs // 2
                ly = tmpw // 2 - hs // 3
                pygame.draw.circle(tmp, col, (lx, ly), hs)
                pygame.draw.circle(tmp, col, (lx + hs, ly), hs)
                points = [
                    (lx - hs, ly + hs // 2),
                    (lx + hs * 2, ly + hs // 2),
                    (lx + hs // 2, ly + hs * 2)
                ]
                pygame.draw.polygon(tmp, col, points)
                surf.blit(tmp, (x - tmpw // 2, y - tmpw // 2),
                          special_flags=pygame.BLEND_PREMULTIPLIED)


# pick ring positions (every Nth point along the generated heart contour)
ring_positions = [heart_points[i] for i in range(0, len(heart_points), 3)]
ring_bubbles = RingBubbles(ring_positions, speed_ms=100, window=9)


# ----------------- Confetti -----------------


class ConfettiPiece:
    def __init__(self):
        self.x = random.uniform(0, WIDTH)
        self.y = random.uniform(-HEIGHT, 0)
        self.size = random.randint(2, 6)
        self.color = random.choice(
            [(255, 40, 40), (40, 200, 40), (40, 120, 255), (255, 200, 40)])
        self.speed = random.uniform(1.5, 4.0)

    def update_and_draw(self, surf):
        self.y += self.speed
        self.x += math.sin(self.y * 0.05) * 1.5
        if self.y > HEIGHT + 20:
            self.y = random.uniform(-HEIGHT, -10)
            self.x = random.uniform(0, WIDTH)
        pygame.draw.rect(surf, self.color, (int(self.x),
                         int(self.y), self.size, self.size))


confetti = [ConfettiPiece() for _ in range(120)]


# ----------------- Particle dissolve system -----------------
class Particle:
    def __init__(self, x, y, color, vx, vy, life=900):
        self.x = x
        self.y = y
        self.color = color
        self.vx = vx
        self.vy = vy
        self.life = life
        self.age = 0

    def update(self, dt):
        self.age += dt
        self.x += self.vx * (dt / 16.0)
        self.y += self.vy * (dt / 16.0)

    def draw(self, surf):
        alpha = max(0, 255 - int(255 * (self.age / self.life)))
        col = (self.color[0], self.color[1], self.color[2], alpha)
        s = max(1, int(3 * (1 - self.age / self.life)))
        tmp = pygame.Surface((s * 2, s * 2), pygame.SRCALPHA)
        pygame.draw.circle(tmp, col, (s, s), s)
        surf.blit(tmp, (int(self.x - s), int(self.y - s)),
                  special_flags=pygame.BLEND_PREMULTIPLIED)


particles = []


# ----------------- Rising hearts (small hearts that rise from bottom to center)
class RisingHeart:
    def __init__(self):
        self.x = random.uniform(WIDTH * 0.15, WIDTH * 0.85)
        self.y = HEIGHT + random.uniform(8, 60)
        # target around center; some will slightly overshoot above
        self.target_y = HEIGHT // 2 + random.uniform(-8, 18)
        self.vy = -random.uniform(0.9, 2.4)
        self.vx = random.uniform(-0.8, 0.8)
        self.size = random.uniform(3.0, 7.0)
        # reuse romantic palette from HeartParticle
        try:
            self.color = random.choice(HeartParticle.ROMANTIC_COLORS)
        except Exception:
            self.color = (255, 120, 170)
        self.age = 0
        self.life = random.randint(1200, 3000)
        # 25% chance to slightly cross above center
        self.overshoot = (random.random() < 0.25)
        self.alive = True

    def update(self, dt):
        self.age += dt
        # simple movement upwards with slight horizontal drift
        self.y += self.vy * (dt / 16.0)
        self.x += self.vx * (dt / 16.0)
        # if reached the target, decide to disappear (or overshoot a bit)
        if not self.overshoot and self.y <= self.target_y:
            self.alive = False
        if self.overshoot and self.y <= (self.target_y - random.uniform(8, 42)):
            self.alive = False
        if self.age > self.life:
            self.alive = False

    def draw(self, surf):
        x = int(self.x)
        y = int(self.y)
        s = max(1, int(self.size))
        c = self.color
        # small heart: two circles and a triangle like HeartParticle
        left = (x - s // 2, y - s // 4)
        right = (x + s // 2, y - s // 4)
        rsize = max(1, s // 1)
        pygame.draw.circle(surf, c, left, rsize)
        pygame.draw.circle(surf, c, right, rsize)
        points = [(x - s, y), (x + s, y), (x, y + s + s // 2)]
        pygame.draw.polygon(surf, c, points)


rising_hearts = []
next_rising_spawn = 0


# ----------------- Balloons that lift texts -----------------
class Balloon:
    def __init__(self, kind, key, tx, ty):
        # kind: 'countdown'|'name'|'wish' ; key for countdown is start_ms
        self.kind = kind
        self.key = key
        # balloon position starts below text
        self.x = tx + random.uniform(-12, 12)
        self.y = ty + 24
        self.vy = -random.uniform(0.6, 1.6)
        self.life = random.randint(900, 2200)
        self.age = 0
        self.max_lift = random.uniform(18, 46)
        self.color = random.choice(
            HeartParticle.ROMANTIC_COLORS) if 'HeartParticle' in globals() else (255, 140, 180)
        self.alive = True

    def update(self, dt):
        self.age += dt
        self.y += self.vy * (dt / 16.0)
        if self.age >= self.life:
            self.alive = False

    def draw(self, surf, tether_x, tether_y):
        # draw string from balloon to tether point and balloon circle
        # slight sway based on age
        sway = int(6 * math.sin(self.age / 180.0))
        bx = int(self.x + sway)
        by = int(self.y)
        # string
        pygame.draw.line(surf, (200, 200, 200),
                         (tether_x, tether_y), (bx, by), 2)
        # balloon
        pygame.draw.ellipse(surf, self.color, (bx - 10, by - 18, 20, 28))

    def current_lift(self):
        # eased lift amount based on age/life
        p = min(1.0, self.age / max(1, self.life))
        return ease_out_cubic(p) * self.max_lift


balloons = []


def spawn_particles_from_surface(surf, topleft, count=60):
    # sample pixels on surf to emit particles
    w, h = surf.get_size()
    for i in range(count):
        sx = random.randint(0, max(0, w - 1))
        sy = random.randint(0, max(0, h - 1))
        try:
            col = surf.get_at((sx, sy))
        except Exception:
            col = (255, 255, 255, 255)
        x = topleft[0] + sx
        y = topleft[1] + sy
        ang = random.uniform(0, math.pi * 2)
        spd = random.uniform(1.0, 6.0)
        vx = math.cos(ang) * spd
        vy = math.sin(ang) * spd - random.uniform(0.5, 2.5)
        particles.append(Particle(x, y, col, vx, vy,
                         life=random.randint(600, 1400)))


def update_and_draw_particles(surf, dt):
    for p in particles[:]:
        p.update(dt)
        p.draw(surf)
        if p.age >= p.life:
            particles.remove(p)


# ----------------- Colorful cake renderer (replaces the simple one)
def draw_colorful_cake(cx, cy, t_ms):
    cake_w = 180
    cake_h = 90
    left = cx - cake_w // 2
    top = cy - cake_h // 2 + 18
    # multi-layer colorful stripes
    layers = [
        (250, 200, 230),
        (240, 170, 210),
        (255, 220, 200),
        (245, 200, 255),
    ]
    for i, col in enumerate(layers):
        ly = top + 8 + i * 18
        pygame.draw.rect(screen, (20, 10, 20), (left + 4,
                         ly + 4, cake_w - 8, 14), border_radius=6)
        pygame.draw.rect(screen, col, (left + 6, ly,
                         cake_w - 12, 14), border_radius=6)
    # icing sprinkles (randomized but deterministic-ish using time)
    seed = int(t_ms // 300) % 1000
    random.seed(seed)
    for _ in range(18):
        sx = random.randint(left + 10, left + cake_w - 10)
        sy = random.randint(top + 10, top + cake_h - 10)
        color = random.choice(
            [(255, 120, 180), (255, 200, 80), (180, 255, 220), (200, 200, 255)])
        pygame.draw.circle(screen, color, (sx, sy), 3)
    # candle (center)
    cx_c = cx
    cy_c = top - 8
    pygame.draw.rect(screen, (255, 255, 230), (cx_c - 5,
                     cy_c - 28, 10, 28), border_radius=3)
    # candle flame
    f = (math.sin(t_ms / 120.0) + 1) / 2.0
    flame_h = 10 + int(6 * f)
    flame_col = (255, 220 + int(30 * f), 140)
    pygame.draw.ellipse(screen, flame_col, (cx_c - 6,
                        cy_c - 28 - flame_h, 12, flame_h * 2))


# UI buttons
buttons = []


def do_replay():
    global START, heart_particles, balloons, particles, rising_hearts, next_rising_spawn, music_started, USER_SONG_ACTIVE
    global SHOW_LITTLE_FUN_MSG, SHOW_SONG_SELECT, LFM_START
    global ring_bubbles, cd_steps
    START = pygame.time.get_ticks()
    heart_particles = [HeartParticle(x, y) for x, y in heart_points]
    ring_bubbles = RingBubbles([heart_points[i] for i in range(0, len(heart_points), 3)], speed_ms=100, window=9)
    # fully reset the countdown steps and their dissolve/ballooned state
    cd_steps.clear()
    step_spacing = COUNTDOWN_DURATION // 3
    for i, num in enumerate([3, 2, 1]):
        cd_steps.append(CountdownNumber(num, i * step_spacing, duration_ms=800))
    balloons.clear()
    particles.clear()
    rising_hearts.clear()
    next_rising_spawn = 0
    SHOW_LITTLE_FUN_MSG = False
    SHOW_SONG_SELECT = False
    LFM_START = 0
    music_started = False
    USER_SONG_ACTIVE = False
    try:
        pygame.mixer.music.stop()
    except Exception:
        pass


# placeholder for Little Fun message display
SHOW_LITTLE_FUN_MSG = False
LFM_START = 0
LFM_DURATION = 3500


def do_your_wishes():
    # collect a short message and open default mail client with prefilled mailto
    try:
        # prefer a simple tkinter dialog when available (non-blocking to import here)
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        msg = simpledialog.askstring(
            'Your Wishes', 'Type your message to send:')
        root.destroy()
    except Exception:
        # fallback to console input
        try:
            msg = input('Enter your wish message to send: ')
        except Exception:
            msg = None
    if msg:
        try:
            import webbrowser
            from urllib.parse import quote
            body = quote(msg)
            webbrowser.open(
                f'mailto:email@gail.com?subject=Birthday%20Wish&body={body}')
        except Exception:
            # if we can't open the mail client, just print to console as fallback
            print('Wish ready to send to email@gail.com:\n', msg)


SONGS = [
    ("Birthday Song 1", "song1.mp3", (255,220,0)),
    ("Birthday Song 2", "song2.mp3", (120,220,200)),
    ("Birthday Song 3", "song3.mp3", (200,120,255)),
    ("Birthday Song 4", "song4.mp3", (250,145,145)),
]
SHOW_SONG_SELECT = False
USER_SONG_ACTIVE = False

# Utility for song playback

def play_song(songfile):
    try:
        pygame.mixer.music.load(songfile)
        pygame.mixer.music.play(-1)
    except Exception as e:
        print(f"Could not play {songfile}: {e}")

def do_little_fun():
    global SHOW_SONG_SELECT, SHOW_LITTLE_FUN_MSG, LFM_START
    SHOW_LITTLE_FUN_MSG = False  # hide previous
    SHOW_SONG_SELECT = True
    LFM_START = pygame.time.get_ticks()


def do_exit():
    pygame.quit()
    sys.exit()


def toggle_confetti():
    global SHOW_CONFETTI
    SHOW_CONFETTI = not SHOW_CONFETTI


def toggle_matrix_mode():
    global MATRIX_CINEMATIC
    MATRIX_CINEMATIC = not MATRIX_CINEMATIC
    create_matrix_columns(MATRIX_CINEMATIC)


buttons.append(Button((WIDTH - 120, 12, 100, 32),
               'Replay', do_replay, bg=(40, 180, 40)))
buttons.append(Button((WIDTH - 120, 52, 100, 32),
               'Exit', do_exit, bg=(180, 40, 40)))
# add Your Wishes and Little Fun buttons (blue, purple)
buttons.append(Button((WIDTH - 120, 92, 100, 32),
               'Your Wishes', do_your_wishes, bg=(40, 120, 220)))
buttons.append(Button((WIDTH - 120, 132, 100, 32),
               'Little Fun', do_little_fun, bg=(160, 80, 200)))
# hidden by default: confetti/matrix mode controls kept but UI buttons removed
# buttons.append(Button((WIDTH - 120, 92, 100, 32), 'Confetti',
#                toggle_confetti, bg=(60, 60, 120)))
# buttons.append(Button((WIDTH - 120, 132, 100, 32), 'Matrix',
#                toggle_matrix_mode, bg=(40, 90, 40)))


# ----------------- Main loop -----------------
music_started = False
running = True
# Start main song on application launch
try:
    pygame.mixer.music.load(CURRENT_SONGFILE)
    pygame.mixer.music.play(-1)
    music_started = True
except Exception:
    music_started = False

while running:
    dt = clock.tick(FPS)
    t = now_ms()
    # Event/process logic split for modal vs normal
    if SHOW_SONG_SELECT:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                SHOW_SONG_SELECT = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                button_w, button_h = 240, 60
                gap = 24
                left = WIDTH//2 - button_w//2
                top = 200
                for i, (label, songfile, color) in enumerate(SONGS):
                    y = top + i*(button_h+gap)
                    rect = pygame.Rect(left, y, button_w, button_h)
                    if rect.collidepoint(mx, my):
                        pygame.mixer.music.stop()
                        play_song(songfile)
                        SHOW_SONG_SELECT = False
                        USER_SONG_ACTIVE = True
        # Matrix background (draw underneath modal)
        screen.fill(BLACK)
        for col in matrix_columns:
            col.update_and_draw(screen)
        # Usual heart animation logic
        if t < COUNTDOWN_DURATION:
            for step in cd_steps:
                step.draw(screen, t)
                if not getattr(step, 'ballooned', False):
                    dt_step = t - step.start
                    if 0 <= dt_step <= step.dur and (dt_step / step.dur) > 0.75:
                        bx = WIDTH // 2
                        by = HEIGHT // 2
                        b = Balloon('countdown', step.start, bx, by)
                        balloons.append(b)
                        step.ballooned = True
        elif t < COUNTDOWN_DURATION + NAME_DURATION:
            local = t - COUNTDOWN_DURATION
            p = min(1.0, local / 800.0)
            alpha = int(255 * p)
            yoff = int((1 - p) * 40)
            name_surf = render_rainbow_text(f'Happy Birthday, Achai!', font_big)
            name_surf.set_alpha(alpha)
            name_rect = name_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40 + yoff))
            screen.blit(name_surf, name_rect)
            if not any(b.kind == 'name' for b in balloons) and p > 0.6:
                balloons.append(Balloon('name', 'name', name_rect.centerx, name_rect.centery))
            if 'DOB' in globals() and DOB:
                dob_txt = font_mid.render(f'Date of Birth: {DOB}', True, OVERLAY_COLOR)
                dob_s = dob_txt.copy()
                dob_s.set_alpha(alpha)
                dob_r = dob_s.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 8 + yoff))
                screen.blit(dob_s, dob_r)
        elif t < COUNTDOWN_DURATION + NAME_DURATION + WISH_DURATION:
            local = t - COUNTDOWN_DURATION - NAME_DURATION
            p = min(1.0, local / 800.0)
            alpha = int(255 * p)
            yoff = int((1 - p) * 20)
            wish_surf = render_rainbow_text(WISH, font_mid)
            wish_surf.set_alpha(alpha)
            wrect = wish_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 10 + yoff))
            screen.blit(wish_surf, wrect)
            if not any(b.kind == 'wish' for b in balloons) and p > 0.6:
                balloons.append(Balloon('wish', 'wish', wrect.centerx, wrect.centery))
        else:
            ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 120))
            screen.blit(ov, (0, 0))
            for p in heart_particles:
                p.update(t)
                p.draw(screen)
            if t >= next_rising_spawn:
                for _ in range(random.randint(1, 3)):
                    rising_hearts.append(RisingHeart())
                next_rising_spawn = t + random.randint(220, 700)
            for rh in rising_hearts[:]:
                rh.update(dt)
                rh.draw(screen)
                if not rh.alive:
                    try:
                        rising_hearts.remove(rh)
                    except ValueError:
                        pass
            ring_bubbles.update_and_draw(screen, t)
            if SHOW_CONFETTI:
                for c in confetti:
                    c.update_and_draw(screen)
            draw_colorful_cake(WIDTH // 2, HEIGHT // 2 + 20, t)
            update_and_draw_particles(screen, dt)
            msg = font_mid.render('With all my love', True, (255, 220, 230))
            mr = msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 180))
            screen.blit(msg, mr)
        # Draw modal on top
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 190))
        screen.blit(ov, (0, 0))
        heading = font_mid.render("Choose Birthday Song", True, (255,255,210))
        head_rect = heading.get_rect(center=(WIDTH//2, 120))
        screen.blit(heading, head_rect)
        button_w, button_h = 240, 60
        gap = 24
        left = WIDTH//2 - button_w//2
        top = 200
        for i, (label, songfile, color) in enumerate(SONGS):
            y = top + i*(button_h+gap)
            rect = pygame.Rect(left, y, button_w, button_h)
            pygame.draw.rect(screen, color, rect, border_radius=10)
            bordercol = (0,0,0)
            pygame.draw.rect(screen, bordercol, rect, width=2, border_radius=10)
            txt = font_small.render(label, True, (40,40,40))
            txtr = txt.get_rect(center=rect.center)
            screen.blit(txt, txtr)
        pygame.display.flip()
        continue  # skip rest of loop (especially button handling below)
    else:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
            # UI buttons
            for b in buttons:
                b.handle_event(event)
    # Matrix background
    screen.fill(BLACK)
    for col in matrix_columns:
        col.update_and_draw(screen)

    # (no background balloons)

    # Sequence
    if t < COUNTDOWN_DURATION:
        for step in cd_steps:
            # render countdown in rainbow and allow balloon to lift as it dissolves
            step.draw(screen, t)
            # when the number is near its end, spawn a balloon tethered to it
            if not getattr(step, 'ballooned', False):
                # compute where the number is drawn
                dt = t - step.start
                if 0 <= dt <= step.dur and (dt / step.dur) > 0.75:
                    # spawn a balloon that tugs the number upwards while fading
                    # estimate center position
                    bx = WIDTH // 2
                    by = HEIGHT // 2
                    b = Balloon('countdown', step.start, bx, by)
                    balloons.append(b)
                    step.ballooned = True
        # Stop music if running a replay/reset
        # (You may need to handle stop on replay elsewhere if necessary)
    else:
        # Only play "MainSong.mp3" after countdown if user song not active
        if not music_started and not USER_SONG_ACTIVE and t >= COUNTDOWN_DURATION:
            try:
                pygame.mixer.music.load("MainSong.mp3")
                pygame.mixer.music.play(-1)
                music_started = True
            except Exception as e:
                print(f"Error: Could not play MainSong.mp3: {e}")
        if USER_SONG_ACTIVE and t < COUNTDOWN_DURATION:
            # If somehow user goes back and countdown plays again, stop user song (edge safety)
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass
            USER_SONG_ACTIVE = False
            music_started = False
    if t < COUNTDOWN_DURATION:
        pass  # Existing countdown handled above
    elif t < COUNTDOWN_DURATION + NAME_DURATION:
        local = t - COUNTDOWN_DURATION
        p = min(1.0, local / 800.0)
        alpha = int(255 * p)
        yoff = int((1 - p) * 40)
        # rainbow name text
        name_surf = render_rainbow_text(f'Happy Birthday, Achai!', font_big)
        name_surf.set_alpha(alpha)
        name_rect = name_surf.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 - 40 + yoff))
        screen.blit(name_surf, name_rect)
        # spawn a balloon the first time it is fading
        if not any(b.kind == 'name' for b in balloons) and p > 0.6:
            balloons.append(
                Balloon('name', 'name', name_rect.centerx, name_rect.centery))
        # optional date of birth display under the name
        if 'DOB' in globals() and DOB:
            dob_txt = font_mid.render(
                f'Date of Birth: {DOB}', True, OVERLAY_COLOR)
            dob_s = dob_txt.copy()
            dob_s.set_alpha(alpha)
            dob_r = dob_s.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 8 + yoff))
            screen.blit(dob_s, dob_r)
    elif t < COUNTDOWN_DURATION + NAME_DURATION + WISH_DURATION:
        local = t - COUNTDOWN_DURATION - NAME_DURATION
        p = min(1.0, local / 800.0)
        alpha = int(255 * p)
        yoff = int((1 - p) * 20)
        wish_surf = render_rainbow_text(WISH, font_mid)
        wish_surf.set_alpha(alpha)
        wrect = wish_surf.get_rect(
            center=(WIDTH // 2, HEIGHT // 2 - 10 + yoff))
        screen.blit(wish_surf, wrect)
        if not any(b.kind == 'wish' for b in balloons) and p > 0.6:
            balloons.append(
                Balloon('wish', 'wish', wrect.centerx, wrect.centery))
    else:
        ov = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        ov.fill((0, 0, 0, 120))
        screen.blit(ov, (0, 0))

        for p in heart_particles:
            p.update(t)
            p.draw(screen)
        # spawn rising hearts periodically
        if t >= next_rising_spawn:
            # spawn 1-3 hearts at a time
            for _ in range(random.randint(1, 3)):
                rising_hearts.append(RisingHeart())
            next_rising_spawn = t + random.randint(220, 700)
        # update/draw rising hearts
        for rh in rising_hearts[:]:
            rh.update(dt)
            rh.draw(screen)
            if not rh.alive:
                try:
                    rising_hearts.remove(rh)
                except ValueError:
                    pass
        # small bubbling hearts around the ring
        ring_bubbles.update_and_draw(screen, t)
        if SHOW_CONFETTI:
            for c in confetti:
                c.update_and_draw(screen)

        # draw colorful cake in the heart center
        draw_colorful_cake(WIDTH // 2, HEIGHT // 2 + 20, t)

        # update/draw dissolve particles
        update_and_draw_particles(screen, dt)

        msg = font_mid.render('With all my love', True, (255, 220, 230))
        mr = msg.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 180))
        screen.blit(msg, mr)

    # Little Fun placeholder message overlay
    if SHOW_LITTLE_FUN_MSG:
        now = pygame.time.get_ticks()
        if now - LFM_START < LFM_DURATION:
            lm = font_mid.render(
                'Little Fun: Guessing game coming soon!', True, (240, 240, 200))
            lr = lm.get_rect(center=(WIDTH // 2, HEIGHT - 60))
            screen.blit(lm, lr)
        else:
            SHOW_LITTLE_FUN_MSG = False

    footer = font_small.render('Press ESC to exit', True, (180, 180, 180))
    screen.blit(footer, (10, HEIGHT - 28))

    # update + draw balloons
    for b in balloons[:]:
        b.update(dt)
        # tether point depends on kind (use slight upward lift while balloon alive)
        if b.kind == 'countdown' or b.kind == 'name' or b.kind == 'wish':
            tether_x = WIDTH // 2
            tether_y = HEIGHT // 2 - \
                40 if b.kind == 'name' else (
                    HEIGHT // 2 if b.kind == 'countdown' else HEIGHT // 2 - 10)
        else:
            tether_x, tether_y = b.x, b.y + 24
        b.draw(screen, tether_x, tether_y -
               int(min(b.max_lift, (b.age / max(1, b.life)) * b.max_lift)))
        if not b.alive:
            try:
                balloons.remove(b)
            except ValueError:
                pass

    # draw buttons and status
    for b in buttons:
        b.draw(screen)
    status = (
        f"Matrix={'Cinematic' if MATRIX_CINEMATIC else 'Calm'}  "
        f"Confetti={'On' if SHOW_CONFETTI else 'Off'}"
    )
    st = font_small.render(status, True, (200, 200, 200))
    screen.blit(st, (10, 10))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()
