import random
import pygame
import flappy_bird_utils
from itertools import cycle

FPS = 30
SCREENWIDTH  = 288
SCREENHEIGHT = 420

VOLUME = 0.02

pygame.init()
FPSCLOCK = pygame.time.Clock()
SCREEN = pygame.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
pygame.display.set_caption('')

IMAGES, SOUNDS, HITMASKS = flappy_bird_utils.load()
PIPEGAPSIZE = 120  # gap between upper and lower part of pipe
BASEY = SCREENHEIGHT

PLAYER_WIDTH = IMAGES['player'][0].get_width()
PLAYER_HEIGHT = IMAGES['player'][0].get_height()
PIPE_WIDTH = IMAGES['pipe'][0].get_width()
PIPE_HEIGHT = IMAGES['pipe'][0].get_height()
BACKGROUND_WIDTH = IMAGES['background'].get_width()
PLAYER_COLOR_OFFSET = True
PLAYER_INDEX_GEN = cycle([0,
                          1,
                          2,
                          1])


class GameState:
    def __init__(self):
        self.score = self.playerIndex = self.loopIter = 0
        self.playerx = int(SCREENWIDTH * -0.2)
        self.playery = int((SCREENHEIGHT - PLAYER_HEIGHT) / 2 )
        self.basex = 0
        self.baseShift = IMAGES['base'].get_width() - BACKGROUND_WIDTH

        newPipe1 = getRandomPipe()
        newPipe2 = getRandomPipe()
        self.upperPipes = [
            {'x': SCREENWIDTH, 'y': newPipe1[0]['y']},
            {'x': SCREENWIDTH + (SCREENWIDTH / 2), 'y': newPipe2[0]['y']},
        ]
        self.lowerPipes = [
            {'x': SCREENWIDTH, 'y': newPipe1[1]['y']},
            {'x': SCREENWIDTH + (SCREENWIDTH / 2), 'y': newPipe2[1]['y']},
        ]

        # player velocity, max velocity, downward accleration, accleration on flap
        self.pipeVelX = -4
        self.playerVelX    =  0
        self.playerVelY    =  0    # player's velocity along Y, default same as playerFlapped
        self.playerMaxVelY =  10   # max vel along Y, max descend speed
        self.playerMinVelY =  -10   # min vel along Y, max ascend speed
        self.playerAccY    =   0   # players downward accleration
        self.playerFlapAcc =  -1   # players speed on flapping
        self.playerFlapped = False # True when player flaps

    def frame_step(self, input_actions):
        pygame.event.pump()

        # print(f"***Pipe {SCREENHEIGHT}, player {self.playery}, dif = {PIPE_HEIGHT-self.playery}")
        reward = 0.1/abs(-SCREENHEIGHT/2-self.playery)
        terminal = False

        # input_actions[0] == 1: do nothing
        # input_actions[1] == x: orb acceleration direction and magnitude [-1, 1]
        print(f"input actions : {input_actions}")
        if input_actions[0] == 0:  # Brakes off
            # if self.playery > -2 * PLAYER_HEIGHT:
            print("FLAP")
            self.playerVelY = self.playerFlapAcc * input_actions[1]
            self.playerVelX = self.playerFlapAcc * input_actions[2]
            self
            self.playerFlapped = True
            #SOUNDS['wing'].play()
        else:
            # DRAG
            self.drag_linear()
            # self.drag_quadratic()

        # check for score
        playerMidPos = self.playerx + PLAYER_WIDTH / 2
        for pipe in self.upperPipes:
            pipeMidPos = pipe['x'] + PIPE_WIDTH / 2
            if pipeMidPos <= playerMidPos < pipeMidPos + 4:
                self.score += 1
                SOUNDS['point'].play().set_volume(VOLUME)
                reward = 1

        # playerIndex basex change
        if (self.loopIter + 1) % 3 == 0:
            self.playerIndex = next(PLAYER_INDEX_GEN)
        self.loopIter = (self.loopIter + 1) % 30
        self.basex = -((-self.basex + 100) % self.baseShift)

        # player's movement
        if self.playerFlapped:
            if self.playerVelY < self.playerMaxVelY:
                pass
                # self.playerVelY += self.playerAccY
                # print(f"Acceleration {acceleration} | pipe1 {self.upperPipes[0]['y']} | pipe2 {self.lowerPipes[0]['y']} | burb {self.playery}\n")
                # self.playerVelY += self.playerFlapAcc
                # self.playerVelX += self.playerFlapAcc

        if self.playerFlapped:
            self.playerFlapped = False
        self.playery += min(self.playerVelY, BASEY - self.playery - PLAYER_HEIGHT)
        self.playerx += min(self.playerVelX, SCREENWIDTH - self.playerx - PLAYER_WIDTH)
        if self.playery < 0:
            self.playery = 0
        if self.playerx < -50:
            self.playerx = -50
        if self.playerx > SCREENWIDTH:
            self.playerx = SCREENWIDTH

        # move pipes to left
        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            uPipe['x'] += self.pipeVelX
            lPipe['x'] += self.pipeVelX

        # add new pipe when first pipe is about to touch left of screen
        if 0 < self.upperPipes[0]['x'] < 5:
            newPipe = getRandomPipe()
            self.upperPipes.append(newPipe[0])
            self.lowerPipes.append(newPipe[1])

        # remove first pipe if its out of the screen
        if self.upperPipes[0]['x'] < -PIPE_WIDTH:
            self.upperPipes.pop(0)
            self.lowerPipes.pop(0)

        # check if crash here
        isCrash= checkCrash({'x': self.playerx, 'y': self.playery,
                             'index': self.playerIndex},
                            self.upperPipes, self.lowerPipes)
        if isCrash:
            SOUNDS['hit'].play().set_volume(VOLUME*2)
            # SOUNDS['die'].play().set_volume(VOLUME)
            terminal = True
            self.__init__()
            reward = -1

        # draw sprites
        SCREEN.blit(IMAGES['background'], (0,0))

        for uPipe, lPipe in zip(self.upperPipes, self.lowerPipes):
            SCREEN.blit(IMAGES['pipe'][0], (uPipe['x'], uPipe['y']))
            SCREEN.blit(IMAGES['pipe'][1], (lPipe['x'], lPipe['y']))

        SCREEN.blit(IMAGES['base'], (self.basex, BASEY))
        # print score so player overlaps the score
        showScore(self.score)
        SCREEN.blit(IMAGES['player'][self.playerIndex],
                    (self.playerx, self.playery))

        image_data = pygame.surfarray.array3d(pygame.display.get_surface())
        pygame.display.update()
        FPSCLOCK.tick(FPS)
        #print self.upperPipes[0]['y'] + PIPE_HEIGHT - int(BASEY * 0.2)
        return image_data, reward, terminal

    def drag_linear(self):
        coef = 0.01
        self.playerVelY += -coef*self.playerVelY
        self.playerVelX -= -coef*self.playerVelX

    def drag_quadratic(self):
        density = .000001
        area = 1
        drag_coef = 1
        self.playerVelY += (1 / 2) * density * area * drag_coef * self.playerVelY ** 2
        self.playerVelX -= (1 / 2) * density * area * drag_coef * self.playerVelX ** 2


