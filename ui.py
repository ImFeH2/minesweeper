import random
import tkinter as tk
from copy import deepcopy
from dataclasses import dataclass
from tkinter import messagebox, ttk
from tkinter.font import Font
from typing import List, Optional

from solver import Action, MineSolver, generate_safe_mines


@dataclass
class GameState:
    """游戏状态快照"""
    mines: List[List[bool]]
    hints: List[List[int]]
    revealed: List[List[bool]]
    flagged: List[List[bool]]
    mines_remaining: int
    game_over: bool


@dataclass
class ReplayStep:
    """回放步骤，包含动作和执行后的状态"""
    action: Action
    state: GameState


class Settings:
    def __init__(self):
        self.width = 30
        self.height = 16
        self.mines = 99
        self.replay_speed = 1


class SettingsWindow:
    def __init__(self, parent, settings, callback):
        self.window = tk.Toplevel(parent)
        self.window.title("设置")
        self.settings = settings
        self.callback = callback

        self.window.configure(bg='#f0f0f0')
        self.window.geometry('300x300')
        style = ttk.Style()
        style.configure('Settings.TLabel', font=('Microsoft YaHei UI', 10))
        style.configure('Settings.TEntry', font=('Microsoft YaHei UI', 10))
        style.configure('Settings.TButton', font=('Microsoft YaHei UI', 10))

        main_frame = ttk.Frame(self.window, padding="20", style='Settings.TFrame')
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="宽度:", style='Settings.TLabel').grid(row=0, column=0, padx=5, pady=10, sticky=tk.W)
        self.width_var = tk.StringVar(value=str(settings.width))
        ttk.Entry(main_frame, textvariable=self.width_var, width=15).grid(row=0, column=1, padx=5, pady=10)

        ttk.Label(main_frame, text="高度:", style='Settings.TLabel').grid(row=1, column=0, padx=5, pady=10, sticky=tk.W)
        self.height_var = tk.StringVar(value=str(settings.height))
        ttk.Entry(main_frame, textvariable=self.height_var, width=15).grid(row=1, column=1, padx=5, pady=10)

        ttk.Label(main_frame, text="地雷数:", style='Settings.TLabel').grid(row=2, column=0, padx=5, pady=10, sticky=tk.W)
        self.mines_var = tk.StringVar(value=str(settings.mines))
        ttk.Entry(main_frame, textvariable=self.mines_var, width=15).grid(row=2, column=1, padx=5, pady=10)

        ttk.Label(main_frame, text="回放速度(秒):", style='Settings.TLabel').grid(row=3, column=0, padx=5, pady=10, sticky=tk.W)
        self.speed_var = tk.StringVar(value=str(settings.replay_speed))
        ttk.Entry(main_frame, textvariable=self.speed_var, width=15).grid(row=3, column=1, padx=5, pady=10)

        ttk.Button(main_frame, text="确定", command=self.apply_settings, style='Settings.TButton').grid(row=4, column=0, columnspan=2, pady=20)

    def apply_settings(self):
        try:
            width = int(self.width_var.get())
            height = int(self.height_var.get())
            mines = int(self.mines_var.get())
            speed = float(self.speed_var.get())

            if width < 5 or height < 5:
                messagebox.showerror("错误", "宽度和高度至少为5")
                return
            if mines >= width * height:
                messagebox.showerror("错误", "地雷数量不能大于或等于格子总数")
                return
            if speed <= 0:
                messagebox.showerror("错误", "回放速度必须大于0")
                return

            self.settings.width = width
            self.settings.height = height
            self.settings.mines = mines
            self.settings.replay_speed = speed
            self.callback()
            self.window.destroy()
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")


