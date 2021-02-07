import pygame
import random
import math
import os
from phyTools import *
from Contact import *
from Polygon import *

#initializes pygame
pygame.init()

#creates a window
screen = pygame.display.set_mode((1920, 1080), pygame.FULLSCREEN)
os.chdir(os.path.dirname(__file__))

#sets up the clock
clock = pygame.time.Clock()
fps = 60
dt = 1/fps
#list of objects that can interact with one another
objects = []
#list of objects that cannot interact with anything
effects = []
#time between enemy one shots
shotTime = 60
#set to true when the player is firing weapons
playerFiring = False
#set to true when the player dies
gameOver = False
#time between enemy spawns
spawnTimer = 360
#time since the last enemy was spawned
spawnTime = spawnTimer
#max player health
playerMaxHealth = 20
#current score
score = 0
#intensity of fade window
alpha = 0
#radius for enemy one hitbox
enemyOneRadius = 70
#image for basic enemy ship
enemyOneImage = pygame.transform.scale(pygame.image.load('Saucer.png'), (int(enemyOneRadius*2.55), int(enemyOneRadius*2.55)))
enemyOneImageRotation = 0
#image for player ship
playerImage = pygame.transform.scale(pygame.image.load('Fighter.png'), (int(100), int(100)))
#image for enemy ship explosion
enemyShipExplosion = pygame.image.load('ShipExplosion.png')
#image for player ship explosion
playerShipExplosion = pygame.image.load('ShipExplosion2.png')
#title screen image
titleImage = pygame.image.load('Logo.png')
#determines current game mode (start menu = 1, main game = 2)
gameMode = 0

#creates the hitbox for the player's ship
def createPlayerShip():
    global playerImage
    #location of the mouse
    mousePos = Vec2(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1])
    #density of the ship
    shapeDensity = 1000000
    player = ((UniformPolygon(offsets = reversed([(playerImage.get_width()/2,-playerImage.get_height()/4), (playerImage.get_width()/2,playerImage.get_height()/4), 
                                                  (0,playerImage.get_height()/2), (-playerImage.get_width()/2,playerImage.get_height()/4), 
                                                  (-playerImage.get_width()/2,-playerImage.get_height()/4), (0,-playerImage.get_height()/2)]), 
                              color = (0,0,0), 
                              pos = Vec2(pygame.display.get_surface().get_width()/2,pygame.display.get_surface().get_height()/2), 
                              density = shapeDensity,
                              vel = Vec2(0,0),
                              tag = "Player",
                              width = 0)))
    createSkillCooldowns(player)
    setObjectHealth(player)
    objects.append(player)

    #creates engine effect for the player's ship
    shapeDensity = 500
    circleRadius = 10
    circleMass = shapeDensity / circleRadius
    effects.append(Circle(radius = circleRadius, 
                        color = (255, 50, 0), 
                        width = 0,
                        pos = Vec2(-100,-100), 
                        vel = Vec2(0, 0),
                        tag = "EngineOne",
                        momi = (1/2) * circleMass * circleRadius**2,
                        mass = circleMass))
    effects.append(Circle(radius = circleRadius, 
                        color = (255, 50, 0), 
                        width = 0,
                        pos = Vec2(-100,-100), 
                        vel = Vec2(0, 0),
                        tag = "EngineTwo",
                        momi = (1/2) * circleMass * circleRadius**2,
                        mass = circleMass))

