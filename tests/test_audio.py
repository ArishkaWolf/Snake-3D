from array import array
from pathlib import Path
import wave
import pytest
from game.audio import Audio, EFFECT_NAMES, collision_sound


class Sound:
    def __init__(self):
        self.volume=1
        self.loop=False
        self.plays=0

    def setVolume(self,value):
        self.volume=value

    def setLoop(self,value):
        self.loop=value

    def play(self):
        self.plays+=1


class Loader:
    def loadSfx(self,path):
        return Sound()

    def loadMusic(self,path):
        return Sound()


def audio():
    app=type("App",(),{"loader":Loader()})()
    return Audio(app,0.6,0.25)


def test_music_and_effects_have_independent_volume():
    controller=audio()
    controller.update(8)
    music_before=controller.music.volume
    controller.set_volume(0)
    assert all(sound.volume==0 for sound in controller.sounds.values())
    assert controller.music.volume==music_before
    controller.set_volume(0.7)
    controller.set_music_volume(0)
    assert controller.music.volume==0
    assert all(sound.volume==0.7 for sound in controller.sounds.values())


def test_music_starts_once_and_fades_between_pause_and_resume():
    controller=audio()
    assert controller.music.loop and controller.music.plays==1
    assert controller.music.volume==0
    controller.update(8)
    assert controller.music.volume==pytest.approx(0.25)
    controller.update(8,paused=True)
    assert controller.music.volume==pytest.approx(0.25*0.45)
    controller.update(8)
    assert controller.music.volume==pytest.approx(0.25)
    assert controller.music.plays==1


@pytest.mark.parametrize("cause,expected",[("wall","hit_wall"),("body","hit_tail"),("obstacle","hit_wall"),(None,"lose")])
def test_collision_effect_is_chosen_by_logical_cause(cause,expected):
    assert collision_sound(cause)==expected


def test_required_effects_are_distinct_valid_wavs():
    folder=Path(__file__).resolve().parents[1]/"assets"/"sounds"
    frames=[]
    for name in EFFECT_NAMES:
        with wave.open(str(folder/f"{name}.wav"),"rb") as sound:
            assert sound.getnchannels()==1 and sound.getsampwidth()==2
            assert sound.getnframes()>1000
            if name in ("eat","hit_wall","hit_tail"):
                frames.append(sound.readframes(sound.getnframes()))
    assert len(set(frames))==3


def test_music_is_stereo_unclipped_and_has_no_large_loop_click():
    path=Path(__file__).resolve().parents[1]/"assets"/"music"/"little_journey.wav"
    with wave.open(str(path),"rb") as sound:
        assert sound.getnchannels()==2 and sound.getsampwidth()==2
        assert sound.getnframes()/sound.getframerate()==48
        samples=array("h",sound.readframes(sound.getnframes()))
    assert 5000<max(abs(value) for value in samples)<32000
    assert abs(samples[0]-samples[-2])<2500
    assert abs(samples[1]-samples[-1])<2500
