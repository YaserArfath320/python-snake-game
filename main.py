"""
SNAKE — Full Featured Kivy Mobile Game
- 20x20 Grid
- Levels (speed increases every 5 foods)
- Walls mode ON/OFF
- High Score (session)
- Bonus food + Shield power-up
- Touch D-Pad controls
Run: py -3.12 main.py
APK: buildozer android debug
"""

from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.metrics import dp, sp
from kivy.utils import get_color_from_hex
from kivy.uix.screenmanager import ScreenManager, Screen
import random

Window.softinput_mode = 'below_target'

# ── Colours ───────────────────────────────────────────────────────────────────
BG       = get_color_from_hex("#0A0A0A")
WALL_C   = get_color_from_hex("#1a1aff")
SNAKE_H  = get_color_from_hex("#00FF88")
SNAKE_B  = get_color_from_hex("#00CC66")
SNAKE_T  = get_color_from_hex("#008844")
FOOD_C   = get_color_from_hex("#FF4444")
BONUS_C  = get_color_from_hex("#FFD700")
SHIELD_C = get_color_from_hex("#00CFFF")
WHITE    = (1, 1, 1, 1)
ACCENT   = get_color_from_hex("#FF6B35")
GREEN    = get_color_from_hex("#00FF88")
YELLOW   = get_color_from_hex("#FFD700")
RED      = get_color_from_hex("#FF4444")
MUTED    = get_color_from_hex("#888888")

Window.clearcolor = BG

COLS = 20
ROWS = 20
HIGH_SCORE = [0]


# ── D-Pad ─────────────────────────────────────────────────────────────────────
class DPad(Widget):
    def __init__(self, on_dir, **kwargs):
        super().__init__(**kwargs)
        self.on_dir = on_dir
        self.bind(pos=self._draw, size=self._draw)

    def _draw(self, *_):
        self.canvas.clear()
        x, y = self.pos
        w, h = self.size
        b    = min(w, h) / 3
        with self.canvas:
            for bx, by in [(x+b,y+b*2),(x+b,y),(x,y+b),(x+b*2,y+b)]:
                Color(0.2, 0.2, 0.2, 0.9)
                RoundedRectangle(pos=(bx+3,by+3), size=(b-6,b-6), radius=[dp(12)])
            Color(*ACCENT, 0.95)
            # Up
            cx,cy = x+b+b/2, y+b*2+b/2
            Line(points=[cx,cy+b*.24, cx-b*.2,cy-b*.18, cx+b*.2,cy-b*.18], width=2.4, close=True)
            # Down
            cx,cy = x+b+b/2, y+b/2
            Line(points=[cx,cy-b*.24, cx-b*.2,cy+b*.18, cx+b*.2,cy+b*.18], width=2.4, close=True)
            # Left
            cx,cy = x+b/2, y+b+b/2
            Line(points=[cx-b*.24,cy, cx+b*.18,cy+b*.2, cx+b*.18,cy-b*.2], width=2.4, close=True)
            # Right
            cx,cy = x+b*2+b/2, y+b+b/2
            Line(points=[cx+b*.24,cy, cx-b*.18,cy+b*.2, cx-b*.18,cy-b*.2], width=2.4, close=True)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._handle(touch)
            return True

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            self._handle(touch)
            return True

    def _handle(self, touch):
        x, y = self.pos
        w, h = self.size
        b    = min(w, h) / 3
        cx   = x + b * 1.5
        cy   = y + b * 1.5
        dx   = touch.x - cx
        dy   = touch.y - cy
        if abs(dx) > abs(dy):
            self.on_dir((0, 1) if dx > 0 else (0, -1))
        else:
            self.on_dir((-1, 0) if dy > 0 else (1, 0))


