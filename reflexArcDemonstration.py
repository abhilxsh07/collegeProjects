import sys
import math
import time
import webbrowser
import pygame


WIDTH, HEIGHT = 1500, 1000 #any other size looks disgusting :V
FPS = 60 #60fps in the big 25

SPEED_DEFAULT_PXPS = 300.0

#metrics im defining now, will relate to meters later
DELAY_SENSORY_TO_SPINAL_DEFAULT = 0.003
DELAY_SPINAL_TO_MOTOR_DEFAULT   = 0.003

#self explanatory
BG = (16, 18, 22)
TEXT = (235, 236, 240)
HINT = (170, 175, 210)
NODE_FILL = (35, 39, 47)
NODE_BORDER = (240, 240, 240)
EDGE = (130, 140, 165)
IMPULSE = (255, 220, 80)
ACCENT = (255, 240, 140)
PANEL_BG = (26, 28, 34)
PANEL_BORDER = (65, 70, 90)
HILITE = (90, 180, 255)
PAUSE_BADGE = (255, 200, 80)

NODE_R = 34
IMPULSE_R = 8
RIGHT_PANEL_W = 360


GITHUB_URL = "https://github.com/abhilxsh07"
WATERMARK_LEFT_TEXT = "made by - "
WATERMARK_NAME_TEXT = "Abhilash Kar"
WATERMARK_PADDING = 12

#deep breaths, and lets build this, step by step.
pygame.init()
pygame.display.set_caption("Reflex Arc Demonstration")
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 18)
mono = pygame.font.SysFont("consolas", 16)
title_font = pygame.font.SysFont("arial", 22, bold=True)
small = pygame.font.SysFont("arial", 16)

