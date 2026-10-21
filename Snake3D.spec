# PyInstaller onedir: ресурсы и нативные плагины Panda3D лежат рядом с exe.
from PyInstaller.utils.hooks import collect_all

panda_data, panda_binaries, panda_hidden = collect_all("panda3d")
a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=panda_binaries,
    datas=panda_data + [("assets", "assets")],
    hiddenimports=panda_hidden,
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest", "tkinter", "unittest", "pdb"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="Snake3D",
          debug=False, bootloader_ignore_signals=False, strip=False,
          upx=False, console=False)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name="Snake3D")

# Читаемые инструкции и лицензии в корне готовой папки.
from pathlib import Path
from importlib.metadata import distribution
import shutil
output = Path(DISTPATH) / "Snake3D"
for name in ("README.md", "LICENSE", "THIRD_PARTY.md"):
    shutil.copy2(name, output / name)
shutil.copytree("docs", output / "docs", dirs_exist_ok=True)
shutil.copy2("assets/fonts/OFL.txt", output / "NotoSans-OFL.txt")
panda_license = distribution("panda3d").locate_file("panda3d-1.10.16.dist-info/LICENSE.txt")
shutil.copy2(panda_license, output / "Panda3D-LICENSE.txt")