# ── Snake Game ────────────────────────────────────────────────────────────────
class SnakeGame(Widget):
    def __init__(self, on_over, level=1, walls=True, **kwargs):
        super().__init__(**kwargs)
        self.on_over     = on_over
        self.walls       = walls
        self.level       = level
        self.score       = 0
        self.foods_eaten = 0

        mid_r = ROWS // 2
        mid_c = COLS // 2
        self.snake  = [(mid_r, mid_c), (mid_r, mid_c-1), (mid_r, mid_c-2)]
        self.dir    = (0, 1)
        self.next_d = (0, 1)

        self.food        = None
        self.bonus_food  = None
        self.bonus_timer = 0
        self.shield      = False
        self.shield_t    = 0
        self.shield_item = None

        self._place_food()
        self.active = True
        self.bind(pos=self._draw, size=self._draw)

        interval = max(0.08, 0.18 - (level-1)*0.01)
        self._tick = Clock.schedule_interval(self.update, interval)

    def stop(self):
        self._tick.cancel()

    def set_dir(self, d):
        if (d[0]+self.dir[0], d[1]+self.dir[1]) != (0, 0):
            self.next_d = d

    def _free_cells(self):
        occupied = set(self.snake)
        if self.bonus_food: occupied.add(self.bonus_food)
        if self.shield_item: occupied.add(self.shield_item)
        if self.food: occupied.add(self.food)
        return [(r,c) for r in range(ROWS) for c in range(COLS) if (r,c) not in occupied]

    def _place_food(self):
        free = self._free_cells()
        if free:
            self.food = random.choice(free)

    def _place_bonus(self):
        free = self._free_cells()
        if free:
            self.bonus_food  = random.choice(free)
            self.bonus_timer = 8.0

    def _place_shield(self):
        free = self._free_cells()
        if free:
            self.shield_item = random.choice(free)

    def update(self, dt):
        if not self.active:
            return

        self.dir = self.next_d

        if self.bonus_food:
            self.bonus_timer -= dt
            if self.bonus_timer <= 0:
                self.bonus_food = None

        if self.shield:
            self.shield_t -= dt
            if self.shield_t <= 0:
                self.shield = False

        hr, hc = self.snake[0]
        nr = hr + self.dir[0]
        nc = hc + self.dir[1]

        # Wall collision
        if self.walls:
            if nr < 0 or nr >= ROWS or nc < 0 or nc >= COLS:
                if self.shield:
                    self.shield = False
                    self._draw()
                    return
                self._die()
                return
        else:
            nr = nr % ROWS
            nc = nc % COLS

        new_head = (nr, nc)

        # Self collision
        if new_head in self.snake[:-1]:
            if self.shield:
                self.shield = False
                self._draw()
                return
            self._die()
            return

        self.snake.insert(0, new_head)
        ate = False

        if new_head == self.food:
            self.score       += 10 * self.level
            self.foods_eaten += 1
            self._place_food()
            ate = True
            if self.foods_eaten % 5 == 0:
                self._place_bonus()
            if self.foods_eaten % 7 == 0:
                self._place_shield()
            if self.foods_eaten % 5 == 0:
                self.level += 1
                new_interval = max(0.08, 0.18-(self.level-1)*0.01)
                self._tick.cancel()
                self._tick = Clock.schedule_interval(self.update, new_interval)

        elif new_head == self.bonus_food:
            self.score       += 50 * self.level
            self.foods_eaten += 1
            self.bonus_food   = None
            ate = True

        elif new_head == self.shield_item:
            self.shield      = True
            self.shield_t    = 5.0
            self.shield_item = None

        if not ate:
            self.snake.pop()

        if self.score > HIGH_SCORE[0]:
            HIGH_SCORE[0] = self.score

        self._draw()

    def _die(self):
        self.active = False
        self.stop()
        self.on_over(self.score, self.level, HIGH_SCORE[0])

    def _draw(self, *_):
        self.canvas.clear()
        if self.width < 1 or self.height < 1:
            return

        cw = self.width  / COLS
        ch = self.height / ROWS

        with self.canvas:
            Color(*BG)
            Rectangle(pos=self.pos, size=self.size)

            # Grid lines
            Color(0.08, 0.08, 0.08, 1)
            for r in range(ROWS+1):
                y = self.y + r*ch
                Line(points=[self.x, y, self.x+self.width, y], width=0.5)
            for c in range(COLS+1):
                x = self.x + c*cw
                Line(points=[x, self.y, x, self.y+self.height], width=0.5)

            # Wall border
            if self.walls:
                Color(*WALL_C, 0.9)
                Line(rectangle=(self.x, self.y, self.width, self.height), width=3)

            # Shield item
            if self.shield_item:
                r, c = self.shield_item
                sx = self.x + c*cw
                sy = self.y + (ROWS-1-r)*ch
                Color(*SHIELD_C)
                s  = min(cw,ch)*0.7
                ox = (cw-s)/2
                oy = (ch-s)/2
                Ellipse(pos=(sx+ox, sy+oy), size=(s,s))

            # Bonus food
            if self.bonus_food:
                r, c = self.bonus_food
                bx = self.x + c*cw
                by = self.y + (ROWS-1-r)*ch
                Color(*BONUS_C)
                s  = min(cw,ch)*0.75
                ox = (cw-s)/2
                oy = (ch-s)/2
                RoundedRectangle(pos=(bx+ox, by+oy), size=(s,s), radius=[dp(4)])

            # Normal food
            if self.food:
                r, c = self.food
                fx = self.x + c*cw
                fy = self.y + (ROWS-1-r)*ch
                Color(*FOOD_C)
                s  = min(cw,ch)*0.65
                ox = (cw-s)/2
                oy = (ch-s)/2
                Ellipse(pos=(fx+ox, fy+oy), size=(s,s))

            # Snake body
            n = len(self.snake)
            for i, (r, c) in enumerate(self.snake):
                sx  = self.x + c*cw
                sy  = self.y + (ROWS-1-r)*ch
                pad = 1.5

                if i == 0:
                    Color(*SHIELD_C) if self.shield else Color(*SNAKE_H)
                    RoundedRectangle(pos=(sx+pad, sy+pad),
                                     size=(cw-pad*2, ch-pad*2),
                                     radius=[dp(5)])
                    # Eyes
                    Color(0,0,0,1)
                    ew = cw*0.18
                    Ellipse(pos=(sx+cw*0.25, sy+ch*0.55), size=(ew,ew))
                    Ellipse(pos=(sx+cw*0.57, sy+ch*0.55), size=(ew,ew))

                elif i == n-1:
                    Color(*SNAKE_T)
                    s  = min(cw,ch)*0.55
                    ox = (cw-s)/2
                    oy = (ch-s)/2
                    RoundedRectangle(pos=(sx+ox, sy+oy), size=(s,s), radius=[dp(4)])

                else:
                    t   = i / max(n-1, 1)
                    rc  = SNAKE_B[0]*(1-t) + SNAKE_T[0]*t
                    gc  = SNAKE_B[1]*(1-t) + SNAKE_T[1]*t
                    bc  = SNAKE_B[2]*(1-t) + SNAKE_T[2]*t
                    Color(rc, gc, bc, 1)
                    RoundedRectangle(pos=(sx+pad, sy+pad),
                                     size=(cw-pad*2, ch-pad*2),
                                     radius=[dp(3)])