#moves the player's ship to the location of the mouse and makes the ship face the mouse
def movePlayerShip():
    #location of the mouse
    mousePos = Vec2(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1])
    #max velocity of the ship
    maxVel = 300
    #max angular velocity of the ship
    maxAvel = 3
    for obj in objects:
        #distance from the ship's center to the mouse
        distance = mousePos - obj.pos
        if(obj.tag == "Player"):
            #offset that acts as the front of the ship
            frontOffset = obj.offsets[0]
            #front of the ship in world coordinates
            front = obj.world(frontOffset)
            #moves the ship to the mouse
            obj.vel = distance
            #prevents the ship from moving if the mouse is very close to the center of the ship
            if(distance.mag() > frontOffset.mag()/4):
                #applying velocity to the ship
                if(obj.vel.mag() >= maxVel):
                    obj.vel = distance.hat() * maxVel

                #transforming the front offset in world coordinates
                rotatedFront = Vec2((math.cos(-obj.rot.rad) * (front.x - obj.pos.x) - math.sin(-obj.rot.rad) * (front.y - obj.pos.y) + obj.pos.x), 
                                 (math.sin(-obj.rot.rad) * (front.x - obj.pos.x) + math.cos(-obj.rot.rad) * (front.y - obj.pos.y) + obj.pos.y))
                #rotating the position of the mouse about the center of the ship in world coordinates to match the rotation of rotatedFront
                rotatedMousePos = Vec2((math.cos(-obj.rot.rad) * (mousePos.x - obj.pos.x) - math.sin(-obj.rot.rad) * (mousePos.y - obj.pos.y) + obj.pos.x), 
                                 (math.sin(-obj.rot.rad) * (mousePos.x - obj.pos.x) + math.cos(-obj.rot.rad) * (mousePos.y - obj.pos.y) + obj.pos.y))

                #the angle between the ship's center and the mouse's location
                angle = math.atan(distance.x/distance.y)
                #the angle between the ship's center and the mouse's location using atan2
                angle2 = math.atan2(distance.x,-distance.y)
                #the angle that the ship is facing (didn't use obj.rot.rad because it has no upper or lower bounds)
                angle3 = math.atan2((front.x - obj.pos.x),-(front.y - obj.pos.y))
                #calculates the magnitude of angular velocity applied to the ship using two equations
                appliedAvel = 3 * abs(((obj.rot.sin)/(obj.rot.cos)) - math.tan(-angle))
                appliedAvelSecondary = 6 * abs(angle2 - angle3)
                #taking the smallest result between the two equations to prevent the ship from shaking while facing certain directions
                if(abs(appliedAvel) > abs(appliedAvelSecondary) and abs(angle2 - angle3) < math.pi):
                    appliedAvel = appliedAvelSecondary
                #capping the angular velocity
                if(appliedAvel > maxAvel):
                    appliedAvel = maxAvel
                #applying the angular velocity
                if((rotatedMousePos.x - rotatedFront.x) > 0):
                    obj.avel = appliedAvel
                else:
                    obj.avel = -appliedAvel
            else:
                obj.vel = Vec2(0,0)
                obj.avel = 0

#places the engine effects and changes the size of the engine effects proportional to the velocity and angular velocity of the player ship
def changeEngineEffects():
    for obj in objects:
        if obj.tag == "Player":
            for efs in effects:
                #back offset of player ship in world coordinates
                back = obj.world(obj.offsets[3])
                #direction facing back
                direction = (back - obj.pos).hat()
                #changes engine effects
                for efs in effects:
                    if(efs.tag == "EngineOne"):
                        #location of the engine effect
                        firePoint = Vec2(back.x + (playerImage.get_width()*obj.rot.cos)/6,back.y + (playerImage.get_width()*obj.rot.sin)/6)
                        efs.radius = int(((obj.vel).mag() - (obj.avel*20))/50)
                        if(efs.radius > 6):
                            efs.radius = 6
                        if(efs.radius < 0):
                            efs.radius = 0
                        efs.pos = firePoint
                    elif(efs.tag == "EngineTwo"):
                        #location of the engine effect
                        firePoint = Vec2(back.x - (playerImage.get_width()*obj.rot.cos)/6,back.y - (playerImage.get_width()*obj.rot.sin)/6)
                        efs.radius = int(((obj.vel).mag() + (obj.avel*20))/50)
                        if(efs.radius > 6):
                            efs.radius = 6
                        if(efs.radius < 0):
                            efs.radius = 0
                        efs.pos = firePoint
        