class Minesweeper:
    def __init__(self, master):
        self.master = master
        self.master.title("扫雷")
        self.settings = Settings()
        self.replay_timer: Optional[str] = None

        self.colors = {
            1: '#0000FF',  # 蓝色
            2: '#008000',  # 绿色
            3: '#FF0000',  # 红色
            4: '#000080',  # 深蓝色
            5: '#800000',  # 深红色
            6: '#008080',  # 青色
            7: '#000000',  # 黑色
            8: '#808080'   # 灰色
        }

        self._setup_ui()
        self.new_game()

    def _setup_ui(self):
        """初始化UI组件"""
        self.master.configure(bg='#f8f9fa')
        self.style = ttk.Style()
        self.style.configure('Game.TFrame', background='#f8f9fa')
        self.style.configure('Control.TButton', font=('Microsoft YaHei UI', 10))
        self.style.configure('Status.TLabel', font=('Microsoft YaHei UI', 12), background='#f8f9fa')

        # 创建主框架
        self.main_frame = ttk.Frame(self.master, style='Game.TFrame', padding="10")
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        # 创建顶部控制栏
        self.control_frame = ttk.Frame(self.main_frame, style='Game.TFrame')
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)

        # 左侧状态显示
        self.mine_count_label = ttk.Label(self.control_frame, style='Status.TLabel', text="💣 剩余: 0")
        self.mine_count_label.pack(side=tk.LEFT, padx=10)

        # 右侧控制按钮
        button_frame = ttk.Frame(self.control_frame, style='Game.TFrame')
        button_frame.pack(side=tk.RIGHT, padx=5)

        buttons = [
            ("新游戏", self.new_game),
            ("设置", self.open_settings),
            ("AI求解", self.start_ai_solve),
            ("暂停/继续", self.toggle_replay),
            ("后退", self.step_backward),
            ("前进", self.step_forward)
        ]

        for text, command in buttons:
            ttk.Button(button_frame, text=text, command=command, style='Control.TButton', width=8).pack(side=tk.LEFT, padx=2)

        # 创建游戏区域
        self.game_area = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.game_area.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

        # 左侧游戏区域
        self.left_frame = ttk.Frame(self.game_area, style='Game.TFrame')
        self.game_area.add(self.left_frame)
        self.game_frame = ttk.Frame(self.left_frame, style='Game.TFrame')
        self.game_frame.pack(padx=5, pady=5)

        # 右侧操作列表区域
        self.right_frame = ttk.Frame(self.game_area, style='Game.TFrame')
        self.game_area.add(self.right_frame)

        ttk.Label(self.right_frame, text="AI操作序列:",
                  font=('Microsoft YaHei UI', 10, 'bold')).pack(anchor=tk.W, padx=5, pady=5)

        # 创建操作列表框架
        action_container = ttk.Frame(self.right_frame)
        action_container.pack(fill=tk.BOTH, expand=True, padx=5)

        self.action_list = ttk.Treeview(action_container, columns=("step", "action"),
                                        show="headings", height=20)
        self.action_list.heading("step", text="步骤")
        self.action_list.heading("action", text="操作")
        self.action_list.column("step", width=50)
        self.action_list.column("action", width=150)

        action_scroll = ttk.Scrollbar(action_container, orient='vertical',
                                      command=self.action_list.yview)
        action_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.action_list.configure(yscrollcommand=action_scroll.set)
        self.action_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.action_list.bind("<Button-1>", self.on_action_selected)

        self.status_label = ttk.Label(self.right_frame, text="准备就绪",
                                      font=('Microsoft YaHei UI', 9))
        self.status_label.pack(pady=5, padx=5, side=tk.BOTTOM)

        self.button_font = Font(family='Microsoft YaHei UI', size=9, weight='bold')

    def new_game(self):
        """开始新游戏"""
        self.stop_replay()
        for widget in self.game_frame.winfo_children():
            widget.destroy()

        self.buttons = [[None for _ in range(self.settings.height)]
                        for _ in range(self.settings.width)]
        self.mines = [[False for _ in range(self.settings.height)]
                      for _ in range(self.settings.width)]
        self.hints = [[0 for _ in range(self.settings.height)]
                      for _ in range(self.settings.width)]
        self.revealed = [[False for _ in range(self.settings.height)]
                         for _ in range(self.settings.width)]
        self.flagged = [[False for _ in range(self.settings.height)]
                        for _ in range(self.settings.width)]

        for x in range(self.settings.width):
            for y in range(self.settings.height):
                self.buttons[x][y] = self.create_button(x, y)

        self.game_started = False
        self.game_over = False
        self.mines_remaining = self.settings.mines
        self.update_mine_count()

        self.replay_steps = []
        self.current_step = 0
        self.is_replaying = False
        self.solving = False

        for item in self.action_list.get_children():
            self.action_list.delete(item)
        self.status_label.config(text="准备就绪")

    def create_button(self, x, y):
        """创建一个游戏按钮"""
        btn = tk.Button(self.game_frame, width=2, height=1,
                        font=self.button_font,
                        relief=tk.RAISED,
                        bg='#e9ecef',
                        activebackground='#dee2e6')
        btn.grid(row=y, column=x, padx=1, pady=1)
        btn.bind('<Button-1>', lambda e, x=x, y=y: self.left_click(x, y))
        btn.bind('<Button-3>', lambda e, x=x, y=y: self.right_click(x, y))
        return btn

    def place_mines(self, first_x, first_y):
        """在首次点击后放置地雷"""
        # positions = [(x, y) for x in range(self.settings.width)
        #              for y in range(self.settings.height)
        #              if abs(x - first_x) > 1 or abs(y - first_y) > 1]
        # mine_positions = random.sample(positions, self.settings.mines)
        #
        # for x, y in mine_positions:
        #     self.mines[x][y] = True

        self.mines = generate_safe_mines(self.settings.mines, self.settings.width, self.settings.height, first_x, first_y)

        # Calculate hints
        for x in range(self.settings.width):
            for y in range(self.settings.height):
                count = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.settings.width and 0 <= ny < self.settings.height:
                            count += self.mines[nx][ny]
                self.hints[x][y] = count

    def start_ai_solve(self):
        """启动AI求解"""
        if self.solving or self.is_replaying or self.game_over:
            return
        self.solving = True

        self.status_label.config(text="AI正在思考中...")
        for item in self.action_list.get_children():
            self.action_list.delete(item)

        self.master.after(100, self.run_ai_solve)

    def run_ai_solve(self):
        """执行AI求解"""
        try:
            start_x = self.settings.width // 2
            start_y = self.settings.height // 2

            if not self.game_started:
                self.game_started = True
                self.place_mines(start_x, start_y)

            solver = MineSolver(self.mines)
            actions = solver.solve(start_x, start_y)

            initial_state = GameState(
                mines=deepcopy(self.mines),
                hints=deepcopy(self.hints),
                revealed=deepcopy(self.revealed),
                flagged=deepcopy(self.flagged),
                mines_remaining=self.mines_remaining,
                game_over=False
            )

            self.replay_steps = []
            current_state = initial_state

            for action in actions:
                next_state = GameState(
                    mines=deepcopy(current_state.mines),
                    hints=deepcopy(current_state.hints),
                    revealed=deepcopy(current_state.revealed),
                    flagged=deepcopy(current_state.flagged),
                    mines_remaining=current_state.mines_remaining,
                    game_over=current_state.game_over
                )

                if action.is_flag:
                    next_state.flagged[action.x][action.y] = True
                    next_state.mines_remaining -= 1
                else:
                    self.reveal_in_state(next_state, action.x, action.y)
                    if next_state.mines[action.x][action.y]:
                        next_state.game_over = True

                self.replay_steps.append(ReplayStep(action, next_state))
                current_state = next_state

            self.current_step = 0
            self.update_action_list()
            self.start_replay()
            self.status_label.config(text=f"共找到 {len(self.replay_steps)} 步操作")

        except Exception as e:
            self.status_label.config(text=f"AI求解出错: {str(e)}")
        finally:
            self.solving = False

    def reveal_in_state(self, state: GameState, x: int, y: int):
        """在指定状态上执行揭示操作"""
        if (not (0 <= x < self.settings.width and 0 <= y < self.settings.height) or
                state.revealed[x][y] or state.flagged[x][y]):
            return

        state.revealed[x][y] = True
        if state.hints[x][y] == 0:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    self.reveal_in_state(state, x + dx, y + dy)

    def update_action_list(self):
        """更新操作列表显示"""
        for item in self.action_list.get_children():
            self.action_list.delete(item)

        for i, step in enumerate(self.replay_steps):
            action_text = f"标记地雷" if step.action.is_flag else "点击格子"
            action_text += f" ({step.action.x}, {step.action.y})"
            item = self.action_list.insert("", "end", values=(i+1, action_text))

            if i == self.current_step - 1:
                self.action_list.selection_set(item)
                self.action_list.see(item)

    def on_action_selected(self, event):
        """处理操作列表的选择事件"""
        selection = self.action_list.selection()
        if not selection:
            return

        item = self.action_list.item(selection[0])
        step = int(item['values'][0]) - 1
        self.stop_replay()
        self.load_step(step)
        self.current_step = step + 1
        self.status_label.config(text=f"跳转到第 {self.current_step} 步")

    def load_step(self, index: int):
        """加载指定步骤的状态"""
        if 0 <= index < len(self.replay_steps):
            action = self.replay_steps[index].action
            state = self.replay_steps[index].state
            self.mines = deepcopy(state.mines)
            self.hints = deepcopy(state.hints)
            self.revealed = deepcopy(state.revealed)
            self.flagged = deepcopy(state.flagged)
            self.mines_remaining = state.mines_remaining
            self.game_over = state.game_over
            self.update_mine_count()
            self.update_board_display(action)

    def update_board_display(self, action: Action):
        for x in range(self.settings.width):
            for y in range(self.settings.height):
                btn = self.buttons[x][y]

                is_current = x == action.x and y == action.y

                if self.revealed[x][y]:
                    if self.mines[x][y]:
                        if is_current:
                            btn.config(text='💣', bg='#FF4040', relief=tk.SUNKEN)  # 更亮的红色
                        else:
                            btn.config(text='💣', bg='#FF6B6B', relief=tk.SUNKEN)
                    elif self.hints[x][y] > 0:
                        if is_current:
                            btn.config(text=str(self.hints[x][y]),
                                       relief=tk.SUNKEN,
                                       bg='#E6F3FF',  # 淡蓝色背景
                                       fg=self.colors[self.hints[x][y]])
                        else:
                            btn.config(text=str(self.hints[x][y]),
                                       relief=tk.SUNKEN,
                                       bg='#ffffff',
                                       fg=self.colors[self.hints[x][y]])
                    else:
                        if is_current:
                            btn.config(text='', relief=tk.SUNKEN, bg='#E6F3FF')  # 淡蓝色背景
                        else:
                            btn.config(text='', relief=tk.SUNKEN, bg='#ffffff')
                elif self.flagged[x][y]:
                    if is_current:
                        btn.config(text='🚩', relief=tk.RAISED, bg='#FFE6E6')  # 淡红色背景
                    else:
                        btn.config(text='🚩', relief=tk.RAISED, bg='#e0e0e0')
                else:
                    if is_current:
                        btn.config(text='', relief=tk.RAISED, bg='#E6F3FF')  # 淡蓝色背景
                    else:
                        btn.config(text='', relief=tk.RAISED, bg='#e0e0e0')

    def start_replay(self):
        """开始回放"""
        self.is_replaying = True
        self.play_next_step()

    def stop_replay(self):
        """停止回放"""
        self.is_replaying = False
        if self.replay_timer:
            self.master.after_cancel(self.replay_timer)
            self.replay_timer = None

    def toggle_replay(self):
        """切换回放状态"""
        if not self.replay_steps:
            self.status_label.config(text="没有可回放的操作")
            return

        if self.is_replaying:
            self.stop_replay()
            self.status_label.config(text="回放已暂停")
        else:
            self.start_replay()
            self.status_label.config(text="正在回放...")

    def play_next_step(self):
        """播放下一步"""
        if not self.is_replaying or self.current_step >= len(self.replay_steps):
            self.stop_replay()
            return

        current_replay_step = self.replay_steps[self.current_step]
        current_action = current_replay_step.action
        self.load_step(self.current_step)

        # 检查是否游戏结束
        if current_replay_step.state.game_over:
            self.stop_replay()
            if not current_action.is_flag:  # 如果是点击操作导致的游戏结束
                self.status_label.config(text="游戏结束：AI踩到地雷了！")
                messagebox.showinfo("游戏结束", "AI踩到地雷了！")
            return

        self.current_step += 1
        self.update_action_list()

        speed_ms = int(self.settings.replay_speed)
        self.replay_timer = self.master.after(speed_ms, self.play_next_step)

    def step_backward(self):
        """后退一步"""
        if self.current_step > 0:
            self.stop_replay()
            self.current_step -= 1
            self.load_step(max(0, self.current_step - 1))
            self.status_label.config(text=f"后退到第 {self.current_step} 步")
            self.update_action_list()

    def step_forward(self):
        """前进一步"""
        if self.current_step < len(self.replay_steps):
            self.stop_replay()
            current_replay_step = self.replay_steps[self.current_step]
            current_action = current_replay_step.action
            self.load_step(self.current_step)
            self.current_step += 1

            if current_replay_step.state.game_over:
                if not current_action.is_flag:
                    self.status_label.config(text="游戏结束：AI踩到地雷了！")
                    messagebox.showinfo("游戏结束", "AI踩到地雷了！")
            else:
                self.status_label.config(text=f"前进到第 {self.current_step} 步")
            self.update_action_list()

    def open_settings(self):
        """打开设置窗口"""
        SettingsWindow(self.master, self.settings, self.new_game)

    def update_mine_count(self):
        """更新剩余地雷数显示"""
        self.mine_count_label.config(text=f"💣 剩余: {self.mines_remaining}")

    def reveal(self, x, y):
        """揭示一个格子"""
        if (not (0 <= x < self.settings.width and 0 <= y < self.settings.height) or
                self.revealed[x][y] or self.flagged[x][y]):
            return

        self.revealed[x][y] = True
        btn = self.buttons[x][y]

        if self.hints[x][y] > 0:
            btn.config(text=str(self.hints[x][y]),
                       relief=tk.SUNKEN,
                       bg='#ffffff',
                       fg=self.colors[self.hints[x][y]],
                       state=tk.DISABLED)
        elif self.hints[x][y] == 0:
            btn.config(relief=tk.SUNKEN,
                       bg='#ffffff',
                       state=tk.DISABLED)
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    self.reveal(x + dx, y + dy)

    def left_click(self, x, y):
        """处理左键点击事件"""
        if self.game_over or self.flagged[x][y]:
            return

        if not self.game_started:
            self.game_started = True
            self.place_mines(x, y)

        if self.mines[x][y]:
            self.game_over = True
            self.reveal_all()
            messagebox.showinfo("游戏结束", "踩到地雷了！")
            return

        self.reveal(x, y)
        if self.check_win():
            self.game_over = True
            self.reveal_all()
            messagebox.showinfo("恭喜", "你赢了！")

    def right_click(self, x, y):
        """处理右键点击事件"""
        if self.game_over or self.revealed[x][y]:
            return

        self.flagged[x][y] = not self.flagged[x][y]
        self.buttons[x][y].config(text='🚩' if self.flagged[x][y] else '')

        self.mines_remaining += -1 if self.flagged[x][y] else 1
        self.update_mine_count()

    def reveal_all(self):
        """显示所有格子"""
        for x in range(self.settings.width):
            for y in range(self.settings.height):
                btn = self.buttons[x][y]
                if self.mines[x][y]:
                    if self.flagged[x][y]:
                        btn.config(text='💣', bg='#90EE90', relief=tk.SUNKEN)
                    else:
                        btn.config(text='💣', bg='#FF6B6B', relief=tk.SUNKEN)
                elif self.flagged[x][y]:
                    btn.config(text='❌', bg='#FFB6C1', relief=tk.SUNKEN)
                elif not self.revealed[x][y]:
                    self.reveal(x, y)

    def check_win(self):
        """检查是否胜利"""
        return all(self.revealed[x][y] or self.mines[x][y]
                   for x in range(self.settings.width)
                   for y in range(self.settings.height))


if __name__ == '__main__':
    root = tk.Tk()
    game = Minesweeper(root)
    root.mainloop()