# ── Game Screen ───────────────────────────────────────────────────────────────
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._level = 1
        self._walls = True
        self._root  = None
        self._game  = None
        self._tick  = None

    def on_enter(self):
        self._build()

    def on_leave(self):
        if self._game: self._game.stop()
        if self._tick: self._tick.cancel()

    def _build(self):
        if self._root:
            self.remove_widget(self._root)

        root = FloatLayout()

        # HUD
        hud = BoxLayout(orientation='horizontal',
                        size_hint=(1,None), height=dp(42),
                        pos_hint={'top':1},
                        padding=[dp(10),dp(4)], spacing=dp(4))
        with hud.canvas.before:
            Color(0,0,0,1)
            hud._bg = Rectangle(pos=hud.pos, size=hud.size)
        hud.bind(pos=lambda w,_: setattr(w._bg,'pos',w.pos),
                 size=lambda w,_: setattr(w._bg,'size',w.size))

        self._sc_lbl  = Label(text="0",    font_size=sp(14), bold=True, color=YELLOW)
        self._lv_lbl  = Label(text="Lv 1", font_size=sp(14), bold=True, color=GREEN)
        self._hi_lbl  = Label(text="HI 0", font_size=sp(14), bold=True, color=ACCENT)
        self._sh_lbl  = Label(text="",     font_size=sp(14), bold=True, color=SHIELD_C)
        for lbl in [self._sc_lbl, self._lv_lbl, self._hi_lbl, self._sh_lbl]:
            hud.add_widget(lbl)
        root.add_widget(hud)

        # D-Pad bottom center
        ds = dp(210)
        dpad = DPad(on_dir=self._dir,
                    size_hint=(None,None), size=(ds,ds),
                    pos_hint={'center_x':0.5,'y':0.01})
        root.add_widget(dpad)

        # Game
        self._game = SnakeGame(
            on_over=self._over,
            level=self._level,
            walls=self._walls,
            size_hint=(None,None),
            size=(Window.width, Window.width),
            pos=(0, dp(220))
        )
        root.add_widget(self._game)
        Clock.schedule_once(self._fit, 0.05)

        self._root = root
        self.add_widget(root)
        self._tick = Clock.schedule_interval(self._upd_hud, 1/10)

    def _fit(self, *_):
        dpad_h  = dp(225)
        hud_h   = dp(42)
        avail_h = Window.height - hud_h - dpad_h
        avail_w = Window.width
        cell    = min(avail_w/COLS, avail_h/ROWS)
        gw      = cell * COLS
        gh      = cell * ROWS
        self._game.size = (gw, gh)
        self._game.pos  = ((Window.width-gw)/2, dpad_h)

    def _dir(self, d):
        if self._game: self._game.set_dir(d)

    def _upd_hud(self, *_):
        if not self._game: return
        self._sc_lbl.text = str(self._game.score)
        self._lv_lbl.text = f"Lv {self._game.level}"
        self._hi_lbl.text = f"HI {HIGH_SCORE[0]}"
        self._sh_lbl.text = "[SHIELD]" if self._game.shield else ""

    def _over(self, score, level, hi):
        s = self.manager.get_screen('over')
        s.score = score
        s.level = level
        s.hi    = hi
        self.manager.current = 'over'

    def restart(self, level=1, walls=True):
        self._level = level
        self._walls = walls


