"""Интеграционная проверка реального Panda3D и PNG всех основных экранов.

Запуск из корня: python tools/smoke_test.py [--windowed]
Использует отдельный временный профиль, не изменяет прогресс игрока.
"""
import argparse
import json
from pathlib import Path
import random
import sys
import tempfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from panda3d.core import ClockObject, WindowProperties
from game.app import SnakeApp
from game.levels import LEVELS, ENDLESS
from game.snake import Direction
from game.resources import screenshot
from game.save_manager import SaveManager
from tools.autoplay import choose_direction
from config import ASSETS


def run(windowed=False):
    output=Path("artifacts")
    output.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="snake-smoke-") as temp:
        app=SnakeApp(offscreen=not windowed,save_path=Path(temp)/"save.json",audio=windowed)
        clock=ClockObject.getGlobalClock()
        clock.setMode(ClockObject.MNonRealTime)
        clock.setDt(1/60)
        checks=[]
        def frame(name):
            for _ in range(3):
                app.taskMgr.step()
            screenshot(app.win,output/f"{name}.png")
            checks.append(name)
        try:
            frame("01-main")
            app.show_levels()
            frame("02-levels-locked")
            assert not app.start_game(LEVELS[1])
            app.show_customization()
            frame("03-customization-locked")
            app.show_quests()
            frame("04-quests")
            app.show_settings("menu")
            frame("05-settings")
            from direct.gui.DirectGui import DirectSlider
            sliders=[widget for widget in app.ui.widgets if isinstance(widget,DirectSlider)]
            sliders[0]["value"]=0.25
            sliders[1]["value"]=6.2
            sliders[0].commandFunc()
            sliders[1].commandFunc()
            assert app.save.data["settings"]["volume"]==0.25
            app.confirm_reset("menu")
            frame("06-reset-confirmation")
            app.show_settings("menu")
            app.close_settings("menu")

            app.start_game(LEVELS[0])
            app.messenger.send("a")
            assert app.game.pending_direction==Direction.WEST
            app.messenger.send("d")
            assert app.game.pending_direction==Direction.WEST
            app.messenger.send("escape")
            assert app.state=="paused"
            app.messenger.send("escape")
            assert app.state=="playing"

            # Ровно одна секунда при разных FPS должна дать одинаковую сетку.
            fps_bodies=[]
            for fps in (30,144):
                app.start_game(LEVELS[0])
                app.countdown=0
                app.game.food=(0,0)
                clock.setDt(1/fps)
                for _ in range(fps):
                    app.taskMgr.step()
                fps_bodies.append(list(app.game.body))
            assert fps_bodies[0]==fps_bodies[1]
            clock.setDt(1/60)
            checks.append("fps-30-equals-144")

            for index,level in enumerate(LEVELS):
                assert app.start_game(level)
                app.countdown=100000
                app.game.rng=random.Random(4+index)
                app.game.food=app.game.spawn_food()
                frame(f"07-{level.id}-start")
                app.pause()
                frozen=list(app.game.body)
                for _ in range(90):
                    app.taskMgr.step()
                assert app.game.body==frozen
                frame(f"08-{level.id}-pause")
                app.show_settings("paused")
                app.close_settings("paused")
                assert app.state=="paused"
                app.resume()
                old_head=app.game.body[0]
                assert app.game.turn(1)
                assert not app.game.turn(1)
                app.process_step()
                assert app.game.body[0]!=old_head
                # Прохождение реальными шагами, без изменения счёта или выдачи наград вручную.
                for _ in range(6000):
                    direction=choose_direction(app.game)
                    if direction!=app.game.direction:
                        assert app.game.request_direction(direction)
                    app.process_step()
                    if app.state!="playing":
                        break
                assert app.state=="won",(level.id,app.game.reason)
                assert app.game.score==level.goal
                assert level.id in app.save.data["completed_levels"]
                frame(f"09-{level.id}-won")
                assert len(app.effects.particles)<=level.goal*10
            assert app.save.data["total_apples"]==30
            assert len(app.save.data["quests"])==5
            app.show_main()
            app.show_customization()
            for color in ("pink","blue","lavender","yellow","green"):
                assert app.save.select("colors",color)
            assert app.save.select("eyes","blue")
            assert app.save.select("accessories","glasses")
            assert app.save.select("accessories","cap")
            app.refresh_preview()
            app.ui.customization()
            frame("10-customization-cap")
            assert app.save.select("accessories","crown")
            app.refresh_preview()
            frame("11-customization-crown")
            assert SaveManager(app.save.path).data==app.save.data
            app.show_levels()
            frame("12-levels-complete")
            app.show_quests()
            frame("13-quests-complete")

            app.start_game(ENDLESS)
            app.countdown=0
            # Здесь работает обычный аккумулятор времени, а не ручной process_step.
            for _ in range(300):
                app.taskMgr.step()
                if app.state=="lost":
                    break
            assert app.state=="lost"
            frame("14-lost")
            app.retry_key()
            assert app.state=="playing" and app.game.score==0
            frame("15-camera-minimap")
            # Обходим квадрат, проверяя все направления камеры.
            app.countdown=100000
            for index in range(4):
                app.game.turn(1)
                app.process_step()
                for _ in range(18):
                    app.taskMgr.step()
                frame(f"16-camera-turn-{index}")
            for name,points,direction in (
                ("south",[(3,0),(2,0),(1,0),(0,0)],Direction.NORTH),
                ("north",[(16,19),(17,19),(18,19),(19,19)],Direction.SOUTH),
                ("west",[(0,16),(0,17),(0,18),(0,19)],Direction.EAST),
                ("east",[(19,3),(19,2),(19,1),(19,0)],Direction.WEST)):
                # Отдельные допустимые конфигурации у стен для проверки обзора камеры.
                app.game.body=list(points)
                app.game.previous=list(points)
                app.game.direction=direction
                app.game.pending_direction=None
                app.accumulator=0
                app.follow.update(points[0],-90*int(direction),1/60,6.2,snap=True)
                frame(f"16-border-{name}")
            app.show_main()

            baseline=app.render.findAllMatches("**/world").getNumPaths()
            assert baseline==1
            for _ in range(6):
                app.start_game(LEVELS[0])
                app.show_main()
            assert app.render.findAllMatches("**/world").getNumPaths()==baseline
            assert app.aspect2d.findAllMatches("**/minimap").getNumPaths()==0

            if not windowed:
                for width,height,name in ((800,900,"17-portrait"),(1600,900,"18-wide")):
                    assert app.openMainWindow(type="offscreen",size=(width,height),keepCamera=True)
                    app.adjustWindowAspectRatio(width/height)
                    app.ui.resize()
                    app.camLens.setAspectRatio(width/height)
                    frame(name)
            else:
                for width,height,name in ((900,700,"17-window-resize"),(1280,800,"18-window-restore")):
                    props=WindowProperties()
                    props.setSize(width,height)
                    app.win.requestProperties(props)
                    frame(name)
                    assert abs(app.getAspectRatio()-width/height)<0.01
            app.show_settings("menu")
            app.confirm_reset("menu")
            app.reset_progress("menu")
            assert app.save.data["total_apples"]==0
            assert app.state=="menu"
            count=sum(name!="fps-30-equals-144" for name in checks)
            report={"checks":checks,"screenshots":count,"passed":True,"levels_completed":3,
                    "real_apple_events":30,"profile":"temporary","windowed":windowed,
                    "frozen":bool(getattr(sys,"frozen",False)),"resource_root":str(ASSETS),
                    "font_valid":bool(app.font.isValid()),
                    "sound_lengths_seconds":{name:round(sound.length(),3) for name,sound in app.audio.sounds.items()}}
            (output/"smoke-report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
            print(f"PASS: {len(checks)} checks, {count} screenshots; all levels, rewards, saves, menus, camera and scene cleanup")
        finally:
            app.destroy()


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--windowed",action="store_true")
    run(parser.parse_args().windowed)
