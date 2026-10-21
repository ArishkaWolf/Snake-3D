"""Идемпотентная выдача наград за реальные сохранённые события."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Quest:
    id: str
    title: str
    description: str
    reward: str
    category: str
    item: str


QUESTS = (
    Quest("apples20", "Яблочный коллекционер", "Соберите 20 яблок за всё время", "Голубой цвет и голубые глаза", "colors", "blue"),
    Quest("length15", "Большая прогулка", "Достигните длины 15 сегментов", "Жёлтый цвет и зелёные глаза", "colors", "yellow"),
    Quest("garden", "Первый листочек", "Пройдите Зелёный сад", "Розовый цвет", "colors", "pink"),
    Quest("sand", "Солнечный день", "Пройдите Песчаную долину", "Круглые очки и лавандовый цвет", "accessories", "glasses"),
    Quest("lavender", "Выше облаков", "Пройдите Лавандовый мир", "Кепка и корона", "accessories", "cap"),
)


def award_quests(data):
    conditions = {
        "apples20": data["total_apples"] >= 20,
        "length15": data["max_length"] >= 15,
        **{key: key in data["completed_levels"] for key in ("garden", "sand", "lavender")},
    }
    awarded = []
    for quest in QUESTS:
        if conditions[quest.id] and quest.id not in data["quests"]:
            data["quests"].append(quest.id)
            unlock = data["unlocked"][quest.category]
            if quest.item not in unlock:
                unlock.append(quest.item)
            extra = {"apples20": ("eyes", "blue"), "length15": ("eyes", "green"),
                     "sand": ("colors", "lavender"), "lavender": ("accessories", "crown")}.get(quest.id)
            if extra and extra[1] not in data["unlocked"][extra[0]]:
                data["unlocked"][extra[0]].append(extra[1])
            awarded.append(quest)
    return awarded
