"""Сцена: пастельные плитки, бортики и декорации за границей сетки."""
from random import Random
from math import sin, cos, pi
from panda3d.core import AmbientLight, DirectionalLight, Vec4
from config import GRID_SIZE
from game.geometry import ellipsoid, rounded_box, shadow


class World:
    def __init__(self, app, level):
        self.app, self.level = app, level
        self.root = app.render.attachNewNode("world")
        self.decorations=[]
        app.setBackgroundColor(*level.sky)
        ambient = AmbientLight("soft-sky")
        ambient.setColor(Vec4(0.67,0.69,0.73,1))
        sun = DirectionalLight("warm-sun")
        sun.setColor(Vec4(0.48,0.44,0.37,1))
        an = self.root.attachNewNode(ambient)
        sn = self.root.attachNewNode(sun)
        sn.setHpr(-35,-55,0)
        self.root.setLight(an)
        self.root.setLight(sn)
        static = self.root.attachNewNode("static-arena")
        size = GRID_SIZE
        # Игровая клетка (0,0) находится в центре угловой плитки.
        middle = (size-1)/2
        rounded_box(static,(middle,middle,-0.55),(size+1.3,size+1.3,1.0),(0.48,0.57,0.43,1),0.65)
        rng = Random(42)
        for x in range(size):
            for y in range(size):
                shift = rng.uniform(-0.022,0.022) + (0.018 if (x+y)%2 else 0)
                color = tuple(max(0,min(1,v+shift)) for v in level.floor[:3])+(1,)
                rounded_box(static,(x,y,-0.02),(0.986,0.986,0.10),color,0.055)
        curb = tuple(v*0.87 for v in level.floor[:3])+(1,)
        for pos,scale in (((middle,-0.72,0.14),(size+1.0,0.32,0.37)),
                          ((middle,size-0.28,0.14),(size+1.0,0.32,0.37)),
                          ((-0.72,middle,0.14),(0.32,size+1.0,0.37)),
                          ((size-0.28,middle,0.14),(0.32,size+1.0,0.37))):
            rounded_box(static,pos,scale,curb,0.15)
        for x,y in ((-0.72,-0.72),(-0.72,size-0.28),(size-0.28,-0.72),(size-0.28,size-0.28)):
            ellipsoid(static,(x,y,0.30),(0.35,0.35,0.33),(0.96,0.88,0.65,1))
        for x,y in level.obstacles:
            shadow(static,x,y,0.56,0.55)
            ellipsoid(static,(x,y,0.38),(0.48,0.46,0.42),(0.60,0.55,0.47,1),0.72)
            ellipsoid(static,(x-0.12,y-0.15,0.67),(0.20,0.19,0.09),(0.74,0.68,0.59,1))
        for i in range(24):
            edge = i%4
            a = -2.8 if edge < 2 else size+1.8
            b = rng.uniform(-2,size+1)
            x,y = (a,b) if edge%2==0 else (b,a)
            decoration=self.root.attachNewNode("decoration")
            decoration.setPos(x,y,0)
            if level.theme=="garden":
                self.tree(decoration,0,0,rng)
            elif level.theme=="sand":
                self.cactus(decoration,0,0,rng)
            else:
                self.lavender(decoration,0,0,rng)
            decoration.flattenStrong()
            self.decorations.append((decoration,x,y))
        # Основание под островом и мягкие отдалённые холмы.
        rounded_box(static,(middle,middle,-1.20),(90,90,0.3),tuple(v*0.93 for v in level.sky[:3])+(1,),6)
        static.flattenStrong()

    def update_visibility(self,camera,head):
        """Декор у бортика не должен заслонять персонажа камерой снаружи поля."""
        cx,cy=camera.getX(),camera.getY()
        hx,hy=head
        dx,dy=hx-cx,hy-cy
        length_squared=dx*dx+dy*dy
        for node,x,y in self.decorations:
            t=((x-cx)*dx+(y-cy)*dy)/max(length_squared,0.001)
            t_clamped=max(0,min(1,t))
            distance_squared=(x-cx-dx*t_clamped)**2+(y-cy-dy*t_clamped)**2
            if -0.2<t<1.05 and distance_squared<2.3**2:
                node.hide()
            else:
                node.show()

    def tree(self, parent,x,y,rng):
        s = rng.uniform(0.8,1.35)
        shadow(parent,x,y,1.0*s,0.75*s)
        ellipsoid(parent,(x,y,0.8*s),(0.17*s,0.18*s,1.0*s),(0.58,0.42,0.28,1),0.8)
        for dx,dy,dz in ((0,0,2),(-0.5,0,1.8),(0.45,0.1,1.9),(0,0.3,2.4)):
            c = (0.44+rng.random()*0.1,0.64+rng.random()*0.1,0.42,1)
            ellipsoid(parent,(x+dx*s,y+dy*s,dz*s),(0.85*s,0.78*s,0.8*s),c,0.82)
        for dx in (-0.23,0.25):
            ellipsoid(parent,(x+dx,y-0.64*s,1.85*s),(0.12,0.12,0.12),(0.94,0.65,0.49,1))

    def cactus(self,parent,x,y,rng):
        s=rng.uniform(0.8,1.3)
        shadow(parent,x,y,0.7,0.6)
        green=(0.42,0.66,0.53,1)
        ellipsoid(parent,(x,y,1.05*s),(0.32,0.33,1.15*s),green,0.8)
        for dx, z in ((-0.53,0.8),(0.5,1.1)):
            ellipsoid(parent,(x+dx/2,y,z*s),(0.45,0.20,0.20),green,0.8)
            ellipsoid(parent,(x+dx,y,(z+0.25)*s),(0.19,0.20,0.44),green,0.8)
        ellipsoid(parent,(x+0.1,y,2.2*s),(0.14,0.15,0.10),(0.94,0.58,0.61,1))
        ellipsoid(parent,(x+0.85,y+0.4,0.22),(0.45,0.40,0.28),(0.71,0.63,0.54,1),0.65)

    def lavender(self,parent,x,y,rng):
        shadow(parent,x,y,0.85,0.65)
        for dx in (-0.32,0,0.32):
            ellipsoid(parent,(x+dx,y,0.55),(0.07,0.09,0.6),(0.49,0.63,0.49,1))
            ellipsoid(parent,(x+dx,y,1.05+abs(dx)),(0.22,0.25,0.40),(0.68,0.51+rng.random()*0.14,0.82,1))
        if rng.random()<0.6:
            for dx in (-0.8,0,0.7):
                ellipsoid(parent,(x+dx,y,4.0),(0.9,0.65,0.46),(0.97,0.94,0.99,1),0.8)

    def destroy(self):
        self.root.removeNode()