#allows the player to fire weapons
def playerFire():
    global playerFiring
    for obj in objects:
        if(obj.tag == "Player"):
            #location of the mouse
            mousePos = Vec2(pygame.mouse.get_pos()[0],pygame.mouse.get_pos()[1])
            shapeDensity = 10
            circleRadius = 6
            circleMass = shapeDensity / circleRadius
            #speed of the projectile
            projectileSpeed = 1000
            #front offset of player ship in world coordinates
            front = obj.world(obj.offsets[0])
            #direction that the projectile will be fired
            direction = (front - obj.pos).hat()
            #initial location of the first projectile
            firePoint = obj.world(obj.offsets[1]) + direction*(circleRadius*2) + Vec2(-direction.y,direction.x)*5
            if(playerFiring == True and obj.cooldowns[0] <= obj.cooldowns[1]):
                projectile = (Circle(radius = circleRadius, 
                                color = (0, 185, 255), 
                                width = 0,
                                pos = firePoint, 
                                vel = projectileSpeed * direction,
                                tag = "PlayerProjectile",
                                momi = (1/2) * circleMass * circleRadius**2,
                                mass = circleMass))
                setObjectHealth(projectile)
                objects.append(projectile)
            #initial location of the second projectile
            firePoint = obj.world(obj.offsets[5]) + direction*(circleRadius*2) - Vec2(-direction.y,direction.x)*5
            if(playerFiring == True and obj.cooldowns[0] <= obj.cooldowns[1]):
                projectile2 = (Circle(radius = circleRadius, 
                                color = (0, 185, 255), 
                                width = 0,
                                pos = firePoint, 
                                vel = projectileSpeed * direction,
                                tag = "PlayerProjectile",
                                momi = (1/2) * circleMass * circleRadius**2,
                                mass = circleMass))
                setObjectHealth(projectile2)
                objects.append(projectile2)
                obj.cooldowns[1] = 0
            obj.cooldowns[1] += 1
    

#allows enemy ships to fire weapons
def enemyFire():
    for obj in objects:
        if(obj.tag == "Enemy" and isinstance(obj, Circle)):
            if(obj.cooldowns[0] <= obj.cooldowns[1]):
                shapeDensity = 10
                circleRadius = 12
                circleMass = shapeDensity / circleRadius
                #speed of the projectile
                projectileSpeed = 400
                #direction that the projectile will be fired
                direction = (getPlayerLocation() - obj.pos).hat()
                #location of the projectile upon creation
                firePoint = obj.pos + ((obj.radius + circleRadius + 1) * direction)
                projectile = (Circle(radius = circleRadius, 
                               color = (0, 255, 0), 
                               width = 0,
                               pos = firePoint, 
                               vel = projectileSpeed * direction,
                               tag = "EnemyProjectile",
                               momi = (1/2) * circleMass * circleRadius**2,
                               mass = circleMass))
                setObjectHealth(projectile)
                objects.append(projectile)
                obj.cooldowns[1] = 0
            else:
                obj.cooldowns[1] += 1

#adds a number to an object's health
def changeObjectHealth(num, object):
    object.health += num

#creates an enemy ship
def createEnemyOne(pos):
    shapeDensity = 500
    circleRadius = enemyOneRadius
    circleMass = shapeDensity / circleRadius
    enemy = (Circle(radius = circleRadius, 
                        color = (0, 0, 0), 
                        width = 0,
                        pos = pos, 
                        vel = Vec2(0, 0),
                        tag = "Enemy",
                        momi = (1/2) * circleMass * circleRadius**2,
                        mass = circleMass))
    createSkillCooldowns(enemy)
    setObjectHealth(enemy)
    objects.append(enemy)
 
#creates cooldowns for all skills and weapons for the specified object
def createSkillCooldowns(object):
    if(object.tag == "Enemy"):
        #time between shots
        shotCooldown = 90
        #time since last shot fired
        currentShotCooldown = 0
        object.cooldowns = [shotCooldown, currentShotCooldown]
    elif(object.tag == "Player"):
        #time between shots
        shotCooldown = 12
        #time since last shot fired
        currentShotCooldown = 0
        object.cooldowns = [shotCooldown, currentShotCooldown]

#sets the max health for an object
def setObjectHealth(object):
    if(object.tag == "Enemy"):
        object.health = 8
    elif(object.tag == "Player"):
        object.health = playerMaxHealth
    elif(object.tag == "PlayerProjectile"):
        object.health = 1
    elif(object.tag == "EnemyProjectile"):
        object.health = 1

#returns the location of the player's ship
def getPlayerLocation():
    for obj in objects:
        if(obj.tag == "Player"):
            return obj.pos
    return Vec2(-500,-500)

#returns the health of the player
def getPlayerHealth():
    for obj in objects:
        if(obj.tag == "Player"):
            return obj.health
    return 0


