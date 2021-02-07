import pygame
import random
import math
from phyTools import *
from Polygon import *

class Contact:
    def __init__(self, a, b, resolve=False, detect=None):
        # Check if detect has been specified already by user or subclass
        if detect is not None:
            self.detect = getattr(self, detect)
        else:
            # Otherwise find the correct overlap detection
            if isinstance(a, Circle) and isinstance(b, Circle):
                self.detect = self.circle_circle
            elif isinstance(a, Circle) and isinstance(b, Wall):
                self.detect = self.circle_wall
            elif isinstance(a, Wall) and isinstance(b, Circle):
                self.detect = self.circle_wall
                a, b = b, a 
            elif isinstance(a, Wall) and isinstance(b, Wall):
                self.detect = self.nothing
            elif isinstance(a, Polygon) and isinstance(b, Wall):
                self.detect = self.polygon_wall
            elif isinstance(a, Wall) and isinstance(b, Polygon):
                self.detect = self.polygon_wall
                a, b = b, a
            elif isinstance(a, Polygon) and isinstance(b, Polygon):
                self.detect = self.polygon_polygon
            elif isinstance(a, Circle) and isinstance(b, Polygon):
                self.detect = self.circle_polygon
            elif isinstance(a, Polygon) and isinstance(b, Circle):
                self.detect = self.circle_polygon
                a, b = b, a
            else:
                raise(ValueError, f"No overlap detection implemented between {type(a)} and {type(b)}.")
        
        # Store objects a and b
        self.a = a
        self.b = b
        
        # Calculate if contact occurs
        self.detect()

        # Resolve right now, or wait till later
        if resolve:
            self.resolve(renew=False)

    def __bool__(self):
        return self.overlap > 0

    def resolve(self, renew=True):
        if renew:
            self.detect()
        return bool(self)
            
    def nothing(self):
        self.overlap = -math.inf
        self.normal = Vec2(0,0)

    def circle_circle(self):
        self.normal = (self.b.pos - self.a.pos).hat()
        self.overlap = (self.a.radius + self.b.radius) - (self.a.pos - self.b.pos).mag()
        self.offset = self.a.rot.inverse_transform(self.normal) * self.a.radius

    def circle_wall(self):
        self.normal = -self.b.normal
        self.overlap = (self.a.pos - self.b.pos) @ -self.b.normal + self.a.radius + (0.5 * self.b.thickness)
        self.offset = self.a.rot.inverse_transform(self.normal) * self.a.radius

    def center_in_circle(self):
        self.normal = (self.b.pos - self.a.pos).hat()
        self.overlap = (self.a.radius) - (self.a.pos - self.b.pos).mag()

    def circle_in_circle(self):
        self.normal = (self.b.pos - self.a.pos).hat()
        self.overlap = (self.a.pos - self.b.pos).mag()

    def polygon_wall(self):
        poly = self.a
        wall = self.b
        max_overlap = -math.inf
        #checking each offset of the polygon
        for o in poly.offsets:
            point = poly.world(o)
            overlap = (wall.pos - point)@wall.normal + (wall.thickness/2)
            if (overlap > max_overlap):
                max_overlap = overlap
                max_offset = o
        self.overlap = max_overlap
        self.offset = max_offset
        self.normal = -wall.normal

    #only called in polygon_polygon
    def polyCollisionCheck(self, polyOne, polyTwo):
        penetrator = polyOne
        penetrated = polyTwo
        self.overlap = math.inf
        max_overlap = -math.inf
        #for each side of penetrated
        for i in range(len(penetrated.normals)):
            max_overlap = -math.inf
            #loop over the points on penetrator
            for o in penetrator.offsets:
                point = penetrator.world(o)
                penetratedNormal = penetrated.rot.transform(penetrated.normals[i])
                overlap = (penetrated.world(penetrated.offsets[i]) - point) @ penetratedNormal
                if (overlap > max_overlap):
                    max_overlap = overlap
                    max_offset = o
            if (max_overlap < self.overlap):
                self.overlap = max_overlap
                self.normal = -penetratedNormal
                self.offset = max_offset
                self.a = penetrator
                self.b = penetrated

    def polygon_polygon(self):
        self.polyCollisionCheck(self.a, self.b)
        if (self.overlap > 0):
            self.polyCollisionCheck(self.b, self.a)

    def circle_polygon(self):
        if isinstance(self.a, Circle):
            circle = self.a
            polygon = self.b
        else:
            circle = self.b
            polygon = self.a

        self.overlap = math.inf
        #looping over each side of the poylgon
        for i in range(len(polygon.normals)):
            #finding the current overlap with the circle
            polygonNormal = polygon.rot.transform(polygon.normals[i])
            sampledOverlap = (circle.pos - polygon.world(polygon.offsets[i])) @ -polygonNormal + circle.radius
            #setting the overlap equal to the sampled overlap, the offest equaled to the sampled offset, and the normal equal to the sampled normal if the sampled overlap is less than current overlap
            if(sampledOverlap < self.overlap):
                self.overlap = sampledOverlap
                self.normal = -polygonNormal
                self.offset = circle.body(circle.pos + circle.radius*self.normal)#polygon.offsets[i]
                self.a = circle
                self.b = polygon
        #checking polygon as penetrator if self.overlap is less than 0 or if self.overlap is less than or equal to the radius of the circle
        if(self.overlap > 0 or self.overlap <= circle.radius):
            nearestOffset = None
            nearestOffsetDistance = math.inf
            for i in range(len(polygon.normals)):
                #setting the nearest offset equal to the sampled offset if it is closer than the current nearest offset
                if(((polygon.world(polygon.offsets[i]) - circle.pos).mag() < nearestOffsetDistance)):
                   nearestOffset = polygon.offsets[i]
                   nearestOffsetDistance = (polygon.world(polygon.offsets[i]) - circle.pos).mag()
            #finds normal of the pseudo-wall
            wall_normal = ((polygon.world(nearestOffset) - circle.pos).hat())
            #finds position of the pseudo-wall
            wall_pos = (circle.radius * wall_normal) + circle.pos
            #max overlap with the pseudo-wall
            maxOverlap = -math.inf
            #offset of the max overlap
            maxOffset = None
            #finding the max overlap and offset
            for i in range(len(polygon.normals)):
                point = polygon.world(polygon.offsets[i])
                sampleOverlap = (wall_pos - point) @ wall_normal
                if(sampleOverlap > maxOverlap):
                    maxOverlap = sampleOverlap
                    maxOffset = polygon.offsets[i]
            #setting values if the sampled max overlap is less than the current min overlap
            if(maxOverlap < self.overlap):
                self.overlap = maxOverlap
                self.normal = -wall_normal
                self.offset = maxOffset
                self.a = polygon
                self.b = circle


