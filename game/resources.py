"""Загрузка через память обходит узкие Windows-пути в нативных загрузчиках."""
from pathlib import Path
from panda3d.core import VirtualFileSystem, VirtualFileMountRamdisk, PNMImage, StringStream
from config import ASSETS


def mount_assets():
    vfs=VirtualFileSystem.getGlobalPtr()
    mount=VirtualFileMountRamdisk()
    vfs.mount(mount,"/snake-assets",0)
    for folder in ("fonts","sounds"):
        vfs.makeDirectoryFull(f"/snake-assets/{folder}")
        for path in (ASSETS/folder).iterdir():
            if path.suffix.lower() in (".ttf",".wav"):
                vfs.writeFile(f"/snake-assets/{folder}/{path.name}",path.read_bytes(),False)
    return mount


def screenshot(window,path):
    """Сохраняет PNG, в том числе в каталог с кириллицей."""
    image=PNMImage()
    if not window.getScreenshot(image):
        raise RuntimeError("Не удалось получить кадр из графического буфера")
    stream=StringStream()
    if not image.write(stream,"frame.png"):
        raise RuntimeError("Не удалось закодировать PNG")
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_bytes(stream.getData())
