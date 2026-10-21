"""Небольшой набор настроек игры; расстояния измеряются в клетках."""
from pathlib import Path
import sys

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
ASSETS = ROOT / "assets"
GRID_SIZE = 20
START_LENGTH = 4
CAMERA_DISTANCE = 6.2
CAMERA_HEIGHT = 5.0
CAMERA_LOOK_AHEAD = 1.2
CAMERA_SMOOTHING = 7.0
WINDOW_SIZE = (1280, 800)
TITLE = "Snake 3D · Маленькое путешествие"
VERSION = "1.0"

BODY_COLORS = {
    "green": ("Зелёный", (0.39, 0.70, 0.39, 1)),
    "pink": ("Розовый", (0.91, 0.48, 0.63, 1)),
    "blue": ("Голубой", (0.36, 0.69, 0.85, 1)),
    "lavender": ("Лавандовый", (0.65, 0.53, 0.83, 1)),
    "yellow": ("Жёлтый", (0.93, 0.75, 0.32, 1)),
}
EYE_COLORS = {
    "black": ("Чёрные", (0.08, 0.12, 0.13, 1)),
    "blue": ("Голубые", (0.15, 0.42, 0.78, 1)),
    "green": ("Зелёные", (0.13, 0.46, 0.29, 1)),
}
ACCESSORIES = {"glasses": "Круглые очки", "cap": "Кепка", "crown": "Корона"}
