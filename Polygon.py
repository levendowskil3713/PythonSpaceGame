import pygame
import random
import math
from phyTools import *
from Contact import *

#creates a polygon
class Polygon(Particle):
    def __init__(self, offsets=[], color = (0,0,0), normals_length = 0, width = 1, drawCenter = False, **kwargs):
        #store offsets
        self.offsets = []
        self.width = width
        self.drawCenter = drawCenter
        for o in offsets:
            self.offsets.append(Vec2(o))

        #compute normals
        self.normals = []
        for i in range(len(self.offsets)):
            normal = ~(self.offsets[i] - self.offsets[i - 1]).hat()
            self.normals.append(normal)

        self.color = color
        self.normals_length = normals_length
        super().__init__(**kwargs)

    def draw(self,screen):
        #draw polygon
        points = []
        for o  in self.offsets:
            points.append(self.world(o).int())
        pygame.draw.polygon(screen, self.color, points)

        #draw normals
        if self.normals_length > 0:
            for i in range(len(self.offsets)):
                start = self.world((self.offsets[i] + self.offsets[i - 1]) / 2)
                end = start + self.normals_length * self.rot.transform(self.normals[i])
                pygame.draw.line(screen, (0,0,0), start, end)

#creates a polygon with a uniform mass
class UniformPolygon(Polygon):
    def __init__(self, offsets=[], density=1, pos=Vec2(0,0), angle=0, **kwargs):
        mass = 0
        inertia = 0
        centroidNumerator = Vec2(0,0)
        self.offsets = []
        for o in offsets:
            self.offsets.append(Vec2(o))
        for i in range(len(self.offsets)):
            sa = self.offsets[i]
            sb = self.offsets[i - 1]
            triangleMass = density*0.5*(sa % sb)
            mass += triangleMass
            inertia += triangleMass/6*(sa@sa + sb@sb + sa@sb)
            triangleCentroid = 1/3*(sa + sb)
            centroidNumerator += triangleMass*triangleCentroid

        centroid = centroidNumerator / mass

        if mass < 0:
            mass *= -1
            inertia *= -1

        pos = Vec2(pos)
        pos += centroid.rotated(angle)
        inertia -= mass*centroid.mag2()

        for i in range(len(self.offsets)):
            self.offsets[i] -= centroid
        super().__init__(offsets=self.offsets, mass=mass, pos=pos, momi=inertia, rot=angle, **kwargs)
