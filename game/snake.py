"""Логика сетки. Здесь нет импортов Panda3D и зависимости от FPS."""
from enum import IntEnum
from random import Random
from config import GRID_SIZE, START_LENGTH

Cell = tuple[int, int]


class Direction(IntEnum):
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    @property
    def vector(self) -> Cell:
        return ((0, 1), (1, 0), (0, -1), (-1, 0))[self]


class SnakeGame:
    def __init__(self, goal=None, size=GRID_SIZE, obstacles=(), rng=None):
        if size < 6:
            raise ValueError("Поле должно быть не меньше 6×6")
        self.size = size
        self.goal = goal
        self.obstacles = frozenset(obstacles)
        self.rng = rng if rng is not None else Random()
        x, y = size // 2, max(START_LENGTH - 1, size // 2 - 1)
        self.body = [(x, y - i) for i in range(START_LENGTH)]
        self.previous = list(self.body)
        self.direction = Direction.NORTH
        self.previous_direction = self.direction
        self.pending_direction = None
        self.score = 0
        self.status = "playing"
        self.reason = ""
        self.food = self.spawn_food()

    def spawn_food(self):
        occupied = set(self.body) | self.obstacles
        free = [(x, y) for x in range(self.size) for y in range(self.size)
                if (x, y) not in occupied]
        return self.rng.choice(free) if free else None

    def request_direction(self, direction):
        """Одно принятое изменение на шаг. Обратный ход запрещён."""
        direction = Direction(direction)
        if self.status != "playing" or self.pending_direction is not None:
            return False
        if (direction - self.direction) % 4 != 1 and (direction - self.direction) % 4 != 3:
            return False
        self.pending_direction = direction
        return True

    def turn(self, side):
        if side not in (-1, 1):
            raise ValueError("Поворот: -1 влево или 1 вправо")
        return self.request_direction((self.direction + side) % 4)

    def step(self):
        """Возвращает событие: moved / ate / lost / won / idle."""
        if self.status != "playing":
            return "idle"
        self.previous = list(self.body)
        self.previous_direction = self.direction
        if self.pending_direction is not None:
            self.direction = self.pending_direction
        self.pending_direction = None
        dx, dy = self.direction.vector
        x, y = self.body[0]
        head = (x + dx, y + dy)
        grows = head == self.food
        # Хвост освобождает клетку одновременно с движением головы.
        occupied = self.body if grows else self.body[:-1]
        if not (0 <= head[0] < self.size and 0 <= head[1] < self.size):
            self.status, self.reason = "lost", "Вы встретились с краем сада"
            return "lost"
        if head in self.obstacles or head in occupied:
            self.status = "lost"
            self.reason = "На пути оказался камень" if head in self.obstacles else "Хвост оказался слишком близко"
            return "lost"
        self.body.insert(0, head)
        if not grows:
            self.body.pop()
            return "moved"
        self.score += 1
        self.food = self.spawn_food()
        if (self.goal is not None and self.score >= self.goal) or self.food is None:
            self.status = "won"
            return "won"
        return "ate"

    def interpolated(self, alpha):
        alpha = max(0.0, min(1.0, alpha))
        return [(self.previous[min(i, len(self.previous) - 1)][0] * (1 - alpha) + x * alpha,
                 self.previous[min(i, len(self.previous) - 1)][1] * (1 - alpha) + y * alpha)
                for i, (x, y) in enumerate(self.body)]
