"""Оригинальная спокойная инструментальная петля, без семплов и зависимостей.

80 BPM, Dadd9 → Aadd9 → Bm7 → Gmaj7. Мягкие щипковые струны,
стереозадержка, медленные пэды, бас и тихая перкуссия — настроение пост-рока.
Это подготовка ресурса; во время игры синтез не выполняется.
"""
from array import array
from math import exp, pi, sin, sqrt
from pathlib import Path
from random import Random
import struct
import sys
import wave

RATE=22050
BPM=80
BEAT=60/BPM
DURATION=16*4*BEAT


def frequency(midi):
    return 440*2**((midi-69)/12)


def pluck(midi,duration=3.1):
    """Затухающая струна: шумовой импульс и усредняющая обратная связь."""
    rng=Random(500+midi)
    period=round(RATE/frequency(midi)-0.5)
    ring=[rng.uniform(-1,1) for _ in range(period)]
    average=sum(ring)/period
    ring=[value-average for value in ring]
    for _ in range(3):
        ring=[(ring[i]+ring[(i+1)%period])*0.5 for i in range(period)]
    peak=max(abs(value) for value in ring)
    ring=[value/peak for value in ring]
    signal=array("f")
    for i in range(int(duration*RATE)):
        index=i%period
        value=ring[index]
        ring[index]=(value+ring[(index+1)%period])*0.4996
        t=i/RATE
        envelope=min(1,t/0.008)*min(1,(duration-t)/0.18)*exp(-t/2.8)
        signal.append(value*envelope)
    return signal


def pad(midi,duration=8):
    result=array("f")
    f=frequency(midi)
    for i in range(int(duration*RATE)):
        t=i/RATE
        envelope=sin(pi*t/duration)**2
        # Незначительная расстройка и медленное движение вместо резкого тембра.
        value=(sin(2*pi*f*t)+0.38*sin(2*pi*f*1.0017*t)+0.14*sin(4*pi*f*t))
        result.append(value*envelope/1.52)
    return result


def bass(midi):
    f=frequency(midi)
    result=array("f")
    for i in range(int(1.35*RATE)):
        t=i/RATE
        envelope=min(1,t/0.035)*exp(-t*2.6)*min(1,(1.35-t)/0.12)
        result.append((sin(2*pi*f*t)+0.32*sin(4*pi*f*t))*envelope)
    return result


def percussion(kind):
    rng=Random(37)
    duration=0.32 if kind=="kick" else 0.16
    result=array("f")
    low=0.0
    for i in range(int(duration*RATE)):
        t=i/RATE
        noise=rng.uniform(-1,1)
        low=0.7*low+0.3*noise
        if kind=="kick":
            value=sin(2*pi*(52*t+48*(1-exp(-t*35))/35))*exp(-t*18)
        elif kind=="brush":
            value=low*exp(-t*28)
        else:
            value=(noise-low)*exp(-t*70)
        result.append(value*min(1,t/0.003)*min(1,(duration-t)/0.02))
    return result


def compose(destination):
    count=int(DURATION*RATE)
    left=array("f",[0])*count
    right=array("f",[0])*count
    guitar_l=array("f",[0])*count
    guitar_r=array("f",[0])*count
    def mix(signal,start,gain,pan=0,dest=None):
        l,r=dest if dest else (left,right)
        offset=round(start*RATE)%count
        lg=gain*sqrt((1-pan)/2)
        rg=gain*sqrt((1+pan)/2)
        for i,value in enumerate(signal):
            index=(offset+i)%count
            l[index]+=value*lg
            r[index]+=value*rg

    chords=[(38,[50,57,62,64,66,64,62,57],[50,57,62,66]),
            (33,[45,52,57,59,61,59,57,52],[45,52,59,61]),
            (35,[47,54,57,62,66,62,57,54],[47,54,57,62]),
            (31,[43,50,54,57,62,57,54,50],[43,50,54,59])]
    cache={midi:pluck(midi) for midi in {n for _,notes,_ in chords for n in notes}|{59,61,62,64,66}}
    kick,brush,hat=(percussion(kind) for kind in ("kick","brush","hat"))
    motifs=[(66,64),(62,64),(64,61),(59,61),(62,66),(64,62),(59,62),(57,59)]
    rng=Random(2026)
    for bar in range(16):
        root,notes,voicing=chords[(bar//2)%4]
        start=bar*4*BEAT
        for step,note in enumerate(notes):
            mix(cache[note],start+step*BEAT/2+rng.uniform(-0.008,0.008),
                0.14*(0.85 if step%2 else 1),-0.35 if step%2 else 0.35,(guitar_l,guitar_r))
        for beat in (0,2):
            mix(bass(root),start+beat*BEAT,0.085)
        if bar%2==0:
            for i,note in enumerate(voicing):
                mix(pad(note),start,0.025,(-0.55,-0.2,0.2,0.55)[i])
        mix(kick,start,0.045)
        for beat in (1,3):
            mix(brush,start+beat*BEAT,0.025,0.2)
        for beat in range(4):
            mix(hat,start+(beat+0.5)*BEAT,0.009,-0.45)
        if bar>=8:
            for i,note in enumerate(motifs[bar-8]):
                mix(cache[note],start+(0.5+2*i)*BEAT,0.105,0.15,(guitar_l,guitar_r))

    # Хвосты и задержки переходят через конец в начало: петля не обрывается.
    taps=[(0,1),(0.75*BEAT,0.32),(1.5*BEAT,0.19),(2.25*BEAT,0.11),(3.5*BEAT,0.06)]
    for delay,gain in taps:
        shift=round(delay*RATE)
        for i in range(count):
            index=(i+shift)%count
            a,b=(guitar_r[i],guitar_l[i]) if shift else (guitar_l[i],guitar_r[i])
            left[index]+=a*gain
            right[index]+=b*gain
    mean_l,mean_r=sum(left)/count,sum(right)/count
    peak=max(max(abs(value-mean_l) for value in left),max(abs(value-mean_r) for value in right))
    gain=0.82/max(peak,0.001)
    pcm=bytearray(count*4)
    for i,(l,r) in enumerate(zip(left,right)):
        struct.pack_into("<hh",pcm,i*4,round((l-mean_l)*gain*32767),round((r-mean_r)*gain*32767))
    destination=Path(destination)
    destination.parent.mkdir(parents=True,exist_ok=True)
    with wave.open(str(destination),"wb") as stream:
        stream.setparams((2,2,RATE,0,"NONE","not compressed"))
        stream.writeframes(pcm)
    print(f"Music: {destination}, {DURATION:g}s, stereo, {BPM} BPM")


if __name__=="__main__":
    target=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/"assets/music/little_journey.wav"
    compose(target)