#moves enemy ships to the player
def moveEnemy():
    #total velocity of the enemy
    maxVelocity = 100
    #minimum distance maintained with player ship
    minDistance = 200
    #minimum distance maintained with other enemy ships
    minDistanceEnemy = 200
    #distance is divided by this number
    directionNum = 0
    for obj in objects:
        #distance between the enemy and the player
        distance = (getPlayerLocation() - obj.pos).mag()
        #direction of movement
        direction = Vec2(0,0)

        #moves ships away from other enemy ships
        for obj2 in objects:
            if(obj2.tag == "Enemy" and obj2 != obj and (obj2.pos - obj.pos).mag() < minDistanceEnemy):
                direction += -(obj2.pos - obj.pos).hat()
                directionNum += 1

        #moves ships towards the player
        if((obj.tag == "Enemy") and distance > minDistance):
            direction += (getPlayerLocation() - obj.pos).hat()
            directionNum += 1
            
        #applies the velocity
        if((obj.tag == "Enemy") and directionNum <= 0):
            obj.vel = Vec2(0,0)
        elif((obj.tag == "Enemy") and directionNum > 0):
            direction = direction / directionNum
            obj.vel = direction * (distance/8)
        if((obj.tag == "Enemy") and (obj.vel).mag() > maxVelocity):
            obj.vel = direction * maxVelocity

#removes unneeded and destroyed objects
def clean():
    global gameOver
    global score
    global enemyShipExplosion
    try:
        for obj in objects:
            #removes projectiles that are off the screen
            if((obj.tag == "PlayerProjectile" or obj.tag == "EnemyProjectile") and 
               (obj.pos.x < -50 or obj.pos.x > (pygame.display.get_surface().get_width() + 50) or 
                obj.pos.y < -50 or obj.pos.y > (pygame.display.get_surface().get_height() + 50))):
               objects.pop(objects.index(obj))
            #removes objects with no health
            if(obj.health <= 0):
                if(obj.tag == "Player"):
                    #creates explosion hitbox
                    shapeDensity = 500
                    circleRadius = 1000
                    circleMass = shapeDensity / circleRadius
                    effects.append(Circle(radius = circleRadius, 
                                          color = (0, 0, 0), 
                                          width = 0,
                                          pos = obj.pos, 
                                          vel = Vec2(0, 0),
                                          tag = "ExplosionPlayer",
                                          momi = (1/2) * circleMass * circleRadius**2,
                                          mass = circleMass))
                    gameOver = True
                if(obj.tag == "Enemy"):
                    score += 1
                    #creates explosion hitbox
                    shapeDensity = 500
                    circleRadius = int(obj.radius*6)
                    circleMass = shapeDensity / circleRadius
                    effects.append(Circle(radius = circleRadius, 
                                          color = (0, 0, 0), 
                                          width = 0,
                                          pos = obj.pos, 
                                          vel = Vec2(0, 0),
                                          tag = "Explosion",
                                          momi = (1/2) * circleMass * circleRadius**2,
                                          mass = circleMass))
                objects.pop(objects.index(obj))
    except:
        print("Error: object could not be removed from list")

#reduces the sise of explosion effects
def shrinkExplosion():
    for efs in effects:
        if(efs.tag == "Explosion"):
            efs.radius = int(efs.radius * 0.875)
            if(efs.radius < 80):
                effects.pop(effects.index(efs))
        if(efs.tag == "ExplosionPlayer"):
            efs.radius = int(efs.radius * 0.95)
            if(efs.radius < 80):
                effects.pop(effects.index(efs))

#spawns enemies at a gradually increasing rate
def spawnEnemies():
    global spawnTimer
    global spawnTime
    #time subtracted from the spawn timer each time an enemy is spawned
    spawnRateIncrease = 10
    #capping number of enemies
    enemyNum = 0
    enemyCap = 4
    for obj in objects:
        if(obj.tag == "Enemy"):
            enemyNum += 1
    if(spawnTime >= spawnTimer and enemyNum < enemyCap):
        #determines what side of the screen the enemy will spawn on
        screenSide = random.randrange(1,4,1)
        if(screenSide == 1):
            xLocation = -100
            yLocation = random.randrange(0,pygame.display.get_surface().get_height())
        elif(screenSide == 2):
            xLocation = pygame.display.get_surface().get_width() + 100
            yLocation = random.randrange(0,pygame.display.get_surface().get_height())
        elif(screenSide == 3):
            xLocation = random.randrange(0,pygame.display.get_surface().get_width())
            yLocation = -100
        else:
            xLocation = random.randrange(0,pygame.display.get_surface().get_width())
            yLocation = pygame.display.get_surface().get_height() + 100
        createEnemyOne(Vec2(xLocation,yLocation))
        spawnTime = 0
        if(spawnTimer > 120):
            spawnTimer -= spawnRateIncrease
        if(spawnTimer < 120):
            spawnTimer = 120
    spawnTime += 1

