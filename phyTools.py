from math import sqrt, sin, cos
import math
import numbers
import random
import pygame

class Vec2:
    # constructor in two different ways:
    # Vec2(list) constructs a Vec2 from a list
    # Vec2(x, y) constructs a Vec2 from x and y coordinates
    def __init__(self, x=(0,0), y=None):
        if y is None:
            # hopefully x is a list of two elements
            try:
                if len(x) == 2:
                    self.x = x[0]
                    self.y = x[1]
                else:
                    raise ValueError("Incorrect single-argument instantiation for Vec2")
            except ValueError:
                raise ValueError("Incorrect single-argument instantiation for Vec2")
        else:
            self.x = x
            self.y = y
    
    # emulate a list of two elements
    # len(v) => 2
    def __len__(self):
        return 2
    # v[0] => v.x
    # v[1] => v.y
    def __getitem__(self, i):
        if i == 0:
            return self.x
        elif i == 1:
            return self.y
        else:
            raise IndexError("Index out of range.")

    # printed representation, returns a string
    def __repr__(self):
        return "Vec2(" + str(self.x) + ", " + str(self.y) + ")"

    # printed representation, returns a string
    def __str__(self):
        return "(" + str(self.x) + ", " + str(self.y) + ")"

    # equality ==
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    # Output as a Vec2 of integers, necessary for pygame graphics
    # v.int()
    def int(self):
        return Vec2(round(self.x), round(self.y))
 
    # addition +
    def __add__(self, other):
        return Vec2(self.x + other.x,
                    self.y + other.y)
    
    # subtraction -
    def __sub__(self, other):
        return Vec2(self.x - other.x,
                    self.y - other.y)
   # negation -
    def __neg__(self):
        return Vec2(-1*self.x, -1*self.y)
    

    # scalar multiplication *
    def __mul__(self, other):
        if isinstance(other, numbers.Real):
            return Vec2(self.x*other,
                        self.y*other)
        else:
            raise ValueError("Can only multiply Vec2 by scalar")
    def __rmul__(self, other):
        if isinstance(other, numbers.Real):
            return Vec2(self.x*other,
                        self.y*other)
        else:
            raise ValueError("Can only multiply Vec2 by scalar")
    
    # scalar division / 
    def __truediv__(self, scalar):
        inv = 1 / scalar
        return Vec2(self.x * inv,
                    self.y * inv)

   # dot product @
    def __matmul__(self, other):
        return self.x*other.x + self.y*other.y

    # cross product %
    # returns a scalar for 2D vectors
    def __mod__(self, other):
        return ~self @ other

    # return new Vec2 rotated 90 degrees
    # v.perp()
    def perp(self):
        return Vec2(-self.y, self.x)
    # do the same but overload the ~ operator
    # ~v
    __invert__ = perp
    
    # boolean context means True for nonzero and False for zero
    def __bool__(self):
        return self.x != 0 or self.y != 0

    # magnitude squared, avoids sqrt
    def mag2(self):
        return self.x*self.x + self.y*self.y

    # magnitude
    def mag(self):
        return sqrt(self.mag2())
    # overload abs() to return magnitude
    # abs(v) is the same as v.mag()
    __abs__ = mag

    # unit vector
    def hat(self):
        if self:
            return self / self.mag()
        else:
            return Vec2(0, 0)

    # return a copy
    def copy(self):
        return Vec2(self.x, self.y)

    # v.rotated(rot(radians))
    def rotated(self, rot):
        if isinstance(rot, numbers.Real):
            rot = Rotation(rot)
        return rot.transform(self)

# rotation class
class Rotation:
    def __init__(self, radians):
        self.rad = radians
        self.sin = sin(radians)
        self.cos = cos(radians)

    def rotate_by(self, change_in_angle):
        self.rad += change_in_angle
        self.sin = sin(self.rad)
        self.cos = cos(self.rad)

    def transform(self, v):
        return Vec2(v.x*self.cos - v.y*self.sin,
                    v.x*self.sin + v.y*self.cos)
    def inverse_transform(self, v):
        return Vec2( v.x*self.cos + v.y*self.sin,
                    -v.x*self.sin + v.y*self.cos)

