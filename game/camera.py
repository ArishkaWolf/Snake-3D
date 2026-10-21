"""Слежение по экспоненциальному фильтру, независимому от частоты кадров."""
from math import sin, cos, radians, exp
from panda3d.core import Vec3
from config import CAMERA_HEIGHT, CAMERA_LOOK_AHEAD, CAMERA_SMOOTHING


class FollowCamera:
    def __init__(self,camera):
        self.camera=camera
        self.heading=0.0
        self.position=None
        self.target=None

    def update(self,head,heading,dt,distance,snap=False):
        amount=1-exp(-CAMERA_SMOOTHING*dt)
        self.heading=heading if snap else self.heading+((heading-self.heading+180)%360-180)*amount
        forward=Vec3(-sin(radians(self.heading)),cos(radians(self.heading)),0)
        head=Vec3(head[0],head[1],0.65)
        desired=head-forward*distance+Vec3(0,0,CAMERA_HEIGHT)
        look=head+forward*CAMERA_LOOK_AHEAD+Vec3(0,0,0.15)
        if self.position is None or snap:
            self.position,self.target=desired,look
        else:
            self.position+=(desired-self.position)*amount
            self.target+=(look-self.target)*amount
        self.camera.setPos(self.position)
        self.camera.lookAt(self.target)
