"""Все меню DirectGUI. Координаты даны в системе aspect2d."""
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectButton, DirectSlider, DGG
from panda3d.core import TextNode
from config import BODY_COLORS, EYE_COLORS, ACCESSORIES
from game.levels import LEVELS, ENDLESS
from game.quests import QUESTS, quest_progress
from game.geometry import rounded_card

INK=(0.19,0.29,0.25,1)
MUTED=(0.39,0.46,0.42,1)
PAPER=(0.98,0.97,0.91,0.97)
GREEN=(0.39,0.59,0.42,1)


class UI:
    def __init__(self,app,font):
        self.app,self.font=app,font
        self.widgets=[]
        self.root=None
        self.anchors=[]
        self.hud_score=None
        self.clear()

    def clear(self):
        for widget in reversed(self.widgets):
            widget.destroy()
        self.widgets=[]
        if self.root:
            self.root.removeNode()
        for anchor in self.anchors:
            anchor.removeNode()
        self.anchors=[]
        self.root=self.app.aspect2d.attachNewNode("screen-ui")
        self.resize()
        self.hud_score=None

    def resize(self):
        if self.root:
            self.root.setScale(min(1,self.app.getAspectRatio()/1.62))
        for anchor in self.anchors:
            anchor.setScale(min(1,self.app.getAspectRatio()/1.25))

    def anchor(self,parent):
        node=parent.attachNewNode("ui-anchor")
        self.anchors.append(node)
        node.setScale(min(1,self.app.getAspectRatio()/1.25))
        return node

    def panel(self,x,z,w,h,color=PAPER,parent=None):
        frame=DirectFrame(parent=parent or self.root,geom=rounded_card(w,h,color),frameSize=(-w/2,w/2,-h/2,h/2),
                          pos=(x,0,z),relief=None)
        self.widgets.append(frame)
        return frame

    def text(self,text,x,z,size=0.045,color=INK,align=TextNode.ACenter,parent=None,**kwargs):
        label=DirectLabel(parent=parent or self.root,text=text,text_font=self.font,text_scale=size,
                          text_fg=color,text_align=align,frameColor=(0,0,0,0),pos=(x,-0.02,z),**kwargs)
        self.widgets.append(label)
        return label

    def button(self,text,x,z,command,width=0.83,enabled=True,primary=False,size=0.041):
        normal=GREEN if primary else (0.88,0.91,0.83,1)
        colors=(normal,(0.70,0.79,0.66,1),(0.79,0.86,0.73,1),(0.87,0.87,0.83,1))
        def clicked():
            self.app.audio.play("click")
            command()
        button=DirectButton(parent=self.root,text=text,text_font=self.font,text_scale=size,
                            text_fg=(1,1,0.94,1) if primary else INK,
                            text_pos=(0,-0.014),frameSize=(-width/2,width/2,-0.061,0.061),
                            geom=tuple(rounded_card(width,0.122,c,0.035) for c in colors),
                            frameColor=colors,pos=(x,-0.03,z),relief=None,pressEffect=0,
                            state=DGG.NORMAL if enabled else DGG.DISABLED,command=clicked)
        self.widgets.append(button)
        return button

    def progress_bar(self,current,target,x,z,width=1.68,height=0.022,completed=False):
        self.panel(x+width/2,z,width,height,(0.84,0.87,0.80,1))
        filled=width*max(0,min(1,current/target))
        if filled>0:
            color=GREEN if completed else (0.56,0.72,0.48,1)
            self.panel(x+filled/2,z,filled,height,color)

    def title(self,kicker,title,subtitle=""):
        self.text(kicker,0,0.81,0.029,MUTED)
        self.text(title,0,0.65,0.072)
        if subtitle:
            self.text(subtitle,0,0.53,0.034,MUTED)

    def footer(self,text="A / D или стрелки — поворот     ·     Esc — пауза"):
        self.text(text,0,-0.91,0.028,MUTED)

    def main(self):
        self.clear()
        self.panel(-0.77,0.0,1.10,1.64)
        self.text("S N A K E  /  3 D",-0.77,0.67,0.032,MUTED)
        self.text("Маленькое\nпутешествие",-0.77,0.46,0.068)
        self.text("Одно яблоко — одна история",-0.77,0.28,0.030,MUTED)
        for label,z,command,primary in (
            ("Играть",0.12,self.app.play_next,True),
            ("Выбор уровня",-0.05,self.app.show_levels,False),
            ("Кастомизация",-0.22,self.app.show_customization,False),
            ("Достижения",-0.39,self.app.show_quests,False),
            ("Настройки",-0.56,lambda:self.app.show_settings("menu"),False)):
            self.button(label,-0.77,z,command,primary=primary)
        self.button("Выход",-0.77,-0.73,self.app.quit,width=0.83,size=0.032)
        self.text("Знакомьтесь, ваша змейка",0.65,-0.64,0.038)
        self.text("Собирайте яблоки. Открывайте маленькие радости.",0.65,-0.73,0.026,MUTED)
        self.footer()

    def levels(self):
        self.clear()
        self.title("КУДА ОТПРАВИМСЯ?","Выберите свой мир","Три маленьких приключения и бесконечная прогулка")
        data=self.app.save.data
        for i,level in enumerate(LEVELS):
            x=(i-1)*0.99
            unlocked=level.id in data["unlocked_levels"]
            complete=level.id in data["completed_levels"]
            self.panel(x,0.03,0.92,0.78)
            self.panel(x,0.32,0.92,0.17,level.floor)
            self.text(f"0{i+1}  /  "+("ПРОЙДЕН" if complete else "ОТКРЫТ" if unlocked else "ЗАКРЫТ"),x,0.31,0.029)
            self.text(level.name,x,0.16,0.043)
            self.text(f"Цель: {level.goal} яблок\nНаграда: {level.reward}",x,0.00,0.029,MUTED)
            self.text(f"Рекорд: {data['records'].get(level.id,0)}",x,-0.14,0.030)
            self.button("Начать" if unlocked else "Пройдите предыдущий",x,-0.27,
                        lambda l=level:self.app.start_game(l),width=0.80,enabled=unlocked,primary=unlocked,size=0.031)
        self.button("Бесконечный режим",0,-0.56,lambda:self.app.start_game(ENDLESS),width=1.20)
        self.button("Главное меню",0,-0.75,self.app.show_main,width=1.20)

    def customization(self):
        self.clear()
        self.panel(-0.65,0.0,1.64,1.76)
        self.text("ВАШ МАЛЕНЬКИЙ ГЕРОЙ",-0.65,0.74,0.029,MUTED)
        self.text("Кастомизация",-0.65,0.61,0.064)
        self.text("Цвет тела",-1.31,0.47,0.035,align=TextNode.ALeft)
        data=self.app.save.data
        def choice(category,key):
            if self.app.save.select(category,key):
                self.app.refresh_preview()
                self.customization()
        for i,(key,(name,color)) in enumerate(BODY_COLORS.items()):
            x=-1.14+(i%3)*0.49
            z=0.34-(i//3)*0.14
            unlocked=key in data["unlocked"]["colors"]
            chosen=data["selected"]["color"]==key
            self.button(("• " if chosen else "")+name,x,z,lambda k=key:choice("colors",k),width=0.46,
                        enabled=unlocked,primary=chosen,size=0.032)
        self.text("Цвет глаз",-1.31,0.065,0.035,align=TextNode.ALeft)
        for i,(key,(name,_)) in enumerate(EYE_COLORS.items()):
            self.button(name,-1.14+i*0.49,-0.06,lambda k=key:choice("eyes",k),width=0.46,size=0.027,
                        enabled=key in data["unlocked"]["eyes"],primary=data["selected"]["eyes"]==key)
        self.text("Аксессуары",-1.31,-0.22,0.035,align=TextNode.ALeft)
        for i,(key,name) in enumerate(ACCESSORIES.items()):
            unlocked=key in data["unlocked"]["accessories"]
            selected=key in data["selected"]["accessories"]
            self.button(("Снять: " if selected else "")+name,-0.65,-0.35-i*0.135,
                        lambda k=key:choice("accessories",k),width=1.35,enabled=unlocked,primary=selected,size=0.033)
        self.button("Готово",-0.65,-0.78,self.app.show_main,width=1.35,primary=True)
        self.text("Ваш образ сохраняется автоматически",0.79,-0.56,0.029)
        self.text("Как открыть закрытые предметы:\nрозовый — мир 1; очки и лаванда — мир 2;\nкепка и корона — мир 3; голубой — 20 яблок;\nжёлтый и зелёные глаза — длина 15.",0.79,-0.72,0.026,MUTED)
        self.footer("Закрытые предметы показаны серым. Голубые глаза — за 20 яблок.")

    def quests(self):
        self.clear()
        data=self.app.save.data
        self.title("МАЛЕНЬКИЕ ДОСТИЖЕНИЯ","Коллекция радостей",f"Всего яблок: {data['total_apples']}   ·   Максимальная длина: {data['max_length']}")
        for i,q in enumerate(QUESTS):
            z=0.32-i*0.24
            done=q.id in data["quests"]
            current,target=quest_progress(q.id,data)
            self.panel(0,z,2.65,0.22)
            self.text("ГОТОВО" if done else "В ПУТИ",-1.13,z+0.02,0.025,GREEN if done else MUTED)
            self.text(q.title,-0.87,z+0.045,0.036,align=TextNode.ALeft)
            self.text(q.description,-0.87,z-0.006,0.030,MUTED,align=TextNode.ALeft)
            self.text(q.reward,1.20,z+0.035,0.023,MUTED,align=TextNode.ARight)
            self.progress_bar(current,target,-0.87,z-0.062,completed=done)
            self.text(f"{current} / {target}",1.20,z-0.073,0.030,GREEN if done else INK,align=TextNode.ARight)
        self.button("Главное меню",0,-0.85,self.app.show_main,width=1.2)

    def settings(self,back):
        self.clear()
        self.panel(0,0,1.95,1.70)
        self.title("СДЕЛАЙТЕ СЕБЕ УДОБНО","Настройки")
        self.text("Громкость звуков",0,0.37,0.041)
        slider=DirectSlider(parent=self.root,range=(0,1),value=self.app.save.data["settings"]["volume"],
                            pageSize=0.05,scale=0.61,pos=(0,-0.03,0.23),frameColor=(0.77,0.83,0.71,1),
                            thumb_frameColor=GREEN)
        self.widgets.append(slider)
        def volume():
            self.app.save.data["settings"]["volume"]=float(slider["value"])
            self.app.audio.set_volume(slider["value"])
        slider["command"]=volume
        self.text("Расстояние до камеры",0,0.04,0.041)
        camera=DirectSlider(parent=self.root,range=(4.5,8),value=self.app.save.data["settings"]["camera_distance"],
                            pageSize=0.25,scale=0.61,pos=(0,-0.03,-0.10),frameColor=(0.77,0.83,0.71,1),thumb_frameColor=GREEN)
        self.widgets.append(camera)
        camera["command"]=lambda:self.app.save.data["settings"].update(camera_distance=float(camera["value"]))
        self.text("A / влево — левый поворот     D / вправо — правый\nEsc — пауза     R — повтор после проигрыша",0,-0.32,0.028,MUTED)
        self.button("Сбросить прогресс",0,-0.54,lambda:self.app.confirm_reset(back),width=1.30,size=0.035)
        self.button("Готово",0,-0.73,lambda:self.app.close_settings(back),width=1.30,primary=True)

    def confirm_reset(self,back):
        self.clear()
        self.panel(0,0,1.92,1.0)
        self.text("Начать с чистого листа?",0,0.28,0.055)
        self.text("Рекорды, награды и выбранный образ\nбудут сброшены. Это действие нельзя отменить.",0,0.05,0.034,MUTED)
        self.button("Сбросить",-0.43,-0.25,lambda:self.app.reset_progress(back),width=0.75)
        self.button("Отмена",0.43,-0.25,lambda:self.app.show_settings(back),width=0.75,primary=True)

    def hud(self,level):
        self.clear()
        anchor=self.anchor(self.app.a2dTopLeft)
        self.panel(0.39,-0.20,0.61,0.26,parent=anchor)
        self.text(level.name,0.15,-0.15,0.037,align=TextNode.ALeft,parent=anchor)
        self.hud_score=self.text("",0.15,-0.23,0.032,MUTED,align=TextNode.ALeft,parent=anchor)
        self.button("Пауза  ·  Esc",0,-0.86,self.app.pause,width=0.72,size=0.030)
        self.text("A / ВЛЕВО     ПОВОРОТЫ     D / ВПРАВО",0,-0.96,0.025,MUTED)

    def update_hud(self,game,level):
        if self.hud_score:
            goal=f" / {level.goal}" if level.goal else ""
            self.hud_score["text"]=f"Яблоки: {game.score}{goal}   ·   Длина: {len(game.body)}"

    def pause(self):
        self.clear()
        self.panel(0,0,1.55,1.23)
        self.text("Небольшой привал",0,0.42,0.060)
        for label,z,cmd in (("Продолжить",0.20,self.app.resume),("Начать заново",0.02,self.app.restart_game),
                            ("Настройки",-0.16,lambda:self.app.show_settings("paused")),("Главное меню",-0.34,self.app.show_main)):
            self.button(label,0,z,cmd,width=1.19,primary=z==0.20)
        self.text("Esc — продолжить",0,-0.52,0.029,MUTED)

    def result(self,won):
        self.clear()
        self.panel(0,0,1.98,1.48)
        self.text("ПУТЕШЕСТВИЕ ПРОДОЛЖАЕТСЯ",0,0.59,0.026,MUTED)
        self.text("Какой чудесный день!" if won else "Попробуем ещё раз?",0,0.43,0.061)
        game,level=self.app.game,self.app.level
        message=f"Мир «{level.name}» пройден" if won else game.reason
        self.text(message,0,0.28,0.032,MUTED)
        record=self.app.save.data["records"].get(level.id,0)
        self.text(f"Яблоки: {game.score}     ·     Рекорд: {record}",0,0.12,0.044)
        self.text(("Награда: "+level.reward) if won and level.id!="endless" else "Каждая прогулка делает вас опытнее",0,-0.04,0.032,MUTED)
        next_level=self.app.next_level() if won else None
        self.button("Следующий уровень" if next_level else "Ещё одна прогулка",0,-0.25,
                    (lambda:self.app.start_game(next_level)) if next_level else self.app.restart_game,width=1.45,primary=True)
        self.button("Главное меню",0,-0.44,self.app.show_main,width=1.45)
        self.text("R — повторить" if not won else "Новый образ ждёт в меню кастомизации",0,-0.63,0.028,MUTED)