# ── Menu Screen ───────────────────────────────────────────────────────────────
class MenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.walls = True
        lo = BoxLayout(orientation='vertical', padding=dp(36), spacing=dp(16))
        lo.add_widget(Widget())
        lo.add_widget(Label(text="~~ SNAKE ~~", font_size=sp(52), bold=True, color=GREEN))
        lo.add_widget(Label(text="Eat RED food to grow!", font_size=sp(16), color=(0.9,0.3,0.3,1), halign='center'))
        lo.add_widget(Label(text="Avoid walls and yourself!", font_size=sp(16), color=(0.8,0.8,0.8,1), halign='center'))
        lo.add_widget(Label(text="GOLD food = bonus points!", font_size=sp(16), color=get_color_from_hex("#FFD700"), halign='center'))
        lo.add_widget(Label(text="BLUE item = shield power!", font_size=sp(16), color=get_color_from_hex("#00CFFF"), halign='center'))
        lo.add_widget(Widget())

        self._wall_btn = Button(
            text="[ WALLS: ON ]",
            font_size=sp(17), size_hint_y=None, height=dp(52),
            background_normal='', background_color=get_color_from_hex("#222266"),
            color=WHITE
        )
        self._wall_btn.bind(on_press=self._toggle)
        lo.add_widget(self._wall_btn)

        play = Button(text="PLAY", font_size=sp(24), bold=True,
                      size_hint_y=None, height=dp(68),
                      background_normal='', background_color=GREEN,
                      color=(0,0,0,1))
        play.bind(on_press=self._play)
        lo.add_widget(play)
        lo.add_widget(Widget())
        self.add_widget(lo)

    def _toggle(self, *_):
        self.walls = not self.walls
        if self.walls:
            self._wall_btn.text = "[ WALLS: ON ]"
            self._wall_btn.background_color = get_color_from_hex("#222266")
        else:
            self._wall_btn.text = "[ WALLS: OFF - wrap ]"
            self._wall_btn.background_color = get_color_from_hex("#226622")

    def _play(self, *_):
        gs = self.manager.get_screen('game')
        gs.restart(level=1, walls=self.walls)
        self.manager.current = 'game'


# ── Game Over Screen ──────────────────────────────────────────────────────────
class OverScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.score = 0
        self.level = 1
        self.hi    = 0

        lo = BoxLayout(orientation='vertical', padding=dp(36), spacing=dp(16))
        lo.add_widget(Widget())
        lo.add_widget(Label(text="GAME OVER", font_size=sp(42), bold=True, color=RED))

        self._sc = Label(text="Score: 0",  font_size=sp(24), color=YELLOW)
        self._lv = Label(text="Level: 1",  font_size=sp(18), color=WHITE)
        self._hi = Label(text="Best: 0",   font_size=sp(18), color=ACCENT)
        self._nw = Label(text="",          font_size=sp(20), bold=True, color=GREEN)

        for lbl in [self._sc, self._lv, self._hi, self._nw]:
            lo.add_widget(lbl)
        lo.add_widget(Widget())

        b1 = Button(text="PLAY AGAIN", font_size=sp(20), bold=True,
                    size_hint_y=None, height=dp(62),
                    background_normal='', background_color=GREEN, color=(0,0,0,1))
        b1.bind(on_press=self._retry)

        b2 = Button(text="MENU", font_size=sp(17),
                    size_hint_y=None, height=dp(50),
                    background_normal='', background_color=(0.2,0.2,0.2,1), color=WHITE)
        b2.bind(on_press=lambda _: setattr(self.manager,'current','menu'))

        lo.add_widget(b1)
        lo.add_widget(b2)
        lo.add_widget(Widget())
        self.add_widget(lo)

    def on_enter(self):
        self._sc.text = f"Score: {self.score}"
        self._lv.text = f"Level reached: {self.level}"
        self._hi.text = f"Best: {self.hi}"
        self._nw.text = "** NEW HIGH SCORE! **" if self.score >= self.hi > 0 else ""

    def _retry(self, *_):
        gs = self.manager.get_screen('game')
        gs.restart(level=1)
        self.manager.current = 'game'


# ── App ───────────────────────────────────────────────────────────────────────
class SnakeApp(App):
    def build(self):
        self.title = "Snake"
        sm = ScreenManager()
        sm.add_widget(MenuScreen(name='menu'))
        sm.add_widget(GameScreen(name='game'))
        sm.add_widget(OverScreen(name='over'))
        return sm


if __name__ == "__main__":
    SnakeApp().run()