"""Описание уровней: один алгоритм, разные цели, темп и декорации."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Level:
    id: str
    name: str
    subtitle: str
    goal: int | None
    speed: float
    floor: tuple
    sky: tuple
    theme: str
    reward: str
    obstacles: frozenset = frozenset()


LEVELS = (
    Level("garden", "Зелёный сад", "Тёплый ветер и первые открытия", 5, 3.4,
          (0.66, 0.80, 0.59, 1), (0.79, 0.88, 0.85, 1), "garden", "Розовый цвет"),
    Level("sand", "Песчаная долина", "Прогулка среди кактусов", 10, 3.9,
          (0.88, 0.76, 0.54, 1), (0.94, 0.86, 0.74, 1), "sand", "Круглые очки",
          frozenset({(4, 5), (5, 5), (14, 14), (15, 14)})),
    Level("lavender", "Лавандовый мир", "Чуть быстрее, чуть ближе к облакам", 15, 4.5,
          (0.72, 0.65, 0.83, 1), (0.86, 0.83, 0.94, 1), "lavender", "Кепка"),
)
ENDLESS = Level("endless", "Без спешки", "Бесконечный сад · новый личный рекорд", None, 3.6,
                LEVELS[0].floor, LEVELS[0].sky, "garden", "Личный рекорд")
BY_ID = {level.id: level for level in (*LEVELS, ENDLESS)}