#math to align content so it doesnt stick to a silly linear diagram
POS_RECEPTOR = (110, HEIGHT // 2)
POS_SENSORY  = (300, HEIGHT // 2 - 110)
POS_SPINAL   = (500, HEIGHT // 2)
POS_MOTOR    = (700, HEIGHT // 2 + 110)
POS_MUSCLE   = (880, HEIGHT // 2)

PATH_R_TO_S  = [POS_RECEPTOR, (200, HEIGHT // 2 - 55), POS_SENSORY]
PATH_S_TO_SP = [POS_SENSORY, (400, HEIGHT // 2 - 55), POS_SPINAL]
PATH_SP_TO_M = [POS_SPINAL, (600, HEIGHT // 2 + 55), POS_MOTOR]
PATH_M_TO_MU = [POS_MOTOR, (790, HEIGHT // 2 + 55), POS_MUSCLE]
#defining those nodes
NODES = [
    ("Receptor", POS_RECEPTOR),
    ("Sensory neuron", POS_SENSORY),
    ("Spinal cord", POS_SPINAL),
    ("Motor neuron", POS_MOTOR),
    ("Muscle", POS_MUSCLE),
]

#node-specific info
PART_INFO = {
    "Receptor": {
        "does": "Detects a change (touch, stretch, heat, pain) and starts the nerve signal.",
        "examples": [
            "Patellar tendon tap (knee-jerk)",
            "Touching a hot surface",
            "Muscle stretch in the quadriceps",
            "Pinprick on the skin",
        ],
    },
    "Sensory neuron": {
        "does": "Carries the signal from the receptor into the spinal cord (afferent pathway).",
        "examples": [
            "A-delta fibers carry fast pain/temperature",
            "A-beta fibers carry touch/pressure",
        ],
    },
    "Spinal cord": {
        "does": "Relay point: the signal crosses a synapse (± interneuron) and forms the reflex plan.",
        "examples": [
            "Monosynaptic stretch reflex (knee-jerk)",
            "Polysynaptic withdrawal reflex (hand pulls back)",
        ],
    },
    "Motor neuron": {
        "does": "Carries the command out from the spinal cord to the muscle (efferent pathway).",
        "examples": [
            "α-motor neuron activates quadriceps",
            "Inhibits antagonist via interneurons",
        ],
    },
    "Muscle": {
        "does": "Contracts as the final effect — this is the visible reflex action.",
        "examples": [
            "Quadriceps shortens → lower leg kicks",
            "Biceps contracts to pull hand away",
        ],
    },
}

#soulconsumingcodeneededhelpwith
def draw_node(pos, text, highlight=False):
    pygame.draw.circle(screen, NODE_FILL, pos, NODE_R)
    border = HILITE if highlight else NODE_BORDER
    pygame.draw.circle(screen, border, pos, NODE_R, 2)
    t = font.render(text, True, TEXT)
    screen.blit(t, t.get_rect(center=(pos[0], pos[1] - NODE_R - 16)))

def draw_path(points):
    pygame.draw.lines(screen, EDGE, False, points, 3)

def path_len(points):
    d = 0.0
    for i in range(len(points)-1):
        x1,y1 = points[i]
        x2,y2 = points[i+1]
        d += math.hypot(x2-x1, y2-y1)
    return d


def interp(points, dist):
    if dist <= 0: return points[0]
    left = dist
    for i in range(len(points)-1):
        x1,y1 = points[i]
        x2,y2 = points[i+1]
        seg = math.hypot(x2-x1, y2-y1)   #coordinate geometry finally came in handy
        if left <= seg:
            t = 0 if seg == 0 else left/seg
            return (x1 + t*(x2-x1), y1 + t*(y2-y1))
        left -= seg
    return points[-1]

def pxps_to_mps(px_per_s, px_per_meter=3000.0):
    #scaling 3000px to be ~ 1m
    return px_per_s / px_per_meter

def wrap_text(text, font_obj, max_width):

    words = text.split()
    lines, line = [], ""
    for w in words:
        test = (line + " " + w).strip()
        if font_obj.size(test)[0] <= max_width:
            line = test
        else:
            if line: lines.append(line)
            line = w
    if line: lines.append(line)
    return lines

def mouse_over_node(mx, my):
    for name, pos in NODES:
        if math.hypot(mx - pos[0], my - pos[1]) <= NODE_R + 6:
            return name
    return None

#defining classes for each keyboard action instance defined
class Segment:
    def __init__(self, pts, syn_delay=0.0, name=""):  #the init, naturally, hold all my variables
        self.pts = pts
        self.len = path_len(pts)
        self.syn_delay = syn_delay
        self.name = name

class Impulse:
    def __init__(self, speed_pxps, d1, d2):
        self.speed = speed_pxps
        self.d1 = d1
        self.d2 = d2
        self.make_segments()
        self.reset()

    def make_segments(self):
        self.segs = [
            Segment(PATH_R_TO_S, 0.0, "Sensory neuron"),     # leaving Receptor → heading to Sensory neuron
            Segment(PATH_S_TO_SP, self.d1, "Spinal cord"),
            Segment(PATH_SP_TO_M, self.d2, "Motor neuron"),
            Segment(PATH_M_TO_MU, 0.0, "Muscle"),
        ]

    def reset(self):
        self.active = False
        self.paused = False
        self.si = 0
        self.dist = 0.0
        self.wait = 0.0
        self.t0 = None
        self.events = []
        self.trials = 0
        self.last_measured_ms = None

    def start(self):
        if self.active and not self.paused:
            return  #if it's paused, rather than restarting the damn thing just, yk, resumes.

        if self.active and self.paused:
            self.paused = False
            return
        self.active = True
        self.paused = False
        self.si = 0
        self.dist = 0.0
        self.wait = 0.0
        self.t0 = time.time()
        self.events = [("Stimulus (receptor)", self.t0)]
        self.trials += 1

    # NEW: pause toggle
    def toggle_pause(self):
        if self.active:
            self.paused = not self.paused

    def update(self, dt):
        if not self.active:
            return
        if self.paused:
            return  # freeze position and wait timers while paused

        if self.wait > 0:
            self.wait -= dt
            if self.wait < 0: self.wait = 0
            return

        seg = self.segs[self.si]
        self.dist += self.speed * dt

        if self.dist >= seg.len:
            self.dist = seg.len
            now = time.time()
            self.events.append((f"Reached {seg.name}", now))

            if seg.syn_delay > 0:
                self.wait = seg.syn_delay

            if self.si < len(self.segs) - 1:
                self.si += 1
                self.dist = 0.0
            else:
                # finished
                self.active = False
                end = time.time()
                self.events.append(("Muscle contracts", end))
                self.last_measured_ms = (end - self.t0) * 1000.0
                self.print_summary()

    def pos(self):
        seg = self.segs[self.si]
        return interp(seg.pts, self.dist)

    def current_step(self):
        return self.segs[self.si].name if self.active else "—"

    def current_focus_part(self):  #defining what and when info will be displayed
        """Which part's info should the panel show when not hovering."""
        if not self.active:
            # idle will show Receptor by default
            return "Receptor"
        # During the very start of the first segment, still highlight Receptor
        if self.si == 0 and self.dist < max(1.0, self.segs[0].len * 0.20):
            return "Receptor"
        # otherwise the target node of the current segment
        return self.segs[self.si].name

    def progress_pct(self):
        seg = self.segs[self.si]
        return 0.0 if seg.len == 0 else min(100.0, 100.0 * self.dist / seg.len)

    def print_summary(self):
        print("\n=== Reflex timeline ===")
        base = self.events[0][1]
        for label, t in self.events:
            print(f"{(t-base)*1000:7.2f} ms : {label}")
        print(f"Total latency: {self.last_measured_ms:.2f} ms")
        print("=======================\n")


imp = Impulse(SPEED_DEFAULT_PXPS, DELAY_SENSORY_TO_SPINAL_DEFAULT, DELAY_SPINAL_TO_MOTOR_DEFAULT)  #implementing the impulse class execution by passing in arguments

def total_path_px():
    return path_len(PATH_R_TO_S) + path_len(PATH_S_TO_SP) + path_len(PATH_SP_TO_M) + path_len(PATH_M_TO_MU)   #coordinate geometry, again.

def predicted_latency_ms():
    travel_s = total_path_px() / max(1e-9, imp.speed)
    return (travel_s + imp.d1 + imp.d2) * 1000.0


last_watermark_name_rect = None

def draw_watermark(): #rendering the watermark

    global last_watermark_name_rect

    left_surf = small.render(WATERMARK_LEFT_TEXT, True, HINT)
    name_surf = small.render(WATERMARK_NAME_TEXT, True, HILITE)

    total_w = left_surf.get_width() + name_surf.get_width()
    x = WIDTH - total_w - WATERMARK_PADDING
    y = HEIGHT - name_surf.get_height() - WATERMARK_PADDING

    # draw text
    screen.blit(left_surf, (x, y))
    name_x = x + left_surf.get_width()
    screen.blit(name_surf, (name_x, y))

    # underline for the hyperlink look
    underline_y = y + name_surf.get_height() - 2
    pygame.draw.line(screen, HILITE, (name_x, underline_y), (name_x + name_surf.get_width(), underline_y), 1)

    # update rect for click detection
    last_watermark_name_rect = pygame.Rect(name_x, y, name_surf.get_width(), name_surf.get_height())

#Self explanatory imo
def draw_scene(show_panel=True, hover_name=None):
    screen.fill(BG)

    # title + quick help
    screen.blit(title_font.render("Spinal Reflex (Simple)", True, TEXT), (20, 16))
    y = 52
    for msg in [
        "Space/Click: Stimulus   P: Pause/Resume   Up/Down: Speed   Q/A & W/S: Delays   R: Reset   L: Toggle panel ",
        f"Speed: {imp.speed:.0f} px/s  ({pxps_to_mps(imp.speed):.3f} m/s)   Trials: {imp.trials}     Hover over each part to learn more.",
    ]:
        screen.blit(mono.render(msg, True, HINT), (20, y))
        y += 20

    # show PAUSED badge if paused
    if imp.paused:
        badge = mono.render("PAUSED", True, PAUSE_BADGE)
        screen.blit(badge, (20, y))

    # diagram paths
    for p in (PATH_R_TO_S, PATH_S_TO_SP, PATH_SP_TO_M, PATH_M_TO_MU):
        draw_path(p)

    # which node to highlight
    focus_part = hover_name if hover_name else imp.current_focus_part()

    # nodes
    for name, pos in NODES:
        draw_node(pos, name, highlight=(name == focus_part))

    # impulse
    if imp.active or imp.wait > 0:
        x, y2 = imp.pos()
        pygame.draw.circle(screen, IMPULSE, (int(x), int(y2)), IMPULSE_R)
        pygame.draw.circle(screen, ACCENT, (int(x), int(y2)), IMPULSE_R+5, 2)

    # small delay tags near synapses
    tag1 = mono.render(f"{int(round(imp.d1*1000))} ms", True, ACCENT)
    tag2 = mono.render(f"{int(round(imp.d2*1000))} ms", True, ACCENT)
    screen.blit(tag1, tag1.get_rect(center=((POS_SENSORY[0]+POS_SPINAL[0])//2, (POS_SENSORY[1]+POS_SPINAL[1])//2 - 18)))
    screen.blit(tag2, tag2.get_rect(center=((POS_SPINAL[0]+POS_MOTOR[0])//2, (POS_SPINAL[1]+POS_MOTOR[1])//2 + 22)))

    # right info panel
    if show_panel:
        draw_info_panel(focus_part)

    # watermark (always on top)
    draw_watermark()

def draw_info_panel(part_name):
    panel = pygame.Rect(WIDTH - RIGHT_PANEL_W, 0, RIGHT_PANEL_W, HEIGHT)
    pygame.draw.rect(screen, PANEL_BG, panel)
    pygame.draw.rect(screen, PANEL_BORDER, panel, 1)

    x = panel.x + 16
    y = 16
    screen.blit(title_font.render("Part Info", True, TEXT), (x, y)); y += 30

    # Show which part we’re describing
    screen.blit(font.render(part_name, True, HILITE), (x, y)); y += 26

    info = PART_INFO.get(part_name, None)
    if info:
        # What it does
        screen.blit(font.render("What it does:", True, TEXT), (x, y)); y += 22
        for line in wrap_text(info["does"], small, RIGHT_PANEL_W - 32):
            screen.blit(small.render(line, True, TEXT), (x, y))
            y += 20
        y += 8

        # Examples
        screen.blit(font.render("Examples:", True, TEXT), (x, y)); y += 22
        for ex in info["examples"]:
            bullet = "• " + ex
            for line in wrap_text(bullet, small, RIGHT_PANEL_W - 32):
                screen.blit(small.render(line, True, TEXT), (x, y))
                y += 20
        y += 12


    y = HEIGHT - 120
    pygame.draw.line(screen, PANEL_BORDER, (x, y-8), (panel.x + RIGHT_PANEL_W - 16, y-8), 1)
    pred = predicted_latency_ms()
    meas = imp.last_measured_ms
    items = [
        f"Predicted reflex time: {pred:0.1f} ms",
        f"Last measured time:    {meas:0.1f} ms" if meas else "Last measured time:    —",
        f"Current step:          {imp.current_step()}",
        f"Progress this step:    {imp.progress_pct():.0f} %",
        f"Synapse wait left:     {int(max(0.0, imp.wait)*1000)} ms",
    ]
    for s in items:
        screen.blit(mono.render(s, True, TEXT), (x, y))
        y += 20

# FINALLY. the main function. ironic cause everything important done is "outside" the main fn
def main():
    global last_watermark_name_rect
    show_panel = True
    hover_name = None

    while True:
        dt = clock.tick(FPS) / 1000.0
        mx, my = pygame.mouse.get_pos()
        hover_name = mouse_over_node(mx, my)

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit(); sys.exit()

            if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                # If user clicks on the watermark name, open GitHub
                if last_watermark_name_rect is not None and last_watermark_name_rect.collidepoint((mx, my)):
                    webbrowser.open(GITHUB_URL)
                else:
                    # otherwise, treat as stimulus or resume if paused
                    if imp.active and imp.paused:
                        imp.toggle_pause()
                    else:
                        imp.start()

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    # Space keeps existing behavior: start; if paused, resume
                    if imp.active and imp.paused:
                        imp.toggle_pause()
                    else:
                        imp.start()
                elif e.key == pygame.K_p:
                    imp.toggle_pause()  # <-- NEW: pause/resume
                elif e.key == pygame.K_UP:   imp.speed += 25.0
                elif e.key == pygame.K_DOWN: imp.speed = max(25.0, imp.speed - 25.0)
                elif e.key == pygame.K_q:    imp.d1 = min(0.05, imp.d1 + 0.001); imp.make_segments()
                elif e.key == pygame.K_a:    imp.d1 = max(0.0,  imp.d1 - 0.001); imp.make_segments()
                elif e.key == pygame.K_w:    imp.d2 = min(0.05, imp.d2 + 0.001); imp.make_segments()
                elif e.key == pygame.K_s:    imp.d2 = max(0.0,  imp.d2 - 0.001); imp.make_segments()
                elif e.key == pygame.K_r:
                    imp.speed = SPEED_DEFAULT_PXPS
                    imp.d1 = DELAY_SENSORY_TO_SPINAL_DEFAULT
                    imp.d2 = DELAY_SPINAL_TO_MOTOR_DEFAULT
                    imp.make_segments()
                    # Do not force unpause; keep current paused state as-is
                elif e.key == pygame.K_l:
                    show_panel = not show_panel

        imp.update(dt)
        draw_scene(show_panel, hover_name=hover_name)
        pygame.display.flip()

if __name__ == "__main__":
    main()
