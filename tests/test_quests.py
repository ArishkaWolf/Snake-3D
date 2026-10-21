from copy import deepcopy
import pytest
from game.quests import QUESTS, quest_progress
from game.save_manager import default_data


def test_partial_progress_matches_saved_statistics():
    data=default_data()
    data.update(total_apples=14,max_length=12)
    assert quest_progress("apples20",data)==(14,20)
    assert quest_progress("length15",data)==(12,15)


def test_level_progress_uses_best_run_without_awarding_completion():
    data=default_data()
    data["records"]={"garden":3,"sand":6,"lavender":11}
    before=deepcopy(data)
    assert quest_progress("garden",data)==(3,5)
    assert quest_progress("sand",data)==(6,10)
    assert quest_progress("lavender",data)==(11,15)
    assert data==before


@pytest.mark.parametrize("quest_id",["garden","sand","lavender"])
def test_completed_world_is_full_without_a_record(quest_id):
    data=default_data()
    data["completed_levels"]=[quest_id]
    current,target=quest_progress(quest_id,data)
    assert current==target


@pytest.mark.parametrize("quest",QUESTS,ids=lambda q:q.id)
def test_earned_achievement_always_has_a_full_bar(quest):
    data=default_data()
    data["quests"]=[quest.id]
    current,target=quest_progress(quest.id,data)
    assert current==target


@pytest.mark.parametrize("value",[-10,0,1000])
def test_progress_stays_within_bar_bounds(value):
    data=default_data()
    data.update(total_apples=value,max_length=value)
    data["records"]={"garden":value,"sand":value,"lavender":value}
    for quest in QUESTS:
        current,target=quest_progress(quest.id,data)
        assert 0<=current<=target


def test_missing_level_record_starts_empty():
    data=default_data()
    assert quest_progress("garden",data)==(0,5)
    assert quest_progress("sand",data)==(0,10)
    assert quest_progress("lavender",data)==(0,15)
