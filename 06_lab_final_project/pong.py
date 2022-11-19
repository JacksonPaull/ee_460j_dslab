import pygame
import random
import math

# Defining Global Constants
c_white = (255, 255, 255)
c_black = (0  ,   0,   0)
c_red   = (255,   0,   0)

class GameObject:
    def update(self, dt):
        pass
    def draw(self, surf):
        pass

class Ball(GameObject):
    r = 10

    def __init__(self, x, y, engine):
        self.x = x
        self.y = y
        self.engine = engine

        dx = (-1 if random.random() > 0.5 else 1) * 0.5 
        dy = (random.random() - 0.5) * 2 
        mag = math.sqrt(dx ** 2 + dy ** 2)

        self.speed = (dx/mag, dy/mag)

    def update(self, dt):
        # Move
        self.y += self.speed[1] * dt
        self.x += self.speed[0] * dt

        dy = 1
        dx = 1

        # Adjust position for collisions with ceiling and floor
        if self.y < 0:
            self.y *= -1 # Flip distance to top borders
            dy = -1
        if self.y > self.engine.scr_height:
            self.y -= 2*(self.y - self.engine.scr_height)
            dy = -1

        # Check for collisions with paddles
        for i, p in enumerate([self.engine.objects['paddle1'], self.engine.objects['paddle2']]):
            if self.x >= p.x and self.x <= p.x + p.width and self.y >= p.y and self.y <= p.y + p.height:
                # Ball collided with paddle
                if i == 0:
                    self.engine.objects['scoreboard'].p1Score += 1
                    self.x = p.x + p.width + self.r
                else:
                    self.engine.objects['scoreboard'].p2Score += 1
                    self.x = p.x - self.r
                
                dx = -1

        # Check for round over (Paddle missed a ball)
        if self.x < 0:
            self.engine.round_over = True
            self.x *= -1 # Flip distance to top border
            dx = -1
        if self.x > self.engine.scr_width:
            self.engine.round_over = True
            self.x -= 2*(self.x - self.engine.scr_width)
            dx = -1

        # Update Speed
        if dx != 1 or dy != 1:
            newxv = self.speed[0] * dx #* self.speed #* 1.0125, # (optional) Increase speed
            newyv = self.speed[1] * dy #* self.speed
            self.speed = (newxv, newyv)

    def draw(self, surf):
        pygame.draw.circle(surf, c_white, (self.x, self.y), self.r)

        # Debug code to shoe dx and dy for the ball
        """t = self.engine.fnt_debug.render(f'Ball Speed: ({self.speed[0]:.2f}, {self.speed[1]:.2f})', False, c_white)
        t_rect = t.get_rect()
        t_rect.topleft = (10, 10)
        surf.blit(t, t_rect)

        t = self.engine.fnt_debug.render(f'Magnitude: {math.sqrt(self.speed[0] ** 2 + self.speed[1] ** 2):.2f}', False, c_white)
        t_rect = t.get_rect()
        t_rect.topleft = (10, 60)
        surf.blit(t, t_rect)"""
        


class Paddle(GameObject):
    width = 25
    height = 135 # Center at y + 67
    speed = 0.5
    keybinds = {
        'up':pygame.K_w,
        'down':pygame.K_s
    }

    def __init__(self, x, y, engine, keybinds=None):
        self.x = x
        self.y = y
        self.engine = engine
        if keybinds is not None:
            self.keybinds = keybinds

    def update(self, dt):
        if pygame.key.get_pressed()[self.keybinds['up']]:
            self.move_up(dt)
        if pygame.key.get_pressed()[self.keybinds['down']]:
            self.move_down(dt)
        
    def move_up(self, dt):
        self.y -= min(self.speed*dt, self.y)

    def move_down(self, dt):
        self.y += self.speed*dt
        if self.y + self.height > self.engine.scr_height:
            self.y = self.engine.scr_height - self.height

    def draw(self, surf):
        surf.fill(c_white, (self.x, self.y, self.width, self.height))
        #pygame.draw.line(surf, c_red, (self.x - 5, self.y + 67), (self.x + self.width + 5, self.y + 67), width=3) # Debug code to show the center of the paddle