#creates the user interface
def createUI():
    #health bar
    HBXLocation = pygame.display.get_surface().get_width()/100
    HBYLocation = pygame.display.get_surface().get_height()/100
    HBWidth = 30
    pygame.draw.rect(screen, (255,255,255), [HBXLocation,HBYLocation,pygame.display.get_surface().get_width()/4,HBWidth])
    if(getPlayerHealth() > 0):
        pygame.draw.rect(screen, (255,0,0), [HBXLocation,HBYLocation,(getPlayerHealth()*(pygame.display.get_surface().get_width()/playerMaxHealth))/4,HBWidth])

    #score display
    font = pygame.font.Font('freesansbold.ttf', 30)
    text = font.render("Score: " + str(score), True, (255,255,255))
    textRect = text.get_rect()
    textRect.left = HBXLocation
    textRect.top = HBYLocation*2 + HBWidth
    screen.blit(text,textRect)

#displays game logo
def createLogo(surface):
    titleImageCopy = titleImage
    rect = titleImageCopy.get_rect()
    rect.center = (pygame.display.get_surface().get_width()/2,pygame.display.get_surface().get_height()/2)
    surface.blit(titleImageCopy,rect)
    font = pygame.font.Font('freesansbold.ttf', 40)
    text = font.render("Click to Start or Press Escape to Quit", True, (225,225,225))
    textRect = text.get_rect()
    textRect.center = (pygame.display.get_surface().get_width()/2,pygame.display.get_surface().get_height()/1.075)
    screen.blit(text,textRect)

#applies images to ships
def applyShipImages(surface):
    global enemyOneImage
    global enemyOneImageRotation
    global playerImage
    for obj in objects:
        if(obj.tag == "Enemy" and enemyOneImage != None):
            enemyOneImageCopy = pygame.transform.rotate(enemyOneImage,enemyOneImageRotation).copy()
            surface.blit(enemyOneImageCopy,(int(obj.pos.x - enemyOneImageCopy.get_width()/2),int(obj.pos.y - enemyOneImageCopy.get_height()/2)))
        if(obj.tag == "Player" and playerImage != None):
            playerImageCopy = pygame.transform.rotate(playerImage,-(obj.rot.rad * (180/math.pi))).copy()
            surface.blit(playerImageCopy,(int(obj.pos.x - playerImageCopy.get_width()/2),int(obj.pos.y - (playerImageCopy.get_height())/2)))
    enemyOneImageRotation += 1.5

#applies images to effects
def applyEffectImages(surface):
    global enemyShipExplosion
    global playerShipExplosion
    for efs in effects:
        if(efs.tag == "Explosion" and enemyShipExplosion != None):
            enemyShipExplosionCopy = pygame.transform.scale(enemyShipExplosion, (efs.radius,efs.radius))
            rect = enemyShipExplosionCopy.get_rect()
            rect.center = efs.pos
            surface.blit(enemyShipExplosionCopy,rect)
        if(efs.tag == "ExplosionPlayer" and playerShipExplosion != None):
            playerShipExplosionCopy = pygame.transform.scale(playerShipExplosion, (efs.radius,efs.radius))
            rect = playerShipExplosionCopy.get_rect()
            rect.center = efs.pos
            surface.blit(playerShipExplosionCopy,rect)

#creates game over text
def createGameOverText(surface):
    font = pygame.font.Font('freesansbold.ttf', 130)
    text = font.render("GAME OVER", True, (225,0,0))
    textRect = text.get_rect()
    textRect.center = (pygame.display.get_surface().get_width()/2,pygame.display.get_surface().get_height()/2.2)
    screen.blit(text,textRect)
    font = pygame.font.Font('freesansbold.ttf', 70)
    text = font.render("SCORE: " + str(score), True, (255,255,255))
    textRect = text.get_rect()
    textRect.center = (pygame.display.get_surface().get_width()/2,pygame.display.get_surface().get_height()/1.8)
    screen.blit(text,textRect)
    font = pygame.font.Font('freesansbold.ttf', 40)
    text = font.render("Press Space to Return to Main Menu or Press Escape to Quit", True, (225,225,225))
    textRect = text.get_rect()
    textRect.center = (pygame.display.get_surface().get_width()/2,pygame.display.get_surface().get_height()/1.075)
    screen.blit(text,textRect)

