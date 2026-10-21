"""Короткие эффекты и фоновая музыка на отдельных каналах Panda3D."""
import math
import struct
import wave
from pathlib import Path
from random import Random

NOTES = {"click": (620,), "eat": (660,880), "win": (523,659,784,1046),
         "lose": (392,330,220), "unlock": (784,988,1175)}
EFFECT_NAMES=(*NOTES,"hit_wall","hit_tail")


def collision_sound(collision):
    return {"wall":"hit_wall","obstacle":"hit_wall","body":"hit_tail"}.get(collision,"lose")


def generate_sounds(folder):
    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    for name,notes in NOTES.items():
        data=[]
        duration=0.085 if name=="click" else 0.12
        rate=22050
        for frequency in notes:
            for i in range(int(duration*rate)):
                t=i/rate
                envelope=min(1,t/0.008)*max(0,1-t/duration)**2
                sample=(math.sin(2*math.pi*frequency*t)+0.20*math.sin(4*math.pi*frequency*t))*envelope
                data.append(struct.pack("<h",int(sample*9000)))
        with wave.open(str(folder/f"{name}.wav"),"wb") as stream:
            stream.setnchannels(1)
            stream.setsampwidth(2)
            stream.setframerate(rate)
            stream.writeframes(b"".join(data))
    # Стена — короткий низкий стук; тело — более мягкий пружинящий звук.
    for name in ("hit_wall","hit_tail"):
        rate=22050
        duration=0.24 if name=="hit_wall" else 0.34
        rng=Random(19)
        phase=0.0
        low=0.0
        data=bytearray()
        for i in range(int(duration*rate)):
            t=i/rate
            low=0.65*low+0.35*rng.uniform(-1,1)
            if name=="hit_wall":
                pitch=65+125*math.exp(-t*35)
                value=0.85*math.sin(phase)+0.55*low*math.exp(-t*28)
            else:
                pitch=135+125*math.exp(-t*22)+30*math.sin(t*20)
                value=0.75*math.sin(phase)+0.20*math.sin(phase*2)
            phase+=2*math.pi*pitch/rate
            envelope=min(1,t/0.004)*math.exp(-t*13)*min(1,(duration-t)/0.03)
            data.extend(struct.pack("<h",int(value*envelope*15000)))
        with wave.open(str(folder/f"{name}.wav"),"wb") as stream:
            stream.setparams((1,2,rate,0,"NONE","not compressed"))
            stream.writeframes(data)


class Audio:
    def __init__(self,app,volume,music_volume=0.25):
        self.sounds={name:app.loader.loadSfx(f"/snake-assets/sounds/{name}.wav") for name in EFFECT_NAMES}
        self.set_volume(volume)
        self.music=app.loader.loadMusic("/snake-assets/music/little_journey.wav")
        self.music.setLoop(True)
        self.music_gain=0.0
        self.set_music_volume(music_volume)
        self.music.play()

    def set_volume(self,volume):
        for sound in self.sounds.values():
            sound.setVolume(volume)

    def play(self,name):
        self.sounds[name].play()

    def set_music_volume(self,volume):
        self.music_volume=max(0,min(1,volume))
        self.music.setVolume(self.music_volume*self.music_gain)

    def update(self,dt,paused=False):
        # Плавное начало и небольшое приглушение в паузе; трек не запускается заново.
        target=0.45 if paused else 1.0
        self.music_gain+=(target-self.music_gain)*(1-math.exp(-2.5*max(0,dt)))
        self.music.setVolume(self.music_volume*self.music_gain)
