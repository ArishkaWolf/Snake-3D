"""Проверяемые JSON-сохранения с атомарной записью в профиль пользователя."""
from copy import deepcopy
from datetime import datetime
import json
import os
from pathlib import Path
import tempfile
from config import ACCESSORIES, BODY_COLORS, EYE_COLORS
from game.levels import LEVELS, BY_ID
from game.quests import QUESTS, award_quests


def default_data():
    return {"version": 1, "completed_levels": [], "unlocked_levels": ["garden", "endless"],
            "records": {}, "total_apples": 0, "max_length": 4, "quests": [],
            "unlocked": {"colors": ["green"], "eyes": ["black"], "accessories": []},
            "selected": {"color": "green", "eyes": "black", "accessories": []},
            "settings": {"volume": 0.6, "camera_distance": 6.2}}


def integer(value, fallback=0):
    return max(0, min(value, 10**9)) if type(value) is int else fallback


def strings(value, allowed):
    return list(dict.fromkeys(v for v in value if isinstance(v, str) and v in allowed)) if isinstance(value, list) else []


def sanitize(raw):
    """Чужие/устаревшие поля и неверные типы не ломают запуск."""
    data = default_data()
    if not isinstance(raw, dict):
        return data
    data["completed_levels"] = strings(raw.get("completed_levels"), [v.id for v in LEVELS])
    data["total_apples"] = integer(raw.get("total_apples"))
    data["max_length"] = max(4, integer(raw.get("max_length"), 4))
    records = raw.get("records", {})
    if isinstance(records, dict):
        data["records"] = {k: integer(v) for k, v in records.items() if k in BY_ID}
    # Награды и доступность вычисляем заново из достижений, а не доверяем спискам JSON.
    refresh_unlocks(data)
    selected = raw.get("selected", {})
    if isinstance(selected, dict):
        for field, category, allowed in (("color", "colors", BODY_COLORS), ("eyes", "eyes", EYE_COLORS)):
            value = selected.get(field)
            if isinstance(value, str) and value in allowed and value in data["unlocked"][category]:
                data["selected"][field] = value
        data["selected"]["accessories"] = strings(selected.get("accessories"), data["unlocked"]["accessories"])
    settings = raw.get("settings", {})
    if isinstance(settings, dict):
        for key, low, high in (("volume", 0, 1), ("camera_distance", 4.5, 8)):
            value = settings.get(key)
            if type(value) in (int, float) and low <= value <= high:
                data["settings"][key] = float(value)
    return data


def refresh_unlocks(data):
    unlocked = ["garden", "endless"]
    for index, level in enumerate(LEVELS[:-1]):
        if level.id in data["completed_levels"]:
            unlocked.append(LEVELS[index + 1].id)
    data["unlocked_levels"] = unlocked
    new = award_quests(data)
    data["quests"].sort(key=[q.id for q in QUESTS].index)
    for category, order in (("colors", BODY_COLORS), ("eyes", EYE_COLORS), ("accessories", ACCESSORIES)):
        data["unlocked"][category].sort(key=list(order).index)
    return new


class SaveManager:
    def __init__(self, path=None):
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / ".local" / "share"))
        self.path = Path(path) if path else base / "Snake3D" / "save.json"
        self.warning = ""
        self.data = default_data()
        self.load()

    def load(self):
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                raise ValueError("Корень JSON должен быть объектом")
            self.data = sanitize(raw)
        except FileNotFoundError:
            self.save()
        except (ValueError, UnicodeError):
            self.warning = "Повреждённое сохранение: создан новый профиль. Копия сохранена рядом."
            try:
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
                self.path.replace(self.path.with_name(f"save.corrupt-{stamp}.json"))
                self.save()
            except OSError:
                self.warning = "Не удалось восстановить сохранение. Проверьте права доступа к папке профиля."
        except OSError:
            self.warning = "Не удалось прочитать сохранение. Прогресс пока хранится в памяти."

    def save(self):
        temporary = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=self.path.parent,
                                             prefix="save-", suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(self.data, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            return True
        except (OSError, ValueError):
            self.warning = "Не удалось записать прогресс. Проверьте свободное место и права доступа."
            return False
        finally:
            if temporary is not None and temporary.exists():
                try:
                    temporary.unlink()
                except OSError:
                    pass

    def record_apple(self, length):
        self.data["total_apples"] += 1
        self.data["max_length"] = max(length, self.data["max_length"])
        new = refresh_unlocks(self.data)
        self.save()
        return new

    def finish(self, level_id, score, won):
        self.data["records"][level_id] = max(score, self.data["records"].get(level_id, 0))
        if won and level_id != "endless" and level_id not in self.data["completed_levels"]:
            self.data["completed_levels"].append(level_id)
        new = refresh_unlocks(self.data)
        self.save()
        return new

    def select(self, category, item):
        key = {"colors": "color", "eyes": "eyes", "accessories": "accessories"}[category]
        if item not in self.data["unlocked"][category]:
            return False
        if category == "accessories":
            selected = self.data["selected"][key]
            if item in selected:
                selected.remove(item)
            else:
                # Кепка и корона занимают одно место; очки сочетаются с обеими.
                if item in ("cap", "crown"):
                    selected[:] = [i for i in selected if i not in ("cap", "crown")]
                selected.append(item)
        else:
            self.data["selected"][key] = item
        self.save()
        return True

    def reset(self):
        previous = deepcopy(self.data)
        self.data = default_data()
        if not self.save():
            self.data = previous
            return False
        return True
