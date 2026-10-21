import json
import math
import pytest
from game.save_manager import SaveManager, sanitize
from game.quests import award_quests


def test_first_run_and_roundtrip(tmp_path):
    path=tmp_path/"profile"/"save.json"
    save=SaveManager(path)
    assert path.exists()
    save.record_apple(5)
    save.finish("garden",5,True)
    assert save.select("colors","pink")
    loaded=SaveManager(path)
    assert loaded.data==save.data
    assert loaded.data["total_apples"]==1
    assert loaded.data["selected"]["color"]=="pink"
    assert loaded.data["records"]["garden"]==5


@pytest.mark.parametrize("bad",["{broken", "[]", "null", "\ufeffnot-json"])
def test_corrupt_file_backed_up(tmp_path,bad):
    path=tmp_path/"save.json"
    path.write_text(bad,encoding="utf-8")
    save=SaveManager(path)
    assert save.warning
    assert list(tmp_path.glob("save.corrupt-*.json"))
    assert json.loads(path.read_text(encoding="utf-8"))["version"]==1


def test_wrong_schema_is_sanitized():
    data=sanitize({"completed_levels":42,"total_apples":-8,"max_length":"bad", "records":[],
                   "selected":{"color":[],"eyes":{},"accessories":[{},"bad"]},
                   "settings":{"volume":math.nan,"camera_distance":math.inf},"unlocked":None})
    assert data["total_apples"]==0
    assert data["max_length"]==4
    assert data["selected"]["color"]=="green"
    assert data["settings"]["volume"]==0.6


def test_rewards_only_once(tmp_path):
    save=SaveManager(tmp_path/"save.json")
    first=save.finish("garden",5,True)
    second=save.finish("garden",5,True)
    assert [q.id for q in first]==["garden"]
    assert second==[]
    assert save.data["unlocked"]["colors"].count("pink")==1
    assert "sand" in save.data["unlocked_levels"]
    assert "lavender" not in save.data["unlocked_levels"]


def test_all_progress_unlocks_and_selection(tmp_path):
    save=SaveManager(tmp_path/"save.json")
    assert not save.select("accessories","cap")
    assert not save.select("colors","pink")
    for index in range(20):
        save.record_apple(4+index)
    for key,score in (("garden",5),("sand",10),("lavender",15)):
        save.finish(key,score,True)
    assert len(save.data["quests"])==5
    assert set(save.data["unlocked"]["colors"])=={"green","pink","blue","lavender","yellow"}
    assert save.select("accessories","cap")
    assert save.select("accessories","glasses")
    assert save.select("accessories","crown")
    assert set(save.data["selected"]["accessories"])=={"crown","glasses"}
    save.select("accessories","glasses")
    assert save.data["selected"]["accessories"]==["crown"]
    assert SaveManager(save.path).data==save.data


def test_record_not_reduced_and_loss_not_completion(tmp_path):
    save=SaveManager(tmp_path/"save.json")
    save.finish("garden",4,False)
    save.finish("garden",1,False)
    assert save.data["records"]["garden"]==4
    assert save.data["completed_levels"]==[]


def test_reset(tmp_path):
    save=SaveManager(tmp_path/"save.json")
    save.finish("garden",5,True)
    assert save.reset()
    assert SaveManager(save.path).data["completed_levels"]==[]
    assert save.data["selected"]["color"]=="green"


def test_io_error_is_reported_without_crash(tmp_path):
    blocker=tmp_path/"file"
    blocker.write_text("occupied",encoding="utf-8")
    save=SaveManager(blocker/"save.json")
    assert not save.save()
    assert save.warning


def test_failed_atomic_replace_retains_old_file(tmp_path,monkeypatch):
    import game.save_manager as module
    save=SaveManager(tmp_path/"save.json")
    original=save.path.read_bytes()
    save.data["total_apples"]=4
    def fail(*args):
        raise OSError("Disk full")
    monkeypatch.setattr(module.os,"replace",fail)
    assert not save.save()
    assert save.path.read_bytes()==original
    assert not list(tmp_path.glob("*.tmp"))


def test_restore_missing_reward_lists_from_statistics():
    data=sanitize({"total_apples":20,"max_length":15,"completed_levels":["garden","sand","lavender"]})
    assert len(data["quests"])==5
    assert award_quests(data)==[]
