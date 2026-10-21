"""Проверка ZIP после распаковки, без Python/исходников в окружении EXE.

Это проверка изоляции приложения в текущей Windows, а не чистая виртуальная машина.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import wave
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from game.audio import EFFECT_NAMES


def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()


def verify(path):
    path=Path(path).resolve()
    workspace=Path(__file__).resolve().parents[1]
    output=workspace/"artifacts"/"release-verification"
    output.mkdir(parents=True,exist_ok=True)
    test_dir=Path(tempfile.mkdtemp(prefix="Распаковка Snake 3D ",dir=output))
    with zipfile.ZipFile(path) as archive:
        if archive.testzip():
            raise RuntimeError("ZIP CRC check failed")
        for name in archive.namelist():
            destination=(test_dir/name).resolve()
            if not destination.is_relative_to(test_dir.resolve()):
                raise ValueError("Unsafe ZIP path")
        archive.extractall(test_dir)
    roots=[p for p in test_dir.iterdir() if p.is_dir()]
    if len(roots)!=1:
        raise RuntimeError("ZIP must have one top-level application folder")
    app_dir=roots[0]
    for line in (app_dir/"MANIFEST.sha256").read_text(encoding="utf-8").splitlines():
        expected,name=line.split("  ",1)
        if sha256(app_dir/name)!=expected:
            raise RuntimeError(f"Manifest mismatch: {name}")
    info=json.loads((app_dir/"BUILD_INFO.json").read_text(encoding="utf-8"))
    sound_files=app_dir/"_internal"/"assets"/"sounds"
    for name in EFFECT_NAMES:
        with wave.open(str(sound_files/f"{name}.wav"),"rb") as sound:
            assert sound.getnframes()>0 and sound.getnchannels()==1
    with wave.open(str(app_dir/"_internal/assets/music/little_journey.wav"),"rb") as music:
        assert music.getnchannels()==2 and music.getnframes()/music.getframerate()==48
    runtime=app_dir/"_internal"
    assert list(runtime.glob("python3*.dll"))
    assert (runtime/"assets"/"fonts"/"NotoSans-Regular.ttf").stat().st_size>100000
    assert list((runtime/"panda3d").glob("libpandagl*.dll"))

    # Ни исходников проекта, ни виртуального окружения, ни Python в PATH дочернего EXE.
    env={key:value for key,value in os.environ.items() if key.upper() not in ("PYTHONHOME","PYTHONPATH","VIRTUAL_ENV")}
    windows=Path(env.get("SystemRoot",r"C:\Windows"))
    env["PATH"]=str(windows/"System32")+os.pathsep+str(windows)
    env["LOCALAPPDATA"]=str(test_dir/"User profile")
    env["TEMP"]=env["TMP"]=str(test_dir/"Temp")
    Path(env["TEMP"]).mkdir()
    exe=app_dir/"Snake3D.exe"
    def launch(*args):
        result=subprocess.run([str(exe),*args],cwd=app_dir,env=env,timeout=60,
                              stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        if result.returncode:
            raise RuntimeError(f"EXE failed ({result.returncode}): {result.stderr.decode(errors='replace')[:1000]}")

    launch("--smoke-frames","12","--screenshot","artifacts/startup.png")
    save=Path(env["LOCALAPPDATA"])/"Snake3D"/"save.json"
    data=json.loads(save.read_text(encoding="utf-8"))
    assert data["version"]==1
    # Отдельный тестовый профиль имитирует существующее корректное сохранение.
    data.update(total_apples=5,completed_levels=["garden"],records={"garden":5})
    data["selected"]["color"]="pink"
    data["settings"]["volume"]=0.35
    data["settings"]["music_volume"]=0.17
    save.write_text(json.dumps(data,ensure_ascii=False),encoding="utf-8")
    launch("--smoke-frames","12","--screenshot","artifacts/restored-profile.png")
    restored=json.loads(save.read_text(encoding="utf-8"))
    assert restored["total_apples"]==5 and restored["selected"]["color"]=="pink"
    assert restored["settings"]["volume"]==0.35 and "sand" in restored["unlocked_levels"]
    assert restored["settings"]["music_volume"]==0.17
    launch("--self-test")
    smoke=json.loads((app_dir/"artifacts"/"smoke-report.json").read_text(encoding="utf-8"))
    assert smoke["passed"] and smoke["frozen"] and smoke["font_valid"] and smoke["windowed"]
    assert all(length>0 for length in smoke["sound_lengths_seconds"].values())
    assert smoke["music_length_seconds"]==48 and smoke["music_loop"]
    assert smoke["collision_sounds_tested"]==["hit_wall","hit_tail"]
    assert Path(smoke["resource_root"]).resolve().is_relative_to(app_dir.resolve())
    report={"passed":True,"archive":path.name,"archive_sha256":sha256(path),
            "archive_bytes":path.stat().st_size,"version":info["version"],"source_commit":info["source_commit"],
            "source_dirty":info["source_dirty"],"packager":info["packager"],
            "zip_crc_and_manifest":"passed","python_in_path":False,"clean_windows_vm_tested":False,
            "extracted_to":str(app_dir),"default_save_and_reload":"passed", "windowed_smoke":smoke}
    destination=path.with_suffix(".verification.json")
    destination.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"PASS: extracted ZIP, isolated PATH, fonts, {len(EFFECT_NAMES)} effects, looping music, saves, {len(smoke['checks'])} checks")
    print(destination)
    return report


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("archive",type=Path)
    verify(parser.parse_args().archive)