def getRandomPipe():
    """returns a randomly generated pipe"""
    # y of gap between upper and lower pipe
    gapYs = [20, 30, 40, 50, 60, 70, 80, 90]
    index = random.randint(0, len(gapYs)-1)
    gapY = gapYs[index]

    gapY += int(BASEY * 0.2)
    pipeX = SCREENWIDTH + 10

    return [
        {'x': pipeX, 'y': gapY - PIPE_HEIGHT},  # upper pipe
        {'x': pipeX, 'y': gapY + PIPEGAPSIZE},  # lower pipe
    ]


def showScore(score):
    """displays score in center of screen"""
    scoreDigits = [int(x) for x in list(str(score))]
    totalWidth = 0  # total width of all numbers to be printed

    for digit in scoreDigits:
        totalWidth += IMAGES['numbers'][digit].get_width()

    # Xoffset = (SCREENWIDTH - totalWidth) / 2
    Xoffset = 10

    for digit in scoreDigits:
        SCREEN.blit(IMAGES['numbers'][digit], (Xoffset, SCREENHEIGHT * 0.02))
        Xoffset += IMAGES['numbers'][digit].get_width()


def checkCrash(player, upperPipes, lowerPipes):
    """returns True if player collders with base or pipes."""

    pi = player['index']

    if PLAYER_COLOR_OFFSET:
        pi += 3

    player['w'] = IMAGES['player'][pi].get_width()
    player['h'] = IMAGES['player'][pi].get_height()

    # if player crashes into ground
    if player['y'] + player['h'] >= BASEY - 1:
        return True
    else:

        playerRect = pygame.Rect(player['x'], player['y'],
                      player['w'], player['h'])

        for uPipe, lPipe in zip(upperPipes, lowerPipes):
            # upper and lower pipe rects
            uPipeRect = pygame.Rect(uPipe['x'], uPipe['y'], PIPE_WIDTH, PIPE_HEIGHT)
            lPipeRect = pygame.Rect(lPipe['x'], lPipe['y'], PIPE_WIDTH, PIPE_HEIGHT)

            # player and upper/lower pipe hitmasks
            print(f"PI: {pi}")
            pHitMask = HITMASKS['player'][pi]
            uHitmask = HITMASKS['pipe'][0]
            lHitmask = HITMASKS['pipe'][1]

            # if bird collided with upipe or lpipe
            uCollide = pixelCollision(playerRect, uPipeRect, pHitMask, uHitmask)
            lCollide = pixelCollision(playerRect, lPipeRect, pHitMask, lHitmask)

            if uCollide or lCollide:
                return True

    return False


def pixelCollision(rect1, rect2, hitmask1, hitmask2):
    """Checks if two objects collide and not just their rects"""
    rect = rect1.clip(rect2)

    if rect.width == 0 or rect.height == 0:
        return False

    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y

    for x in range(rect.width):
        for y in range(rect.height):
            if hitmask1[x1+x][y1+y] and hitmask2[x2+x][y2+y]:
                return True
    return False
