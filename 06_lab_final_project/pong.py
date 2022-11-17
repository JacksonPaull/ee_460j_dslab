import pygame


# Defining Global Constants
c_white = (255, 255, 255)
c_black = (0  ,   0,   0)

class Ball:
    r = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        

    def update(self):
        pass

    def draw(self, surf):
        pygame.draw.circle(surf, c_white, (self.x, self.y), self.r)


class Paddle:
    width = 25
    height = 100

    def __init__(self, x, y):
        self.x = x
        self.y = y
        

    def move_up(self):
        pass

    def move_down(self):
        pass

    def draw(self, surf):
        surf.fill(c_white, (self.x, self.y, self.width, self.height))

class Pong_Game_Engine:
    def __init__(self):
        pass



    def update():
        pass






pygame.init()


screen = pygame.display.set_mode((320, 240))

ball = Ball(100, 100)
paddle = Paddle(200, 100)

objects = [ball, paddle]

while True:
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            exit()
    

    screen.fill(c_black)

    for o in objects:
        o.draw(screen)

    pygame.display.flip()