#creates an un-fading black rectangle
def reverseFadeWindow(surface):
    global alpha
    transparentSurface = pygame.Surface((pygame.display.get_surface().get_width(),pygame.display.get_surface().get_height()))
    transparentSurface.set_alpha(alpha)
    transparentSurface.fill((0,0,0))
    surface.blit(transparentSurface, (0,0))
    alpha += 1.5

#creates a fading black rectangle
def fadeWindow(surface):
    global alpha
    transparentSurface = pygame.Surface((pygame.display.get_surface().get_width(),pygame.display.get_surface().get_height()))
    transparentSurface.set_alpha(alpha)
    transparentSurface.fill((0,0,0))
    surface.blit(transparentSurface, (0,0))
    alpha -= 1.5

#applies an attractive force to enemy projectiles proportional to the distance between the projectile and the player's ship
def enemyProjectileSeekingForce():
    #max projectile velocity
    maxVel = 500
    for obj in objects:
        if(obj.tag == "EnemyProjectile"):
            #magnitude of the force
            forceMag = 120000/(getPlayerLocation() - obj.pos).mag()
            #direction of the force
            forceDec = (getPlayerLocation() - obj.pos).hat()
            #applies the force
            obj.add_force(forceMag * forceDec)
            if((obj.vel).mag() > maxVel):
                obj.vel = obj.vel.hat() * maxVel

#runs the start menu
def runStart():
    global gameMode
    global gameOver
    gameOver = False
    t = 0
    running = True
    #set to true after mouse click
    fading = False
    while running:
        global playerFiring
        global alpha

        #colors the background
        screen.fill((0,0,0))

        if(alpha < 255):
            createLogo(screen)

        if(fading == True):
            if(alpha >= 255):
                gameMode = 2
                running = False
            else:
                reverseFadeWindow(screen)

        #draws all objects
        for obj in objects:
            if(obj.tag != "Player" and obj.tag != "Enemy" and obj.tag != "PlayerProjectile" and obj.tag != "EnemyProjectile"):
                obj.draw(screen)

        #flips the display
        pygame.display.update()

        #limits the frame rate
        clock.tick(fps)

        if(playerFiring == True):
            fading = True

        #event loop
        for event in pygame.event.get():
            if event.type == pygame.MOUSEBUTTONDOWN:
                if(event.button == 1):
                    playerFiring = True
            if event.type == pygame.MOUSEBUTTONUP:
                if(event.button == 1):
                    playerFiring = False
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
            if(event.type == pygame.KEYDOWN):
                pressed = pygame.key.get_pressed()
                if(pressed[pygame.K_ESCAPE]):
                    running = False
                    pygame.quit()

