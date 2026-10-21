"""Короткие WAV-сигналы синтезируются стандартной библиотекой Python."""
import math
import struct
import wave
from pathlib import Path
from config import ASSETS

NOTES = {"click": (620,), "eat": (660,880), "win": (523,659,784,1046),
         "lose": (392,330,220), "unlock": (784,988,1175)}


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


class Audio:
    def __init__(self,app,volume):
        self.sounds={name:app.loader.loadSfx(f"/snake-assets/sounds/{name}.wav") for name in NOTES}
        self.set_volume(volume)

    def set_volume(self,volume):
        for sound in self.sounds.values():
            sound.setVolume(volume)

    def play(self,name):
        self.sounds[name].play()
