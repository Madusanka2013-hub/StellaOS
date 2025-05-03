import tkinter as tk
import random

CELL_SIZE = 20
TICK_MS = 100
TOP_PADDING = 40
DIVIDER_WIDTH = 2
BACKGROUND_COLOR = "#1d1f21"
SNAKE_COLOR = "#4CAF50"
FOOD_COLOR = "#FF9800"
OBSTACLE_COLOR = "#F44336"
SCORE_BACKGROUND_COLOR = "#333C57"
DIVIDER_COLOR = "#FFFFFF"
POWERUP_COLOR = "#FFEB3B"
SHIELD_COLOR = "#00BCD4"

class SnakeGame:
    def __init__(self, root, parent):
        self.root = root
        self.parent = parent
        self.root.after(100, self.create_canvas)

    def create_canvas(self):
        self.width = self.parent.winfo_width()
        self.height = self.parent.winfo_height() - 150
        self.canvas = tk.Canvas(self.parent, bg=BACKGROUND_COLOR, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.create_rectangle(0, 0, self.width, TOP_PADDING,
            fill=SCORE_BACKGROUND_COLOR, outline="", width=0, tags="score_background")
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.root.bind("<KeyPress>", self.change_direction)

        self.snake = []
        self.snake_direction = 'Right'
        self.food = None
        self.obstacles = []
        self.powerups = []
        self.score = 0
        self.level = 1
        self.score_text_id = None
        self.level_text_id = None
        self.shield_icon_id = None
        self.shield_text_id = None
        self.multiplier_icon_id = None
        self.multiplier_text_id = None
        self.shield_active = False
        self.shield_timer = 0
        self.multiplier_active = False
        self.multiplier_timer = 0
        self.shield_colors = ["#9C27B0", "#BA68C8", "#CE93D8"]
        self.shield_color_index = 0
        self.multiplier_colors = ["#FF5722", "#FF7043", "#FF8A65"]
        self.running = False
        self.after_id = None
        self.restart_button = None
        self.enemy_snake = []
        self.enemy_direction = 'Right'
        self.enemy_move_tick = 0
        self.enemy_change_freq = 3
        self.parent.bind("<<ContentResized>>", self.handle_resize_event)

    def on_canvas_resize(self, event):
        self.width = event.width
        self.height = event.height
        if not hasattr(self, "start_button_window"):
            self.start_button = tk.Button(self.canvas, text="Start Game", command=self.start_game, font=("Arial", 14), width=12, bg="#00b300", fg="white")
            self.start_button_window = self.canvas.create_window(self.width // 2, self.height // 2, window=self.start_button)
        else:
            self.canvas.coords(self.start_button_window, self.width // 2, self.height // 2)

    def handle_resize_event(self, event=None):
        w = self.parent.winfo_width()
        h = self.parent.winfo_height()
        self.canvas.config(width=w, height=h)
        self.width = w
        self.height = h - 150
        if hasattr(self, "start_button_window"):
            self.canvas.coords(self.start_button_window, w // 2, h // 2)

    def start_game(self):
        self.canvas.delete("all")
        self.score = 0
        self.level = 1
        self.enemy_snake = []
        self.enemy_direction = 'Right'
        self.enemy_move_tick = 0
        self.init_game()
        self.canvas.create_rectangle(0, 0, self.width, TOP_PADDING,
            fill=SCORE_BACKGROUND_COLOR, outline="", width=2, tags="score_background")
        self.running = True
        self.after_id = self.canvas.after(TICK_MS, self.run_game)
        self.root.focus_force()

    def init_game(self):
        self.snake = [(100, 100), (80, 100), (60, 100)]
        self.snake_direction = 'Right'
        self.food = self.create_food()
        self.obstacles = self.create_obstacles(5 + (self.level - 1) * 2)
        self.powerups = self.create_powerups()
        self.update_snake()
        self.draw_food()
        self.draw_obstacles()
        self.draw_powerups()
        self.update_score()

    def update_score(self):
        if self.score_text_id:
            self.canvas.delete(self.score_text_id)
        if self.level_text_id:
            self.canvas.delete(self.level_text_id)
        self.canvas.delete("shield_text")
        self.canvas.delete("multiplier_text")
        shield_x = self.width - 140
        multiplier_x = self.width - 320
        shield_y = TOP_PADDING // 2 - 10
        multiplier_y = TOP_PADDING // 2 - 10
        shield_color_in_field = "#555555"
        for p in self.powerups:
            if p['type'] == 'shield':
                shield_color_in_field = p.get('color', SHIELD_COLOR)
                break
        multiplier_color_in_field = "#555555"
        for p in self.powerups:
            if p['type'] == 'multiplier':
                multiplier_color_in_field = p.get('color', self.multiplier_colors[0])
                break
        self.score_text_id = self.canvas.create_text(self.width // 2 - 80, TOP_PADDING // 2,
            text=f"Score: {self.score}", fill="white", font=("Arial", 16), tags="score")
        self.level_text_id = self.canvas.create_text(self.width // 2 + 40, TOP_PADDING // 2,
            text=f"Level: {self.level}", fill="white", font=("Arial", 16), tags="level")
        self.shield_icon_id = self.canvas.create_rectangle(shield_x, shield_y, shield_x + 20, shield_y + 20,
            fill=SHIELD_COLOR if self.shield_active else shield_color_in_field, outline="black")
        shield_text = f"Schild ({int(self.shield_timer)})" if self.shield_active else "Schild"
        self.shield_text_id = self.canvas.create_text(shield_x + 60, TOP_PADDING // 2,
            text=shield_text, fill="white", font=("Arial", 12), tags="shield_text")
        self.multiplier_icon_id = self.canvas.create_rectangle(multiplier_x, multiplier_y, multiplier_x + 20, multiplier_y + 20,
            fill=self.multiplier_colors[0] if self.multiplier_active else multiplier_color_in_field, outline="black")
        multiplier_text = f"Multiplikator ({int(self.multiplier_timer)})" if self.multiplier_active else "Multiplikator"
        self.multiplier_text_id = self.canvas.create_text(multiplier_x + 80, TOP_PADDING // 2,
            text=multiplier_text, fill="white", font=("Arial", 12), tags="multiplier_text")

    def create_food(self):
        while True:
            x = random.randint(0, (self.width // CELL_SIZE) - 1) * CELL_SIZE
            y = random.randint(0, ((self.height - TOP_PADDING - DIVIDER_WIDTH) // CELL_SIZE) - 1) * CELL_SIZE
            pos = (x, y)
            if pos not in self.snake and pos not in self.obstacles:
                return pos

    def create_obstacles(self, count=5):
        obstacles = []
        while len(obstacles) < count:
            x = random.randint(0, (self.width // CELL_SIZE) - 1) * CELL_SIZE
            y = random.randint(0, ((self.height - TOP_PADDING - DIVIDER_WIDTH) // CELL_SIZE) - 1) * CELL_SIZE
            pos = (x, y)
            too_close = any(abs(x - sx) < 2*CELL_SIZE and abs(y - sy) < 2*CELL_SIZE for (sx, sy) in self.snake)
            if pos not in self.snake and pos != self.food and not too_close:
                obstacles.append(pos)
        return obstacles

    def create_powerups(self, count=3):
        powerups = []
        while len(powerups) < count:
            x = random.randint(0, (self.width // CELL_SIZE) - 1) * CELL_SIZE
            y = random.randint(0, ((self.height - TOP_PADDING - DIVIDER_WIDTH) // CELL_SIZE) - 1) * CELL_SIZE
            pos = (x, y)
            if pos not in self.snake and pos != self.food:
                rand = random.random()
                if rand < 0.33:
                    powerups.append({'pos': pos, 'type': 'shield', 'color': SHIELD_COLOR})
                elif rand < 0.66:
                    powerups.append({'pos': pos, 'type': 'multiplier', 'color': self.multiplier_colors[0]})
                else:
                    powerups.append({'pos': pos, 'type': 'normal'})
        return powerups

    def update_snake(self):
        self.canvas.delete("snake")
        for x, y in self.snake:
            color = self.shield_colors[self.shield_color_index] if self.shield_active else SNAKE_COLOR
            self.canvas.create_rectangle(x, y + TOP_PADDING, x + CELL_SIZE, y + CELL_SIZE + TOP_PADDING,
                fill=color, outline="black", tags="snake")

    def draw_food(self):
        self.canvas.delete("food")
        food_x, food_y = self.food
        self.canvas.create_rectangle(food_x, food_y + TOP_PADDING, food_x + CELL_SIZE, food_y + CELL_SIZE + TOP_PADDING,
            fill=FOOD_COLOR, outline="black", tags="food")

    def draw_obstacles(self):
        self.canvas.delete("obstacle")
        for ox, oy in self.obstacles:
            self.canvas.create_rectangle(ox, oy + TOP_PADDING, ox + CELL_SIZE, oy + CELL_SIZE + TOP_PADDING,
                fill=OBSTACLE_COLOR, outline="black", tags="obstacle")

    def draw_powerups(self):
        self.canvas.delete("powerup")
        for p in self.powerups:
            px, py = p['pos']
            color = p['color'] if p['type'] in ['shield', 'multiplier'] else POWERUP_COLOR
            self.canvas.create_rectangle(px, py + TOP_PADDING, px + CELL_SIZE, py + CELL_SIZE + TOP_PADDING,
                fill=color, outline="black", tags="powerup")

    def draw_enemy_snake(self):
        self.canvas.delete("enemy_snake")
        for x, y in self.enemy_snake:
            self.canvas.create_rectangle(x, y + TOP_PADDING, x + CELL_SIZE, y + CELL_SIZE + TOP_PADDING,
                fill="#FF00FF", outline="black", tags="enemy_snake")

    def spawn_enemy_snake(self):
        length = 3 + max(0, self.level - 10)
        while True:
            start_x = random.randint(length + 2, (self.width // CELL_SIZE) - 3) * CELL_SIZE
            start_y = random.randint(3, ((self.height - TOP_PADDING - DIVIDER_WIDTH) // CELL_SIZE) - 1) * CELL_SIZE
            new_snake = [(start_x - CELL_SIZE * i, start_y) for i in range(length)]
            if not any(seg in self.snake or seg in self.obstacles for seg in new_snake):
                self.enemy_snake = new_snake
                self.enemy_direction = random.choice(['Up', 'Down', 'Left', 'Right'])
                break

    def move_enemy_snake(self):
        if not self.enemy_snake:
            return

        self.enemy_move_tick += 1
        if self.enemy_move_tick % self.enemy_change_freq == 0:
            directions = ['Up', 'Down', 'Left', 'Right']
            random.shuffle(directions)
            for dir in directions:
                if dir == self.enemy_direction:
                    continue
                dx, dy = 0, 0
                if dir == 'Up': dy = -CELL_SIZE
                elif dir == 'Down': dy = CELL_SIZE
                elif dir == 'Left': dx = -CELL_SIZE
                elif dir == 'Right': dx = CELL_SIZE
                new_head = ((self.enemy_snake[0][0] + dx) % self.width,
                            (self.enemy_snake[0][1] + dy) % (self.height - TOP_PADDING - DIVIDER_WIDTH))
                if new_head not in self.obstacles:
                    self.enemy_direction = dir
                    break

        dx, dy = 0, 0
        if self.enemy_direction == 'Up': dy = -CELL_SIZE
        elif self.enemy_direction == 'Down': dy = CELL_SIZE
        elif self.enemy_direction == 'Left': dx = -CELL_SIZE
        elif self.enemy_direction == 'Right': dx = CELL_SIZE

        new_head = ((self.enemy_snake[0][0] + dx) % self.width,
                    (self.enemy_snake[0][1] + dy) % (self.height - TOP_PADDING - DIVIDER_WIDTH))
        self.enemy_snake = [new_head] + self.enemy_snake[:-1]

    def change_direction(self, event):
        if event.keysym == 'Up' and self.snake_direction != 'Down':
            self.snake_direction = 'Up'
        elif event.keysym == 'Down' and self.snake_direction != 'Up':
            self.snake_direction = 'Down'
        elif event.keysym == 'Left' and self.snake_direction != 'Right':
            self.snake_direction = 'Left'
        elif event.keysym == 'Right' and self.snake_direction != 'Left':
            self.snake_direction = 'Right'

    def move_snake(self):
        head_x, head_y = self.snake[0]
        if self.snake_direction == 'Up':
            head_y -= CELL_SIZE
        elif self.snake_direction == 'Down':
            head_y += CELL_SIZE
        elif self.snake_direction == 'Left':
            head_x -= CELL_SIZE
        elif self.snake_direction == 'Right':
            head_x += CELL_SIZE
        head_x %= self.width
        head_y %= (self.height - TOP_PADDING - DIVIDER_WIDTH)
        new_head = (head_x, head_y)
        self.snake = [new_head] + self.snake[:-1]

    def check_collisions(self):
        head = self.snake[0]
        if (not self.shield_active) and (head in self.snake[1:] or head in self.obstacles):
            self.running = False
            self.show_restart_button()

        if head == self.food:
            self.snake.append(self.snake[-1])
            self.food = self.create_food()
            self.score += 2 if self.multiplier_active else 1
            if self.score // 5 >= self.level:
                self.level += 1
                self.obstacles = self.create_obstacles(5 + (self.level - 1) * 2)
            self.update_score()
            self.draw_obstacles()

        if self.level >= 10 and not self.enemy_snake:
            self.spawn_enemy_snake()

        if head in self.enemy_snake and not self.shield_active:
            self.running = False
            self.show_restart_button()

        for p in self.powerups:
            if abs(head[0] - p['pos'][0]) < CELL_SIZE and abs(head[1] - p['pos'][1]) < CELL_SIZE:
                if p['type'] == 'shield':
                    self.shield_active = True
                    self.shield_timer = 10
                elif p['type'] == 'multiplier':
                    self.multiplier_active = True
                    self.multiplier_timer = 10
                else:
                    self.score += 2
                self.powerups.remove(p)

    def show_restart_button(self):
        if self.restart_button:
            self.restart_button.destroy()
        self.restart_button = tk.Button(self.canvas, text="Restart", command=self.restart_game, font=("Arial", 14), width=12, bg="#FF5733", fg="white")
        self.canvas.create_window(self.width // 2, self.height // 2 + 40, window=self.restart_button)

    def restart_game(self):
        self.canvas.delete("all")
        self.start_game()
        
    def run_game(self):
        if self.running:
            self.move_snake()
            self.check_collisions()
            self.update_snake()
            self.draw_food()
            self.draw_obstacles()
            self.draw_powerups()

            if self.level >= 10:
                self.move_enemy_snake()
                self.draw_enemy_snake()

            if self.shield_active:
                self.shield_timer -= TICK_MS / 1000
                if self.shield_timer <= 0:
                    self.shield_active = False
                    self.shield_timer = 0
                self.shield_color_index = (self.shield_color_index + 1) % len(self.shield_colors)

            if self.multiplier_active:
                self.multiplier_timer -= TICK_MS / 1000
                if self.multiplier_timer <= 0:
                    self.multiplier_active = False
                    self.multiplier_timer = 0

            self.update_score()
            self.after_id = self.canvas.after(TICK_MS, self.run_game)
        else:
            self.canvas.create_text(self.width // 2, self.height // 2 - 20, text="GAME OVER", fill="red", font=("Arial", 24))

def main(parent):
    SnakeGame(parent.master, parent)