#runs the game
def runMainGame():
    t = 0
    running = True
    global alpha
    global gameMode
    #set to after the fading stops
    fading = True
    while running:

        #colors the background
        screen.fill((0,0,0))

        if(gameOver == False and fading == False):
            spawnEnemies()

        #clears forces acting upon all objects
        for obj in objects:
            obj.clear_force()

        enemyProjectileSeekingForce()
    
        #updates velocity and position
        t += dt
        for obj in objects:
            obj.update(dt)
    
        if(gameOver == False and fading == False):
            movePlayerShip()
            enemyFire()
            playerFire()
        moveEnemy()
        changeEngineEffects()
        shrinkExplosion()
        clean()

        #resolves collisions for objects
        for j in range(1, len(objects)):
            for i in range(j):
                executeCollision = False
                #collisions between ships and allied projectiles are ignored
                if((((objects[i].tag == "Enemy" or objects[i].tag == "EnemyProjectile") and 
                    (objects[j].tag == "Enemy" or objects[j].tag == "EnemyProjectile")) == False and
                    ((objects[i].tag == "Player" or objects[i].tag == "PlayerProjectile") and 
                    (objects[j].tag == "Player" or objects[j].tag == "PlayerProjectile")) == False
                     or (objects[i].tag == "Enemy" and objects[j].tag == "Enemy"))):
                    #prevents unnecessary collisions from resolving to improve performance
                    if(isinstance(objects[i],Circle) and isinstance(objects[j],Circle)):
                        if((objects[i].radius + objects[j].radius) >= (objects[i].pos - objects[j].pos).mag()):
                            executeCollision = True
                    elif(isinstance(objects[i],Circle) and objects[j].tag == "Player"):
                        pseudoRadius = -1
                        for l in range(len(objects[j].normals)):
                            if(objects[j].offsets[l].mag() > pseudoRadius):
                                pseudoRadius = objects[j].offsets[l].mag()
                        if((objects[i].pos - objects[j].pos).mag() <= (pseudoRadius + objects[i].radius)):
                            executeCollision = True
                    elif(isinstance(objects[j],Circle) and objects[i].tag == "Player"):
                        pseudoRadius = -1
                        for l in range(len(objects[i].normals)):
                            if(objects[i].offsets[l].mag() > pseudoRadius):
                                pseudoRadius = objects[i].offsets[l].mag()
                        if((objects[i].pos - objects[j].pos).mag() <= (pseudoRadius + objects[j].radius)):
                            executeCollision = True
                    else:
                        executeCollision = True
                if(executeCollision == True):
                    c = Bounce(objects[i], objects[j],0.7)
                    if (c):
                        #deals damage to objects involving projectiles (only enemy projectiles harm the player and vice versa)
                            if(c.overlap >= 0 and (((objects[i].tag == "EnemyProjectile" or objects[j].tag == "EnemyProjectile") 
                                and (objects[i].tag == "Player" or objects[j].tag == "Player")) or ((objects[i].tag == "PlayerProjectile" 
                                or objects[j].tag == "PlayerProjectile") and (objects[i].tag == "Enemy" or objects[j].tag == "Enemy"))
                                or ((objects[i].tag == "PlayerProjectile" or objects[i].tag == "EnemyProjectile") and (objects[j].tag 
                                == "PlayerProjectile" or objects[j].tag == "EnemyProjectile")))):
                                changeObjectHealth(-1, objects[i])
                                changeObjectHealth(-1, objects[j])
                            elif(c.overlap >= 0 and (objects[i].tag == "PlayerProjectile" or objects[i].tag == "EnemyProjectile")):
                                changeObjectHealth(-1, objects[i])
                            elif(c.overlap >= 0 and (objects[j].tag == "PlayerProjectile" or objects[j].tag == "EnemyProjectile")):
                                changeObjectHealth(-1, objects[j])
                            c.resolve()

        #draws all objects, effects, and images
        for obj in objects:
            if(obj.tag != "EnemyProjectile" and obj.tag != "PlayerProjectile"):
                obj.draw(screen)
        for efs in effects:
            efs.draw(screen)
        applyShipImages(screen)
        applyEffectImages(screen)
        for obj in objects:
            if(obj.tag == "EnemyProjectile" or obj.tag == "PlayerProjectile"):
                obj.draw(screen)
        createUI()

        #game over fade
        if(gameOver == True):
            reverseFadeWindow(screen)
            if(alpha > 255):
                alpha == 255
            createGameOverText(screen)

        #game start fade
        if(alpha > 0 and gameOver == False):
            fadeWindow(screen)
        elif(alpha <= 0 and gameOver == False):
            fading = False

        #flips the display
        pygame.display.update()

        #limits the frame rate
        clock.tick(fps)

        #event loop
        for event in pygame.event.get():
            global playerFiring
            if event.type == pygame.MOUSEBUTTONDOWN:
                if(event.button == 1):
                    playerFiring = True
            if event.type == pygame.MOUSEBUTTONUP:
                if(event.button == 1):
                    playerFiring = False
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
            if(event.type == pygame.KEYDOWN):
                pressed = pygame.key.get_pressed()
                if(pressed[pygame.K_ESCAPE]):
                    running = False
                    pygame.quit()
                if(pressed[pygame.K_SPACE] and gameOver == True):
                    alpha = 0
                    gameMode = 1
                    running = False


gameMode = 1
while(gameMode != 0):
    if(gameMode == 1):
        runStart()
    elif(gameMode == 2):
        score = 0
        spawnTimer = 360
        spawnTime = spawnTimer
        createPlayerShip()
        for obj in objects:
            if(obj.tag == "Player"):
                obj.health = playerMaxHealth
                obj.pos = Vec2(pygame.display.get_surface().get_width()/2,pygame.display.get_surface().get_height()/2)
            if(obj.tag == "Enemy"):
                obj.health = 0
                score -= 1
            elif(obj.tag == "EnemyProjectile" or obj.tag == "PlayerProjectile"):
                obj.health = 0
        runMainGame()
    else:
        gameMode = 0
