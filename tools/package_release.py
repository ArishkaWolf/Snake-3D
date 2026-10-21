"""ZIP для игрока и отдельный набор itch.io; только стандартная библиотека."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from config import VERSION
from game.audio import EFFECT_NAMES


def sha256(path):
    digest=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()


def git(*args):
    return subprocess.check_output(["git","-c",f"safe.directory={ROOT.as_posix()}",*args],cwd=ROOT,text=True).strip()


def archive_tree(folder,destination,prefix,extra=None):
    files=sorted(path for path in folder.rglob("*") if path.is_file())
    destination.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(destination,"w",zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
        for path in files:
            if path.is_symlink():
                raise ValueError(f"Symlink not allowed in release: {path}")
            archive.write(path,f"{prefix}/{path.relative_to(folder).as_posix()}")
        for name,content in (extra or {}).items():
            archive.writestr(f"{prefix}/{name}",content)
    with zipfile.ZipFile(destination) as archive:
        bad=archive.testzip()
        if bad:
            raise ValueError(f"ZIP CRC error: {bad}")
    checksum=destination.with_suffix(destination.suffix+".sha256")
    checksum.write_text(f"{sha256(destination)}  {destination.name}\n",encoding="ascii")
    return destination


def package(build_dir=ROOT/"dist"/"Snake3D",output_dir=ROOT/"dist"):
    build_dir=Path(build_dir)
    required=["Snake3D.exe","README.txt","LICENSE","NotoSans-OFL.txt","Panda3D-LICENSE.txt",
              "_internal/assets/fonts/NotoSans-Regular.ttf",
              "_internal/assets/music/little_journey.wav",
              *[f"_internal/assets/sounds/{name}.wav" for name in EFFECT_NAMES]]
    # Python 3.11/3.12 тоже поддерживаются: имя DLL зависит от сборочного Python.
    if not list((build_dir/"_internal").glob("python3*.dll")):
        raise FileNotFoundError("Bundled Python runtime is missing")
    for name in required:
        if not (build_dir/name).is_file():
            raise FileNotFoundError(f"Required release file is missing: {name}")
    info={"version":VERSION,"platform":"Windows x64","packager":"PyInstaller onedir",
          "source_commit":git("rev-parse","HEAD"),"source_dirty":bool(git("status","--porcelain")),
          "built_at_utc":datetime.now(timezone.utc).isoformat(),"external_python_required":False}
    files=sorted(path for path in build_dir.rglob("*") if path.is_file())
    manifest="".join(f"{sha256(path)}  {path.relative_to(build_dir).as_posix()}\n" for path in files)
    game=archive_tree(build_dir,Path(output_dir)/f"Snake-3D-v{VERSION}-Windows.zip",f"Snake-3D-v{VERSION}-Windows",
                      {"BUILD_INFO.json":json.dumps(info,ensure_ascii=False,indent=2),"MANIFEST.sha256":manifest})
    kit=archive_tree(ROOT/"publishing"/"itchio",Path(output_dir)/f"Snake-3D-v{VERSION}-itchio-kit.zip","Snake-3D-itchio-kit")
    for path in (game,kit):
        print(f"{path.name}: {path.stat().st_size:,} bytes; SHA256 {sha256(path)}")
    return game,kit


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--build-dir",type=Path,default=ROOT/"dist"/"Snake3D")
    parser.add_argument("--output-dir",type=Path,default=ROOT/"dist")
    args=parser.parse_args()
    package(args.build_dir,args.output_dir)
