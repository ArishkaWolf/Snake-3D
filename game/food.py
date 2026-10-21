"""Яблоко и короткое кольцо искр при подборе."""
from math import sin, cos, pi
from game.geometry import ellipsoid, shadow


class FoodVisual:
    def __init__(self,parent):
        self.root=parent.attachNewNode("apple")
        self.model=self.root.attachNewNode("apple-model")
        for x in (-0.12,0.12):
            ellipsoid(self.model,(x,0,0.48),(0.29,0.34,0.36),(0.91,0.28,0.32,1),0.85)
        ellipsoid(self.model,(-0.18,-0.24,0.62),(0.075,0.025,0.13),(1,0.68,0.61,1))
        stem=ellipsoid(self.model,(0,0,0.91),(0.048,0.05,0.18),(0.42,0.28,0.19,1),0.8)
        stem.setR(-16)
        leaf=ellipsoid(self.model,(0.19,0,0.93),(0.23,0.10,0.055),(0.35,0.64,0.34,1))
        leaf.setR(-25)
        self.shade=shadow(self.root,0,0,0.45,0.38)

    def update(self,cell,time):
        if cell is None:
            self.root.hide()
            return
        self.root.show()
        self.root.setPos(cell[0],cell[1],0)
        self.model.setZ(0.06+0.06*sin(time*2.5))
        self.model.setH(sin(time*0.8)*12)


class PickupEffects:
    def __init__(self,parent):
        self.root=parent.attachNewNode("pickup-effects")
        self.particles=[]

    def emit(self,cell):
        for i in range(10):
            angle=2*pi*i/10
            node=ellipsoid(self.root,(cell[0],cell[1],0.5),(0.10,0.10,0.10),(1,0.86,0.39,1))
            node.setLightOff()
            self.particles.append([node,cell,angle,0.0])

    def update(self,dt):
        alive=[]
        for node,cell,angle,age in self.particles:
            age+=dt
            if age>=0.65:
                node.removeNode()
                continue
            node.setPos(cell[0]+cos(angle)*age*1.8,cell[1]+sin(angle)*age*1.8,0.5+sin(age/0.65*pi)*0.8)
            node.setScale(0.10*(1-age/0.65))
            alive.append([node,cell,angle,age])
        self.particles=alive