class Particle:
    #initial variables
    mass = 4.3
    vel = Vec2(0,0)
    force = Vec2(0,0)
    pos = Vec2(0,0)

    #constructor
    def __init__(self, pos, mass, vel, rot = 0, avel = 0, momi = math.inf, tag = None):
        self.pos = pos
        self.mass = mass
        self.vel = vel
        self.rot = Rotation(rot)
        self.avel = avel
        self.momi = momi
        self.torque = 0
        self.tag = tag

    #clear the force
    def clear_force(self):
        self.force = Vec2(0,0)
        self.torque = 0

    #adds the force applied to the obj
    def add_force(self, addedForce, addedForcePos = None):
        self.force = addedForce + self.force
        if(addedForcePos != None):
            r = addedForcePos - self.pos
            self.torque += r % addedForce

    #adds an impulse to the particle
    def add_impulse(self, addedImpulse, addedImpulsePos = Vec2(0,0)):
        self.vel += addedImpulse/self.mass
        if(addedImpulsePos != Vec2(0,0)):
            r = addedImpulsePos - self.pos
            self.avel += r % (addedImpulse / self.momi)

    #adds a torque to the particle
    def add_torque(self, addedTorque):
        self.torque += addedTorque

    #updates the position of the projectile
    def update(self, dt):
        self.vel.x += (self.force.x/self.mass) * dt
        self.vel.y += (self.force.y/self.mass) * dt
        self.pos += self.vel * dt
        self.avel += (self.torque / self.momi) * dt
        self.rot.rotate_by(self.avel * dt)

    #world coordinates
    def world(self, body):
        return self.rot.transform(body) + self.pos

    #body coordinates
    def body(self, world):
        return self.rot.inverse_transform(world - self.pos)

class Circle(Particle):
    def __init__(self, radius=100, color = (255,255,255), width = 0, rotationPoint = False, **kwargs):
        self.color = color
        self.radius = radius
        self.width = width
        self.rotationPoint = rotationPoint
        super().__init__(**kwargs)

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.pos.int(), self.radius, self.width)
        if(self.rotationPoint == True):
            if(self.color != (0,0,0)):
                pointColor = (0,0,0)
            else:
                pointColor = (255,255,255)
            pygame.draw.circle(screen, pointColor, self.pos.int() + Vec2(int(self.rot.cos * (self.radius / 2)),int(self.rot.sin * (self.radius / 2))), int(self.radius / 8), 0)

class Wall(Particle):
    def __init__(self, pos = Vec2(0,0), pos2 = Vec2(0,0), color = (0,0,0), thickness = 15, **kwargs):
        super().__init__(pos = pos, **kwargs)
        self.pos2 = pos2
        self.color = color
        self.normal = ~(self.pos2 - self.pos).hat()
        self.thickness = thickness
    def draw(self,screen):
        pygame.draw.line(screen, self.color, self.pos, self.pos2, self.thickness)

class SingleForce():
    def __init__(self,particles = []):
        self.particles = particles
    def apply(self):
        for p in self.particles:
            p.add_force (self.force(p))
    def force (self,p):
        return Vec2(0,0)

class PairForce():
    def __init__(self,particles = []):
        self.particles = particles
    def apply(self):
        for i in range(len(self.particles)):
            for j in range (i):
                force = self.force(self.particles[i],self.particles[j])
                self.particles[i].add_force(force)
                self.particles[j].add_force(-force)
    def force(self,a,b):
        return Vec2(0,0)

class Bond():
    def __init__(self, pairs=[]):
        self.pairs = pairs
        self.firstRemovedPairIndex = None

    def apply(self):
        for p in self.pairs:
            if(self.firstRemovedPairIndex == None or self.firstRemovedPairIndex > self.pairs.index(p)):
                force = self.force(p[0], p[1])
                p[0].add_force(force)
                p[1].add_force(-1*force)

   
                
    def force(self, a, b):
        return Vec2(0,0)

    #removes all bonds related to a specified particle
    #treat the p parameter as an element of a pair within the pairs list
    def remove_particle(self, p):
        for i in self.pairs:
            if i[0] == p:
                self.firstRemovedPairIndex = self.pairs.index(i)
                self.pairs.pop(self.pairs.index(i))

    #deletes a bond between two particles
    #treat the bond parameter as an element of pairs
    def remove_bond(self, pairs, bond, particle):
        for i in self.pairs:
            if i[0] == pairs[0] or i[1] == pairs[1]:
                self.pairs.pop(i)

