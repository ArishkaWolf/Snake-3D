"""Координатор приложения. Меню, сеанс игры и отрисовка живут раздельно."""
from math import sin, cos
from pathlib import Path
from panda3d.core import (loadPrcFileData, Filename, AntialiasAttrib, ClockObject, WindowProperties)
from direct.showbase.ShowBase import ShowBase
from config import ASSETS, TITLE, WINDOW_SIZE, BODY_COLORS
from game.snake import SnakeGame
from game.levels import LEVELS, ENDLESS
from game.save_manager import SaveManager
from game.world import World
from game.customization import SnakeVisual
from game.camera import FollowCamera
from game.food import FoodVisual, PickupEffects
from game.minimap import Minimap
from game.audio import Audio
from game.ui import UI
from game.resources import mount_assets


class SnakeApp(ShowBase):
    def __init__(self,offscreen=False,save_path=None,audio=True):
        loadPrcFileData("snake",f"window-title {TITLE}\nwin-size {WINDOW_SIZE[0]} {WINDOW_SIZE[1]}\n"
                        "sync-video true\nframebuffer-multisample 1\nmultisamples 4\n"
                        "textures-power-2 none\nnotify-level warning\n")
        if not audio:
            loadPrcFileData("silent","audio-library-name null")
        super().__init__(windowType="offscreen" if offscreen else None)
        self.disableMouse()
        self.render.setAntialias(AntialiasAttrib.MAuto)
        self.camLens.setFov(61)
        self.camLens.setNearFar(0.15,140)
        self.save=SaveManager(save_path)
        self.resource_mount=mount_assets()
        self.font=self.loader.loadFont("/snake-assets/fonts/NotoSans-Regular.ttf")
        self.font.setPixelsPerUnit(64)
        self.audio=Audio(self,self.save.data["settings"]["volume"])
        self.ui=UI(self,self.font)
        self.state="menu"
        self.world=None
        self.visual=None
        self.minimap=None
        self.game=None
        self.level=LEVELS[0]
        self.accumulator=0.0
        self.time=0.0
        self.countdown=0.0
        self.follow=FollowCamera(self.camera)
        self.notice=None
        self.notice_time=0.0
        self.exitFunc=self.persist_progress
        self.accept("a",self.turn,[-1])
        self.accept("arrow_left",self.turn,[-1])
        self.accept("d",self.turn,[1])
        self.accept("arrow_right",self.turn,[1])
        # На русской раскладке клавиши A и D посылают ф/в.
        self.accept("ф",self.turn,[-1])
        self.accept("в",self.turn,[1])
        self.accept("escape",self.escape)
        self.accept("r",self.retry_key)
        self.accept("к",self.retry_key)
        self.accept("window-event",self.window_event)
        self.accept("aspectRatioChanged",self.ui.resize)
        self.accept("focus-lost",self.pause)
        self.taskMgr.add(self.update,"snake-update")
        self.show_main()
        if self.save.warning:
            self.toast(self.save.warning,8)

    def clear_scene(self):
        if self.minimap:
            self.minimap.destroy()
            self.minimap=None
        if self.world:
            self.world.destroy()
        self.world=None
        self.visual=None
        self.game=None
        self.food_visual=None
        self.effects=None

    def menu_scene(self):
        self.clear_scene()
        self.world=World(self,LEVELS[0])
        self.refresh_preview()
        self.camera.setPos(12,-2.0,7.2)
        self.camera.lookAt(9.5,7.2,0.40)

    def refresh_preview(self):
        if self.visual:
            self.visual.destroy()
        self.visual=SnakeVisual(self.world.root,self.save.data["selected"])
        # Большая голова смотрит к зрителю; изгиб подчёркивает цельность тела.
        points=[(11,6),(11,7),(11.1,8),(11.6,8.8),(12.5,9.1),(13.4,9.0),(14,8.3),(14.2,7.4)]
        self.visual.update(points,180,snap=True)
        if self.state=="customization":
            self.visual.root.setScale(0.78)
            self.visual.root.setPos(4.22,2.02,0.05)

    def clear_notice(self):
        if self.notice:
            self.notice.destroy()
            self.notice=None

    def show_main(self):
        self.clear_notice()
        if self.game:
            self.save.finish(self.level.id,self.game.score,False)
        self.state="menu"
        self.menu_scene()
        self.ui.main()

    def show_levels(self):
        self.clear_notice()
        self.state="levels"
        self.ui.levels()

    def show_customization(self):
        self.clear_notice()
        self.state="customization"
        self.refresh_preview()
        self.ui.customization()

    def show_quests(self):
        self.clear_notice()
        self.state="quests"
        self.ui.quests()

    def play_next(self):
        for level in LEVELS:
            if level.id not in self.save.data["completed_levels"]:
                self.start_game(level)
                return
        self.start_game(ENDLESS)

    def next_level(self):
        index=next((i for i,l in enumerate(LEVELS) if l.id==self.level.id),None)
        return LEVELS[index+1] if index is not None and index<2 else None

    def start_game(self,level):
        if level.id not in self.save.data["unlocked_levels"]:
            return False
        self.clear_scene()
        self.level=level
        self.game=SnakeGame(goal=level.goal,obstacles=level.obstacles)
        self.world=World(self,level)
        self.visual=SnakeVisual(self.world.root,self.save.data["selected"])
        self.food_visual=FoodVisual(self.world.root)
        self.effects=PickupEffects(self.world.root)
        self.minimap=Minimap(self,self.font)
        self.follow=FollowCamera(self.camera)
        self.accumulator=0.0
        self.countdown=1.5
        self.state="playing"
        self.ui.hud(level)
        self.visual.update(self.game.body,0,snap=True)
        self.follow.update(self.game.body[0],0,0.016,self.save.data["settings"]["camera_distance"],snap=True)
        self.food_visual.update(self.game.food,self.time)
        self.minimap.update(self.game,BODY_COLORS[self.save.data["selected"]["color"]][1])
        self.ui.update_hud(self.game,self.level)
        self.toast("Устраивайтесь поудобнее…  A / D — повороты",1.5)
        return True

    def restart_game(self):
        if self.game:
            self.save.finish(self.level.id,self.game.score,False)
        self.start_game(self.level)

    def retry_key(self):
        if self.state in ("lost","won"):
            self.restart_game()

    def turn(self,side):
        if self.state=="playing":
            self.game.turn(side)

    def pause(self):
        if self.state=="playing":
            self.state="paused"
            self.ui.pause()

    def resume(self):
        if self.state=="paused":
            self.state="playing"
            self.ui.hud(self.level)
            self.ui.update_hud(self.game,self.level)

    def escape(self):
        if self.state=="playing":
            self.pause()
        elif self.state=="paused":
            self.resume()
        elif self.state=="settings":
            self.close_settings(self.settings_back)
        elif self.state=="confirm_reset":
            self.show_settings(self.settings_back)
        elif self.state!="menu":
            self.show_main()

    def show_settings(self,back):
        self.clear_notice()
        self.settings_back=back
        self.state="settings"
        self.ui.settings(back)

    def close_settings(self,back):
        self.save.save()
        if back=="paused":
            self.state="paused"
            self.ui.pause()
        else:
            self.show_main()

    def confirm_reset(self,back):
        self.state="confirm_reset"
        self.ui.confirm_reset(back)

    def reset_progress(self,back):
        if self.save.reset():
            self.audio.set_volume(self.save.data["settings"]["volume"])
            self.show_main()
            self.toast("Новая история начинается здесь")
        else:
            self.show_settings(back)
            self.toast(self.save.warning,6)

    def toast(self,message,duration=3.5):
        if self.notice:
            self.notice.destroy()
        from direct.gui.DirectGui import DirectLabel
        self.notice=DirectLabel(parent=self.aspect2d,text=message,text_font=self.font,text_scale=0.031,
                                text_fg=(0.20,0.32,0.24,1),frameColor=(0.99,0.97,0.87,0.96),
                                pad=(0.035,0.025),pos=(0,-0.2,0.86))
        self.notice.setScale(min(1,self.getAspectRatio()/1.62))
        self.notice_time=duration

    def window_event(self,window):
        if hasattr(window,"getProperties"):
            # Базовый обработчик обновляет aspect2d и обрабатывает крестик окна.
            super().windowEvent(window)
        self.ui.resize()
        if self.notice:
            self.notice.setScale(min(1,self.getAspectRatio()/1.62))
        if hasattr(window,"getProperties"):
            props=window.getProperties()
            if props.hasForeground() and not props.getForeground():
                self.pause()

    def process_step(self):
        before=self.game.score
        cell=self.game.food
        event=self.game.step()
        new=[]
        if self.game.score>before:
            new+=self.save.record_apple(len(self.game.body))
            self.effects.emit(cell)
            self.audio.play("eat")
        if event in ("lost","won"):
            won=event=="won"
            new+=self.save.finish(self.level.id,self.game.score,won)
            self.state=event
            self.audio.play("win" if won else "lose")
            self.ui.result(won)
        if new:
            self.audio.play("unlock")
            self.toast("Открыто: "+" · ".join(q.reward for q in new),5)
        if self.save.warning:
            self.toast(self.save.warning,5)
        return event

    def update(self,task):
        dt=ClockObject.getGlobalClock().getDt()
        self.time+=dt
        if self.notice:
            self.notice_time-=dt
            if self.notice_time<=0:
                self.notice.destroy()
                self.notice=None
        if self.game:
            if self.state=="playing":
                if self.countdown>0:
                    self.countdown=max(0,self.countdown-dt)
                else:
                    self.accumulator+=dt
                    interval=1/self.level.speed
                    while self.accumulator>=interval and self.state=="playing":
                        self.accumulator-=interval
                        self.process_step()
                alpha=min(1,self.accumulator*self.level.speed)
                points=self.game.interpolated(alpha)
                heading=-90*int(self.game.direction)
                self.visual.update(points,heading,dt)
                self.follow.update(points[0],heading,dt,self.save.data["settings"]["camera_distance"])
                self.world.update_visibility(self.camera,points[0])
                self.ui.update_hud(self.game,self.level)
            elif self.state in ("lost","won"):
                self.visual.update(self.game.body,-90*int(self.game.direction),dt)
            if self.state not in ("paused","settings","confirm_reset"):
                self.food_visual.update(self.game.food,self.time)
                self.effects.update(dt)
            self.minimap.update(self.game,BODY_COLORS[self.save.data["selected"]["color"]][1])
        elif self.visual:
            self.visual.head.setP(sin(self.time*1.5)*2)
        return task.cont

    def persist_progress(self):
        if self.game:
            self.save.finish(self.level.id,self.game.score,False)
        else:
            self.save.save()

    def quit(self):
        self.userExit()
