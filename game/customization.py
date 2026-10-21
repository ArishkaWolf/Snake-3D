"""Модель персонажа и аксессуары, прикреплённые к локальному узлу головы."""
from math import atan2, degrees, sin, pi
from panda3d.core import LineSegs, NodePath
from config import BODY_COLORS, EYE_COLORS
from game.geometry import ellipsoid, torus, shadow


class SnakeVisual:
    def __init__(self, parent, selected):
        self.root = parent.attachNewNode("snake")
        self.head = self.root.attachNewNode("head")
        self.body_root = self.root.attachNewNode("body")
        self.color = BODY_COLORS[selected["color"]][1]
        self.segments, self.bridges, self.shadows = [], [], []
        self.heading = 0.0
        self.make_head(selected)

    def make_head(self, selected):
        c = self.color
        belly = tuple(min(1, v*0.58+0.38) for v in c[:3]) + (1,)
        dark = (c[0]*0.4,c[1]*0.52,c[2]*0.44,1)
        ellipsoid(self.head, (0,0.12,0.65), (0.66,0.81,0.57), c, 0.85)
        ellipsoid(self.head, (0,0.66,0.49), (0.60,0.55,0.36), c, 0.8)
        ellipsoid(self.head, (0,0.40,0.26), (0.52,0.62,0.13), belly)
        for x in (-0.34,0.34):
            ellipsoid(self.head, (x,0.33,1.03), (0.30,0.31,0.34), (0.99,0.98,0.89,1))
            ellipsoid(self.head, (x,0.59,1.045), (0.145,0.10,0.19), EYE_COLORS[selected["eyes"]][1])
            ellipsoid(self.head, (x-0.04,0.67,1.12), (0.052,0.025,0.062), (1,1,1,1))
            ellipsoid(self.head, (x*0.76,1.12,0.66), (0.065,0.035,0.043), dark)
            ellipsoid(self.head, (x*1.53,0.90,0.50), (0.060,0.06,0.045), (0.92,0.65,0.57,1))
            brow = ellipsoid(self.head, (x,0.34,1.36), (0.25,0.13,0.065), dark)
            brow.setR(-12 if x < 0 else 12)
        smile = LineSegs("smile")
        smile.setColor(*dark)
        smile.setThickness(3)
        for i in range(21):
            x = -0.42+0.84*i/20
            p = (x,1.245-0.18*(abs(x)/0.42)**2,0.43+0.11*(x/0.42)**2)
            (smile.moveTo if i==0 else smile.drawTo)(*p)
        self.head.attachNewNode(smile.create()).setLightOff()
        accessories = self.head.attachNewNode("accessories")
        for item in selected["accessories"]:
            if item == "glasses":
                ink = (0.22,0.19,0.27,1)
                for x in (-0.34,0.34):
                    torus(accessories,(x,0.695,1.05),0.28,0.035,ink)
                ellipsoid(accessories,(0,0.71,1.07),(0.10,0.035,0.035),ink)
            elif item == "cap":
                ellipsoid(accessories,(0,0.04,1.43),(0.57,0.48,0.26),(0.35,0.57,0.78,1))
                ellipsoid(accessories,(0,0.45,1.38),(0.60,0.43,0.055),(0.29,0.46,0.68,1),0.8)
                ellipsoid(accessories,(0,0.03,1.70),(0.06,0.06,0.045),(0.98,0.80,0.36,1))
            elif item == "crown":
                gold = (1,0.77,0.25,1)
                band = torus(accessories,(0,0.07,1.38),0.43,0.09,gold)
                band.setP(90)
                for x in (-0.35,0,0.35):
                    ellipsoid(accessories,(x,0.10,1.59),(0.09,0.12,0.26),gold,0.8)
                    ellipsoid(accessories,(x,0.10,1.84),(0.09,0.09,0.09),gold)
                ellipsoid(accessories,(0,0.43,1.48),(0.10,0.045,0.12),(0.90,0.38,0.48,1))
        self.head_shadow = shadow(self.root,0,0,0.73,0.72)

    def ensure_length(self, count):
        for i in range(len(self.segments), count-1):
            segment = self.body_root.attachNewNode("segment")
            ellipsoid(segment,(0,0,0.43),(0.455,0.49,0.42),self.color)
            light = tuple(min(1,v*0.7+0.25) for v in self.color[:3])+(1,)
            ellipsoid(segment,(0,0,0.24),(0.39,0.46,0.16),light)
            ellipsoid(segment,(0,0,0.827),(0.16,0.22,0.024),light)
            self.segments.append(segment)
            bridge = ellipsoid(self.body_root,(0,0,0.44),(0.40,0.5,0.38),self.color)
            self.bridges.append(bridge)
            self.shadows.append(shadow(self.body_root,0,0))

    def update(self, points, heading, dt=0.016, snap=False):
        self.ensure_length(len(points))
        self.heading = heading if snap else self.heading + ((heading-self.heading+180)%360-180)*min(1,dt*14)
        self.head.setPos(points[0][0],points[0][1],0)
        self.head.setH(self.heading)
        self.head_shadow.setPos(points[0][0],points[0][1],0.028)
        for i, node in enumerate(self.segments):
            visible = i+1 < len(points)
            node.show() if visible else node.hide()
            self.bridges[i].show() if visible else self.bridges[i].hide()
            self.shadows[i].show() if visible else self.shadows[i].hide()
            if not visible:
                continue
            x,y = points[i+1]
            px,py = points[i]
            node.setPos(x,y,0)
            node.setH(-degrees(atan2(px-x,py-y)))
            bridge = self.bridges[i]
            bridge.setPos((x+px)/2,(y+py)/2,0.43)
            bridge.setH(-degrees(atan2(px-x,py-y)))
            bridge.setScale(0.40,((px-x)**2+(py-y)**2)**0.5/2+0.18,0.37)
            self.shadows[i].setPos(x,y,0.028)

    def destroy(self):
        self.root.removeNode()