class Spring(Bond):
    #set to true after the resting length of the spring is aquired
    def __init__(self, k=0, b=0, **kwargs):
        self.b = b
        self.k = k
        super().__init__(**kwargs)

    def force(self,a,b):
        s = (a.pos-b.pos)
        natLength = a.radius + b.radius + 30
        force = -self.k*(s.mag() - natLength) - self.b*((s.hat()) @ ((a.vel - b.vel)))
        return force*s.hat()

class Gravitation(PairForce):
    def __init__(self,G,**kwargs):
        self.G = G
        super().__init__(**kwargs)
    def force(self,a,b):
        gForce = ((self.G * a.mass * b.mass) / (math.sqrt((a.pos.x - b.pos.x)**2 + (a.pos.y + b.pos.y)**2))**2) * (Vec2((a.pos.x - b.pos.x), (a.pos.y - b.pos.y))/(math.sqrt((a.pos.x + b.pos.x)**2 + (a.pos.y + b.pos.y)**2)))
        return -gForce

class Gravity(SingleForce):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
    def force(self,a):
        return (Vec2(0,a.mass*1000))
 
class Repulsion(PairForce):
    def __init__(self,k,**kwargs):
        self.k = k
        super().__init__(**kwargs)

    def force(self,a,b):
        #resting position of the spring force
        s0 = a.radius + b.radius
        #current distance between the two ends of the force
        s = (a.pos - b.pos).mag()
        #value that is returned by the function
        returnVal = Vec2(0,0)
        #if the circles are touching
        if(math.sqrt((a.pos.x - b.pos.x)**2 + (a.pos.y - b.pos.y)**2) < (a.radius + b.radius)):
            #calculate total force applied
            repForce = -self.k * (s - s0)
            #calculating the angle between the two circles and checking for /0
            if((b.pos.x - a.pos.x) != 0):
                angle = math.atan((b.pos.y - a.pos.y) / (b.pos.x - a.pos.x))
            else:
                angle = 0
            #setting the calculated vector value as the return value
            returnVal = Vec2(repForce * sin(angle), repForce * cos(angle))
            #sets the return value equal to its current opposite if the second circle is above the first circle
            if((a.pos.x > b.pos.x and a.pos.y < b.pos.y) or (a.pos.x < b.pos.x and a.pos.y < b.pos.y)):
                returnVal = -returnVal
        return returnVal

class Wind(SingleForce):
    def __init__(self, c, w, **kwargs):
        #drag force strength (random value)
        self.c = c
        #velocity of the wind (set with other function)
        self.w = w
        super().__init__(**kwargs)
    def force (self,p):
        if(self.w != Vec2(0,0) and p.vel != Vec2(0,0)):
            return ((-self.c * p.radius) * ((p.vel - self.w).mag())**2 * ((p.vel - self.w)/sqrt((p.vel.x - self.w.x)**2 + (p.vel.y - self.w.y)**2)))
        else:
            return Vec2(0,0)

class BubbleForce(PairForce):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
    def force(self,a,b):
        s = 200
        e = s * a.radius + b.radius
        o = a.radius + b.radius
        r = a.pos - b.pos
        return e * ((o / r.mag())**2 - 1) * (o / r.mag())**2 * r.hat()

class Drag(SingleForce):
    def __init__(self,**kwargs):
        super().__init__(**kwargs)
    def force (self,p):
        C = 100
        return -C * p.radius * p.vel

class Friction(SingleForce):
    def __init__(self, u, **kwargs):
        self.u = u
        super().__init__(**kwargs)
    def force (self,p):
        N = p.mass * 1000
        force = N*self.u
        if(p.vel.mag() < force):
            p.vel = Vec2(0,0)
            return Vec2(0,0)
        else:
            return Vec2(p.vel.hat().x * -force, p.vel.hat().y * -force)

class Blow(SingleForce):
    def __init__(self, mousePos, **kwargs):
        self.mousePos = mousePos
        super().__init__(**kwargs)
    def force (self,p):
        b = 1**4
        r = p.pos - Vec2(self.mousePos.x, self.mousePos.y)
        return (2 * math.pi * b * p.radius**2 * p.pos) / (p.pos.mag())**2