"""Неподвижная 2D-карта. Ни второй камеры, ни RenderTexture."""
from panda3d.core import CardMaker, LineSegs, TextNode
from direct.gui.DirectGui import DirectFrame, DirectLabel, DGG


class Minimap:
    def __init__(self,app,font):
        self.app=app
        self.root=app.a2dTopRight.attachNewNode("minimap")
        self.root.setPos(-0.24,0,-0.25)
        self.panel=DirectFrame(parent=self.root,frameColor=(0.98,0.98,0.94,0.93),
                               frameSize=(-0.20,0.20,-0.22,0.20),relief=DGG.FLAT)
        self.label=DirectLabel(parent=self.root,text="КАРТА САДА",text_font=font,text_scale=0.024,
                               text_fg=(0.30,0.40,0.35,1),pos=(0,0,0.16),frameColor=(0,0,0,0))
        self.dynamic=self.root.attachNewNode("map-cells")
        self.size=0.31
        self.last=None

    def square(self,parent,x,z,s,color):
        maker=CardMaker("cell")
        maker.setFrame(-s/2,s/2,-s/2,s/2)
        node=parent.attachNewNode(maker.generate())
        node.setPos(x,0,z)
        node.setColor(*color)
        return node

    def update(self,game,color):
        signature=(tuple(game.body),game.food,game.direction)
        if signature==self.last:
            return
        self.last=signature
        self.dynamic.removeNode()
        self.dynamic=self.root.attachNewNode("map-cells")
        s=self.size/game.size
        def point(cell):
            return ((cell[0]+0.5)*s-self.size/2,(cell[1]+0.5)*s-self.size/2-0.015)
        self.square(self.dynamic,0,-0.015,self.size+0.012,(0.52,0.64,0.55,1))
        self.square(self.dynamic,0,-0.015,self.size,(0.84,0.88,0.77,1))
        for cell in game.obstacles:
            self.square(self.dynamic,*point(cell),s*0.95,(0.50,0.47,0.43,1))
        for cell in reversed(game.body):
            self.square(self.dynamic,*point(cell),s*0.92,color)
        if game.food is not None:
            self.square(self.dynamic,*point(game.food),s*0.85,(0.88,0.25,0.33,1))
        x,z=point(game.body[0])
        self.square(self.dynamic,x,z,s,(0.16,0.34,0.24,1))
        dx,dy=game.direction.vector
        arrow=LineSegs("direction")
        arrow.setColor(1,1,0.9,1)
        arrow.setThickness(2)
        arrow.moveTo(x-dx*s*0.2,-0.01,z-dy*s*0.2)
        arrow.drawTo(x+dx*s*0.65,-0.01,z+dy*s*0.65)
        self.dynamic.attachNewNode(arrow.create())

    def destroy(self):
        self.panel.destroy()
        self.label.destroy()
        self.root.removeNode()