class Scoreboard(GameObject):
    dashed_line_height = 25

    def __init__(self, font, engine):
        # Create scoreboard object
        self.p1Score = 0
        self.p2Score = 0
        
        self.font = font
        self.engine = engine
        self.num_lines = math.ceil(self.engine.scr_height / self.dashed_line_height / 2)


    def draw(self, surf):
        # Draw the current scores of the players in the proper position onto surf
        t = self.font.render(f'Player 1 Score: {self.p1Score}', False, c_white)
        t_rect = t.get_rect()
        t_rect.center = (self.engine.scr_width/4, 50)
        surf.blit(t, t_rect)

        t = self.font.render(f'{self.p2Score}: Player 2 Score', False, c_white)
        t_rect = t.get_rect()
        t_rect.center = (3 * self.engine.scr_width/4, 50)
        surf.blit(t, t_rect)

        for i in range(self.num_lines):
            start_pos = (self.engine.scr_width / 2, self.dashed_line_height * 2 * i)
            end_pos =   (self.engine.scr_width / 2, self.dashed_line_height * 2 * i + self.dashed_line_height)
            pygame.draw.line(surf, c_white, start_pos, end_pos, 3)


class Pong_Game_Engine:
    pygame.init()
    pygame.font.init()
    _framerate = 60
    clock = pygame.time.Clock()
    scr_width, scr_height = 1600, 960
    fnt_debug = pygame.font.SysFont('Arial', 32)

    def __init__(self, screensize=None):
        self.objects = {}
        self.should_quit = False
        self.paused = True

        if screensize is not None:
            self.scr_width, self.scr_height = screensize

        self.screen = pygame.display.set_mode((self.scr_width, self.scr_height))
        self.objects['ball'] = Ball(self.scr_width/2, self.scr_height/2, self)
        self.objects['scoreboard'] = Scoreboard(self.fnt_debug, self)

        p = Paddle(30, self.scr_height/2, self)
        p.y -= math.floor(p.height/2)
        self.objects['paddle1'] = p

        p = Paddle(self.scr_width - 30, self.scr_height/2, self, keybinds={'up':pygame.K_o, 'down':pygame.K_l})
        p.x -= p.width
        p.y -= math.floor(p.height/2)
        self.objects['paddle2'] = p

        # Draw initial screen
        self.screen.fill(c_black)
        for o in self.objects.values():
            o.draw(self.screen)
        pygame.display.flip()

    def update(self):
        dt = self.clock.tick(self._framerate)
        for e in pygame.event.get():
            if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                self.should_quit = True
                return
            if e.type == pygame.KEYDOWN and e.key == pygame.K_SPACE:
                self.paused ^= 1
            if e.type == pygame.KEYDOWN and e.key == pygame.K_r:
                self.reset()

        if self.paused:
            return

        self.screen.fill(c_black)

        for o in self.objects.values():
            o.update(dt)

        for o in self.objects.values():
            o.draw(self.screen)

        pygame.display.flip()

    def reset(self):
        p1 = self.objects['paddle1']
        p2 = self.objects['paddle2']
        ball = self.objects['ball']
        self.paused = True

        p1.x = 30
        p1.y = self.scr_height/2 - math.floor(p1.height/2)

        p2.x = self.scr_width - 30 - p2.width
        p2.y = self.scr_height/2 - math.floor(p2.height/2)

        dx = (-1 if random.random() > 0.5 else 1) * 0.5 
        dy = (random.random() - 0.5) * 2
        mag = math.sqrt(dx ** 2 + dy ** 2)
        ball.speed = (dx/mag, dy/mag)

        ball.x, ball.y = self.scr_width/2, self.scr_height/2

        self.screen.fill(c_black)

        for o in self.objects.values():
            o.draw(self.screen)

        pygame.display.flip()



if __name__ == '__main__':
    pge = Pong_Game_Engine()
    while not pge.should_quit:
        pge.update()



# Todo:
    # - Add Title Screen + press space to unpause
    # - Add pause screen + press space to unpause

    # Add Paddle collision

    # Add Score counter
        # Increment score on paddle collision

    # Implement 'game over' on ball collision with vertical walls
        # space to re-serve
        # r to restart
        # escape to quit

        # (Optional) Game ends after first score to reach 5