class Push(Contact):
    def __init__(self, a, b, **kwargs):
        super().__init__(a, b, **kwargs)
    
    def resolve(self, renew=True):
        super().resolve(renew)
        return self.push()
    
    def push(self, fraction=1):
        if (self.overlap > 0):
            #mass
            try:
                m = (1/((1/self.a.mass) + (1/self.b.mass)))
            except:
                #ignore objects with infinate mass
                m = 0
            self.a.pos += -((self.overlap * m) / self.a.mass) * self.normal
            self.b.pos += ((self.overlap * m) / self.b.mass) * self.normal
            return 1
        else:
            return 0

class Bounce(Push):
    def __init__(self, a, b, restitution=1, muK = 0.3, muS = 0.5, **kwargs):
        self.restitution = restitution
        super().__init__(a, b, **kwargs)

        #static coefficient of friction
        self.muS = muS

        #kenetic coefficient of friction
        self.muK = muK
    
    def resolve(self, renew=True):
        super().resolve(renew)
        return self.bounce()
    
    def bounce(self):
        if (self.overlap > 0 and (self.a.vel - self.b.vel) @ self.normal > 0):
            #restitution
            e = self.restitution


            #tangential force


            #calculates the point of contact
            contactPoint = self.a.world(self.offset)

            #distances between offset and particles
            Sa = contactPoint - self.a.pos
            Sb = contactPoint - self.b.pos

            #Velocities of points a and b
            VaPrime = self.a.vel + ~(Sa * self.a.avel)
            VbPrime = self.b.vel + ~(Sb * self.b.avel)

            

            #relative velocity
            VPrime = VaPrime - VbPrime

            #moment of inertia for a and b
            Ia = self.a.momi
            Ib = self.b.momi

            #unit vector of the normal
            nHat = self.normal

            #mass
            m = 1 / ((1/self.a.mass) + (1/self.b.mass) + (((Sa % nHat)**2)/Ia) + (((Sb % nHat)**2)/Ib))

            #impulse
            Jn = ((1 + e) * (VPrime @ nHat)) * m
            Jt = self.muS*Jn
            J = Jn * nHat

            n = self.normal
            t = ~n

            San = Sa @ n
            Sat = Sa @ t
            Sbn = Sb @ n
            Sbt = Sb @ t

            # PROBLEM HERE
            #Mtt, Mnt and Mnn made
            Mtt = (1/self.a.mass) + (1/self.b.mass)+ (Sat**2/Ia) + (Sbt**2/Ib)
            Mnt = (San * Sat)/Ia +(Sbn*Sbt)/Ib
            Mnn = (1/self.a.mass) + (1/self.b.mass)+ ((San**2)/Ia) + ((Sbn**2)/Ib)

            #Qn and Qt
            Qn = Mtt -self.muS*Mnt
            Qt = (-Mnt + self.muS*Mnn)
            Vns = VPrime @ n - (Qn/Qt * (VPrime@ t))

            #if mu prime is used
            muPrime = max(-self.muS, Mnt/Mnn)
            QnPrime = Mtt - self.muS*Mnt
            QtPrime = (-Mnt + self.muS*Mnn)

            #deltaVn and deltaVt
            deltaVn = -Qn * Jn
            deltaVt = -Qt * Jn
            
            #red case
            if (Qt<= 0 or Vns <= -self.restitution*(VPrime@n)):
                Jn = (1+self.restitution)*(VPrime@n)/Qn
                Jt = self.muS*Jn
            #green case
            elif(Vns <= 0):
                #formulas from slide 11
                Jnc = (VPrime@n)/Qn
                Jnd1 = -Vns/Qn
                Jnd2 = ((VPrime@n) -Vns)/Qn

                #formula from slide 12
                
                Vnt = sqrt(QnPrime/Qn*((self.restitution**2*((VPrime@n)**2 - Vns**2) + Vns**2)))

                Jn = Jnc + Jnd1 + Jnd2
                Jt = self.muS*Jnc + self.muS*Jnd1 +muPrime*Jnd2
            
            #blue case
            elif (Vns >= 0):
                Jnc1 = (VPrime@n - Vns)/Qn
                Jnc2 = Vns/QnPrime

                '''ValueError: math domain error'''
                Vnf = -self.restitution * sqrt(abs((QnPrime/Qn*((VPrime@n)**2 - Vns**2)) + Vns**2))
                Jnd = -Vnf/QnPrime
               
                Jn = Jnc1+ Jnc2 + Jnd
                Jt = (self.muS*Jnc1) +(muPrime *Jnc2)+ (muPrime*Jnd)
            
            #applies the impulse
            Imp = Jn * n + Jt *t
            self.a.add_impulse(addedImpulse = -Imp, addedImpulsePos = contactPoint)
            self.b.add_impulse(addedImpulse = Imp, addedImpulsePos = contactPoint)

            #old mass
            #m = (1/((1/self.a.mass) + (1/self.b.mass)))

            #old impulse
            #J = ((1 + e) * m * (self.a.vel - self.b.vel) @ self.normal) * self.normal

            #old applies the impulse
            #self.a.add_impulse(-J)
            #self.b.add_impulse(J)

            return 1
        else:
            return 0
