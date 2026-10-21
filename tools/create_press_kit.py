"""Реальные скриншоты и обложки itch.io средствами самого Panda3D."""
from pathlib import Path
from random import Random
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from panda3d.core import ClockObject
from game.app import SnakeApp
from game.food import FoodVisual
from game.levels import LEVELS
from game.resources import screenshot
from tools.autoplay import choose_direction


def create():
    output=ROOT/"publishing"/"itchio"
    shots=output/"screenshots"
    shots.mkdir(parents=True,exist_ok=True)
    temp=ROOT/"artifacts"/"press-kit-temp"
    temp.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=temp) as profile:
        app=SnakeApp(offscreen=True,save_path=Path(profile)/"save.json",audio=False)
        clock=ClockObject.getGlobalClock()
        clock.setMode(ClockObject.MNonRealTime)
        clock.setDt(1/60)
        def render(path):
            for _ in range(5):
                app.taskMgr.step()
            screenshot(app.win,path)
        try:
            # Косметика открывается обычным прохождением на временном профиле.
            for index,level in enumerate(LEVELS):
                app.start_game(level)
                app.countdown=100000
                app.game.rng=Random(index+4)
                app.game.food=app.game.spawn_food()
                for _ in range(6000):
                    direction=choose_direction(app.game)
                    if direction!=app.game.direction:
                        app.game.request_direction(direction)
                    app.process_step()
                    if app.state!="playing":
                        break
                assert app.state=="won"

            for index,level in enumerate(LEVELS):
                app.save.data["selected"]["accessories"]=[]
                app.save.select("colors",("green","yellow","lavender")[index])
                if index:
                    app.save.select("accessories","glasses")
                if index==2:
                    app.save.select("accessories","cap")
                app.start_game(level)
                app.countdown=100000
                app.clear_notice()
                # Свободная клетка перед головой хорошо показывает модель еды.
                app.game.food=(10,13)
                render(shots/f"0{index+1}-{level.id}.png")
            app.show_main()
            app.show_customization()
            render(shots/"04-customization.png")
            app.show_quests()
            render(shots/"05-achievements.png")

            app.save.select("colors","green")
            app.save.data["selected"]["accessories"]=[]
            app.show_main()
            app.ui.clear()
            app.clear_notice()
            apple=FoodVisual(app.world.root)
            apple.update((8.4,5.8),0)
            app.camera.setPos(12,1,5.8)
            app.camera.lookAt(11,7.7,0.4)
            for width,height,name in ((1260,1000,"cover-1260x1000.png"),(630,500,"cover-630x500.png")):
                assert app.openMainWindow(type="offscreen",size=(width,height),keepCamera=True)
                app.adjustWindowAspectRatio(width/height)
                app.camLens.setAspectRatio(width/height)
                app.ui.clear()
                app.ui.panel(0,0.68,2.26,0.45,(0.98,0.97,0.91,0.96))
                app.ui.text("МАЛЕНЬКОЕ ПУТЕШЕСТВИЕ",0,0.80,0.040)
                app.ui.text("SNAKE 3D",0,0.61,0.15)
                app.ui.text("Ещё одно яблоко. Ещё одно приключение.",0,0.36,0.041)
                app.ui.panel(0,-0.79,2.14,0.13,(0.98,0.97,0.91,0.97))
                app.ui.text("УЮТНАЯ ЗМЕЙКА  ·  3 МИРА",0,-0.803,0.042)
                for _ in range(5):
                    app.taskMgr.step()
                app.ui.root.setScale(1)
                app.graphicsEngine.renderFrame()
                app.graphicsEngine.renderFrame()
                screenshot(app.win,output/name)
            print(f"Press kit: {output}; 2 covers and 5 screenshots")
        finally:
            app.destroy()


if __name__=="__main__":
    create()
